#!/usr/bin/env python3
"""
Parser to extract individual functions from Infer test files and generate JSONL evaluation data.

Usage:
    python parser.py --test-file ../infer/tests/codetoanalyze/c/pulse/nullptr.c \
                     --issues-exp ../infer/tests/codetoanalyze/c/pulse/issues.exp \
                     --output data/nullptr_basic.jsonl
"""

import argparse
import json
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class Bug:
    bug_type: str
    line_offset: int
    absolute_line: int
    severity: str
    trace: str


@dataclass
class GroundTruth:
    has_bug: bool
    bugs: List[Dict]


@dataclass
class FunctionInfo:
    id: str
    source_file: str
    original_function_name: str
    anonymized_function_name: str
    function_code: str
    includes: List[str]
    dependencies: List[str]
    ground_truth: Dict
    metadata: Dict


def parse_issues_exp(issues_exp_path: str) -> Dict[str, List[Bug]]:
    """
    Parse issues.exp file and return dict mapping function names to bugs.

    Format: file, procedure, line_offset, bug_type, bucket, severity, [trace]
    """
    bugs_by_function = {}

    with open(issues_exp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse CSV-like format
            parts = line.split(', ')
            if len(parts) < 6:
                continue

            file_path = parts[0]
            function_name = parts[1]
            line_offset = int(parts[2])
            bug_type = parts[3]
            severity = parts[5]

            # Extract trace (everything after severity, inside brackets)
            trace_start = line.find('[', line.find(severity))
            trace_end = line.rfind(']')
            trace = ""
            if trace_start != -1 and trace_end != -1:
                trace = line[trace_start+1:trace_end]

            bug = Bug(
                bug_type=bug_type,
                line_offset=line_offset,
                absolute_line=-1,  # Will be filled when we parse functions
                severity=severity,
                trace=trace
            )

            if function_name not in bugs_by_function:
                bugs_by_function[function_name] = []
            bugs_by_function[function_name].append(bug)

    return bugs_by_function


def extract_includes(source_code: str) -> List[str]:
    """Extract all #include statements from source code."""
    includes = []
    for line in source_code.split('\n'):
        line = line.strip()
        if line.startswith('#include'):
            includes.append(line)
    return includes


def extract_functions(source_path: str) -> List[Tuple[str, int, int, str]]:
    """
    Extract functions from C source file.

    Returns: List of (function_name, start_line, end_line, function_code)
    """
    with open(source_path, 'r') as f:
        lines = f.readlines()

    functions = []

    # Simple regex to match function definitions
    # This matches: return_type function_name(params) {
    func_pattern = re.compile(r'^(\w+[\s\*]+)(\w+)\s*\([^)]*\)\s*\{')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments, preprocessor directives, blank lines
        if (not line or
            line.startswith('//') or
            line.startswith('/*') or
            line.startswith('#') or
            line.startswith('*/')):
            i += 1
            continue

        # Check if this looks like a function definition
        match = func_pattern.match(lines[i].strip())
        if match:
            func_name = match.group(2)
            start_line = i + 1  # 1-indexed

            # Find matching closing brace
            brace_count = 0
            in_function = False
            end_line = i

            for j in range(i, len(lines)):
                for char in lines[j]:
                    if char == '{':
                        brace_count += 1
                        in_function = True
                    elif char == '}':
                        brace_count -= 1
                        if in_function and brace_count == 0:
                            end_line = j + 1  # 1-indexed
                            break
                if in_function and brace_count == 0:
                    break

            if end_line > i:
                func_code = ''.join(lines[i:end_line])
                functions.append((func_name, start_line, end_line, func_code))
                i = end_line
            else:
                i += 1
        else:
            i += 1

    return functions


def anonymize_function_name(original_name: str, index: int) -> str:
    """
    Remove hint suffixes from function name while preserving semantic meaning.

    Removes: _bad, _ok, _good, FP_, FN_, _latent
    Keeps: Descriptive parts of the name

    Examples:
        malloc_no_check_bad -> malloc_no_check
        create_null_path_ok -> create_null_path
        FP_some_function -> some_function
        use_after_free_simple_bad -> use_after_free_simple
    """
    name = original_name

    # Remove common hint prefixes
    if name.startswith('FP_'):
        name = name[3:]  # Remove "FP_"
    elif name.startswith('FN_'):
        name = name[3:]  # Remove "FN_"

    # Remove common hint suffixes
    hint_suffixes = ['_bad', '_ok', '_good', '_latent']
    for suffix in hint_suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break

    # If name is empty after removal, use generic name
    if not name:
        name = f"test_function_{index:03d}"

    return name


def anonymize_function_code(code: str, original_name: str, anonymized_name: str) -> str:
    """
    Replace function name in code with anonymized version.
    Uses word boundaries to avoid partial replacements.
    """
    # Use word boundary to match complete function names only
    pattern = r'\b' + re.escape(original_name) + r'\b'
    return re.sub(pattern, anonymized_name, code)




def categorize_function(bugs: List[Bug]) -> str:
    """Categorize function based on bug types."""
    if not bugs:
        return "safe"

    bug_types = {bug.bug_type for bug in bugs}

    if "NULLPTR_DEREFERENCE" in bug_types:
        return "nullptr_dereference"
    elif "MEMORY_LEAK" in bug_types or "MEMORY_LEAK_C" in bug_types:
        return "memory_leak"
    elif "USE_AFTER_FREE" in bug_types:
        return "use_after_free"
    elif "UNINITIALIZED_VALUE" in bug_types or "PULSE_UNINITIALIZED_VALUE" in bug_types:
        return "uninitialized_value"
    elif "RESOURCE_LEAK" in bug_types or "PULSE_RESOURCE_LEAK" in bug_types:
        return "resource_leak"
    else:
        return "other"


def extract_struct_definitions(source_code: str) -> Dict[str, str]:
    """
    Extract all struct definitions from source code.

    Returns: Dict mapping struct name to full struct definition code.
    """
    structs = {}
    lines = source_code.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match struct definition: struct name {
        if line.startswith('struct ') and '{' in line:
            # Extract struct name
            match = re.match(r'struct\s+(\w+)\s*\{', line)
            if match:
                struct_name = match.group(1)

                # Find closing brace
                brace_count = line.count('{') - line.count('}')
                struct_lines = [lines[i]]

                j = i + 1
                while j < len(lines) and brace_count > 0:
                    struct_lines.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    j += 1

                structs[struct_name] = '\n'.join(struct_lines)
                i = j
                continue

        i += 1

    return structs


def find_referenced_structs(code: str, all_structs: Dict[str, str]) -> List[str]:
    """
    Find all struct types referenced in the given code, including nested dependencies.

    Returns: List of struct definition code for structs used in the function.
    """
    referenced = []
    to_check = [code]
    seen_structs = set()

    while to_check:
        current_code = to_check.pop(0)

        for struct_name, struct_def in all_structs.items():
            if struct_name in seen_structs:
                continue

            # Look for "struct struct_name" in the code
            pattern = r'\bstruct\s+' + re.escape(struct_name) + r'\b'
            if re.search(pattern, current_code):
                referenced.append(struct_def)
                seen_structs.add(struct_name)
                # Check this struct definition for nested struct references
                to_check.append(struct_def)

    return referenced


def extract_dependencies(code: str, all_functions: List[str]) -> List[str]:
    """
    Extract function dependencies (other functions called from this one).
    Returns list of function names.
    """
    dependencies = []

    for func_name in all_functions:
        # Look for function calls (function_name followed by parenthesis)
        pattern = r'\b' + re.escape(func_name) + r'\s*\('
        if re.search(pattern, code):
            dependencies.append(func_name)

    return dependencies


def get_dependency_code(dep_names: List[str], all_functions: List[Tuple[str, int, int, str]]) -> List[str]:
    """
    Get the full code for dependency functions.

    Args:
        dep_names: List of function names that are dependencies
        all_functions: List of (name, start_line, end_line, code) tuples

    Returns: List of function code strings for dependencies
    """
    dep_code = []
    func_dict = {name: code for name, _, _, code in all_functions}

    for dep_name in dep_names:
        if dep_name in func_dict:
            dep_code.append(func_dict[dep_name])

    return dep_code


def generate_jsonl(test_file: str, issues_exp: str, output_path: str,
                   anonymize: bool = True, include_safe: bool = True):
    """
    Generate JSONL file from test file and issues.exp.

    Args:
        test_file: Path to C test file
        issues_exp: Path to issues.exp file
        output_path: Path to output JSONL file
        anonymize: Whether to anonymize function names
        include_safe: Whether to include safe functions (no bugs)
    """

    # Parse ground truth
    bugs_by_function = parse_issues_exp(issues_exp)

    # Extract source code
    with open(test_file, 'r') as f:
        source_code = f.read()

    # Extract includes
    includes = extract_includes(source_code)

    # Extract struct definitions
    all_structs = extract_struct_definitions(source_code)

    # Extract functions
    functions = extract_functions(test_file)
    all_function_names = [name for name, _, _, _ in functions]

    # Determine source file relative path
    source_file = os.path.relpath(test_file, os.path.dirname(os.path.dirname(test_file)))

    # Generate examples
    examples = []
    function_index = 1

    for original_name, start_line, end_line, func_code in functions:
        # Skip FP_ and FN_ prefixed functions (known false positives/negatives)
        if original_name.startswith('FP_') or original_name.startswith('FN_'):
            continue

        # Get bugs for this function
        bugs = bugs_by_function.get(original_name, [])

        # Update absolute line numbers for bugs
        for bug in bugs:
            bug.absolute_line = start_line + bug.line_offset

        # Skip safe functions if requested
        if not include_safe and not bugs:
            continue

        # Anonymize if requested
        if anonymize:
            anonymized_name = anonymize_function_name(original_name, function_index)
            anonymized_code = anonymize_function_code(func_code, original_name, anonymized_name)
        else:
            anonymized_name = original_name
            anonymized_code = func_code

        # Extract dependencies (function names)
        dep_names = extract_dependencies(func_code, all_function_names)
        dep_names = [d for d in dep_names if d != original_name]  # Remove self-references

        # Get full code for dependency functions
        dep_code = get_dependency_code(dep_names, functions)

        # Find referenced struct definitions
        struct_defs = find_referenced_structs(func_code, all_structs)

        # Also check dependencies for struct references
        for dep in dep_code:
            struct_defs.extend(find_referenced_structs(dep, all_structs))

        # Remove duplicates while preserving order
        seen = set()
        unique_structs = []
        for struct_def in struct_defs:
            if struct_def not in seen:
                seen.add(struct_def)
                unique_structs.append(struct_def)

        # Create ground truth
        ground_truth = {
            "has_bug": len(bugs) > 0,
            "bugs": [
                {
                    "bug_type": bug.bug_type,
                    "line_offset": bug.line_offset,
                    "absolute_line": bug.absolute_line,
                    "severity": bug.severity,
                    "trace": bug.trace
                }
                for bug in bugs
            ]
        }

        # Determine metadata
        category = categorize_function(bugs)

        metadata = {
            "requires_interprocedural": len(dep_names) > 0,
            "category": category,
            "start_line": start_line,
            "end_line": end_line
        }

        # Combine includes with struct definitions
        # Includes go at the top, then struct definitions
        context_includes = includes + unique_structs

        # Create function info
        func_info = FunctionInfo(
            id=f"{os.path.basename(test_file).replace('.c', '')}_{function_index:03d}",
            source_file=source_file,
            original_function_name=original_name,
            anonymized_function_name=anonymized_name,
            function_code=anonymized_code,
            includes=context_includes,
            dependencies=dep_code,
            ground_truth=ground_truth,
            metadata=metadata
        )

        examples.append(func_info)
        function_index += 1

    # Write JSONL
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for example in examples:
            f.write(json.dumps(asdict(example)) + '\n')

    print(f"Generated {len(examples)} examples")
    print(f"Written to: {output_path}")

    # Print statistics
    bug_count = sum(1 for ex in examples if ex.ground_truth['has_bug'])
    safe_count = len(examples) - bug_count
    print(f"\nStatistics:")
    print(f"  Functions with bugs: {bug_count}")
    print(f"  Safe functions: {safe_count}")

    # Category breakdown
    categories = {}
    for ex in examples:
        cat = ex.metadata['category']
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nCategories:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate JSONL evaluation data from Infer test files'
    )
    parser.add_argument(
        '--test-file',
        required=True,
        help='Path to C test file (e.g., infer/tests/codetoanalyze/c/pulse/nullptr.c)'
    )
    parser.add_argument(
        '--issues-exp',
        required=True,
        help='Path to issues.exp file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output JSONL file'
    )
    parser.add_argument(
        '--no-anonymize',
        action='store_true',
        help='Do not anonymize function names'
    )
    parser.add_argument(
        '--exclude-safe',
        action='store_true',
        help='Exclude functions with no bugs'
    )

    args = parser.parse_args()

    generate_jsonl(
        test_file=args.test_file,
        issues_exp=args.issues_exp,
        output_path=args.output,
        anonymize=not args.no_anonymize,
        include_safe=not args.exclude_safe
    )


if __name__ == '__main__':
    main()
