# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Infer is a static analysis tool for Java, C++, Objective-C, C, Erlang, Hack, Python, Rust, and Swift. The project is written primarily in OCaml and uses a custom clang frontend for C-family languages.

## Build Commands

### Initial Setup
```bash
# Build with opam (recommended, handles dependencies automatically)
./build-infer.sh java          # Build Java analyzer
./build-infer.sh clang         # Build C/C++/Objective-C analyzer (slow, compiles custom clang)
./build-infer.sh               # Build all analyzers

# Add to PATH
export PATH=`pwd`/infer/bin:$PATH

# Or install system-wide
sudo make install
```

### Building from Source (without opam)
```bash
./autogen.sh
./configure  # Use --disable-java-analyzers or --disable-c-analyzers to disable specific analyzers
make -j
```

### Development Setup
```bash
# Install development dependencies (run after ./build-infer.sh)
make devsetup
```

### Development Build Commands
```bash
# Build in development mode (warnings are fatal)
make -j

# Build ignoring warnings (for testing before polishing)
make BUILD_MODE=dev-noerror

# Fast type-check only (from infer/src/ directory, after building once)
make -j -C infer/src check

# Build in bytecode mode for quick testing
make -j -C infer/src byte

# Check build without warnings
make -j test_build
```

## Testing

### Running Tests
```bash
# Run all tests (use -j with number of cores available)
make -j 4 test

# Run specific test from root (rebuilds infer if needed)
make direct_java_biabduction_test

# Run test from test directory (assumes infer is up-to-date)
make -C infer/tests/codetoanalyze/java/biabduction/ test

# Update expected test results after intentional changes
make test-replace
```

### Test Structure
- Tests are in `infer/tests/codetoanalyze/{language}/{analyzer}/`
- Each test has:
  1. Source code to analyze
  2. `issues.exp` file with expected output (one line per issue)
  3. `Makefile` to orchestrate the test
- Naming conventions for test procedures:
  - `*Bad` suffix: should report an error
  - `*Ok` suffix: should not report an error
  - `FP_*` prefix: false positive (documents current limitation)
  - `FN_*` prefix: false negative (documents current limitation)

### Debug Output
```bash
# Generate debug HTML output to inspect symbolic execution
infer --debug -- clang -c examples/hello.c
firefox infer-out/captured/hello.c.*.html
```

## Code Architecture

### Source Organization (`infer/src/`)
- **IR/**: Intermediate representation - core data structures for program representation
- **absint/**: Abstract interpretation framework - foundation for analyses
- **base/**: Base utilities and infrastructure (IStd module, logging, etc.)
- **backend/**: Analysis orchestration and scheduling
- **pulse/**: Pulse analyzer (main memory safety checker) - largest analyzer codebase
- **checkers/**: Various checker implementations
- **bufferoverrun/**: Buffer overrun analysis
- **concurrency/**: Concurrency-related analyses (RacerD, starvation)
- **cost/**: Performance/complexity analysis
- **topl/**: Temporal property verification
- **clang/**: C/C++/Objective-C frontend
- **java/**: Java frontend
- **erlang/**: Erlang frontend
- **python/**: Python frontend
- **textual/**: Textual IR (intermediate language)
- **integration/**: Build system integrations
- **istd/**: Standard library (IStd module - automatically opened in all files)

### Key Concepts
- **IStd module** (`infer/src/istd/IStd.ml`): Automatically opened in every OCaml file, extends Core library
- **Analyzers**: Infer supports multiple analyzers (biabduction, pulse, racerd, etc.) selected via `infer -a {analyzer}`
- **Build systems**: Infer integrates with various build systems through capture/analyze/report phases
- **Frontend → IR → Backend**: Source code is translated to IR by language-specific frontends, then analyzed by backend

## OCaml Development Guidelines

### Module Conventions
```ocaml
open! IStd              // Explicitly open IStd (required in all modules)
module L = Logging      // Use for logging
module F = Format       // For formatting
module CLOpt = CommandLineOption
module MF = MarkupFormatter
```

### Important Rules
- **IStd** is automatically opened everywhere - provides Core library + custom utilities
- **No polymorphic equality**: Use type-specific equality (e.g., `Int.equal`, not `=`)
- **Logging**: Use `module L = Logging` and `Logging.debug_dev` for printf-debugging
- **Printf-debug warning**: `Logging.debug_dev` includes a warning to prevent accidental commits
- **Module names**: Infer modules are prefixed, e.g., module `M` becomes `InferModules__M` or `InferBase__M`
- Use `[@@deriving compare, equal]` for comparison/equality functions
- Named arguments for non-obvious parameters, especially booleans
- Format code with ocamlformat
- Line width limit: 100 characters

### Debugging OCaml
```bash
# Browse OCaml module documentation
make doc

# Using ocamldebug (note the InferModules__ prefix)
ledit ocamldebug infer/bin/infer.bc.exe
(ocd) break @ InferModules__InferAnalyze 100

# OCaml toplevel with infer modules
make toplevel
# Pass options: INFER_ARGS=--debug^-o^infer-out-foo
# Initialize results: ResultsDir.assert_results_dir ""
```

## Language Support

Infer analyzes multiple languages through different frontends:
- **Java**: Via bytecode analysis
- **C/C++/Objective-C**: Via custom clang frontend (`facebook-clang-plugins/`)
- **Erlang**: Via erlang frontend (requires erlc, escript)
- **Hack**: Via hackc
- **Python**: Experimental support
- **Rust**: Experimental (requires charon)
- **Swift**: Experimental

## Build System

- **Primary build**: Uses `dune` (OCaml build system) + `make`
- **Makefile hierarchy**: Root Makefile coordinates builds; commands from root ensure dependencies are up-to-date
- **Build modes**: dev (warnings fatal), dev-noerror (ignores warnings)
- **Dependencies**: Managed via opam (opam/infer.opam.locked has pinned versions)

## Opam Dependencies

To update opam dependencies:
1. Edit `opam/infer.opam`
2. Run `make` in the `opam/` directory to regenerate `infer.opam.locked`

## Common Workflows

### Running Infer
```bash
# Basic usage
infer run -- <build command>

# With specific analyzer
infer run -a pulse -- <build command>

# Common options
infer --debug                    # Enable debug output
infer -o <dir>                   # Custom output directory
infer --help                     # Full options
```

### Making Changes
1. Edit code in `infer/src/`
2. Build with `make -j` (from root) or `make -j -C infer/src check` (fast type-check)
3. Test with relevant test suite
4. Check for warnings: `make -j test_build`
5. Format code: ocamlformat (automatic via .ocamlformat)
6. Update tests if needed: `make test-replace`
