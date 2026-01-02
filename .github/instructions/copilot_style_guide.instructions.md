---
applyTo: '**'
---

Generic Python Scripting Style Guide (Concise)

---

## ⚡ Critical Rules (Read First)

**These 5 rules prevent the most common failures. Internalize before proceeding.**

1. **Check venv FIRST on any import error.** Before debugging `ModuleNotFoundError`, verify: `.venv/` exists → run `.\.venv\Scripts\Activate.ps1` → run `pip install -r requirements.txt`. Most import errors are venv issues.

2. **Run tests before marking work complete.** After code edits, run `pytest` on affected modules. Only report success when tests pass. If tests fail, fix them or document the failure.

3. **Contribute generic utilities to lks_utils.** If `lks_utils` is installed and you're writing code that isn't project-specific, add it to `lks_utils` instead of local `util/`. Follow lks_utils style guide.

4. **Update router docs when changing code.** After adding/modifying scripts, modules, or utilities, update `copilot_codebase_router.instructions.md` and the README "Codebase Router" section.

5. **No shims or wrappers.** When refactoring interfaces, update ALL callers in the same session. Never add compatibility layers—they accumulate tech debt.

---

1. Purpose and scope
- A practical rulebook for building and maintaining reusable Python scripts in this repository.
- Optimize for reliable batch/automation workflows, Windows-safe filesystem ops, and predictable resource usage.
- Keep code, tests, and docs aligned; prefer clarity, determinism, and traceable dependencies.

2. How to use this guide
- Humans: skim 3) Core principles, then jump to what you need.
- LLMs: read 3) Core principles and 6) Module authoring; follow all must/should rules.

3. Project primer
- What: a single-user, local-first Python toolkit that bundles scripts, utilities, schemas, examples, and supporting docs.
- Usage: Windows + PowerShell by default; network activity should be limited to dependency installs or intentional data pulls.
- Tenets: small focused modules (one primary responsibility per file); deterministic outputs for identical inputs; heavy logic in shared utilities; strict JSON/contracts; sanitize paths early; document assumptions.

4. Core principles (TL;DR)
- Single responsibility: prefer small modules or functions with one clear behavior; avoid multi-mode scripts unless accompanied by explicit helper variants.
- Clear naming: avoid vague terms like processor/manager/utility. Function names should be verbs (e.g., `build_report`), and script filenames should describe their primary outcome (e.g., `export_metrics.py`).
- Idempotency and determinism: produce stable outputs for identical inputs; skip work when outputs already exist (provide an overwrite/rerun toggle) and keep list order deterministic.
- Utility-first: orchestrate with scripts and push shared logic into `util/` helpers.
- Schema discipline: declare and validate JSON or config contracts; conform outputs to documented structures.
- Windows-safe defaults: sanitize paths (`safe_filename`, `pathlib.Path`), keep PowerShell-friendly docs, and respect 240-character limits.
- Configuration clarity: expose explicit parameters, prefer optional CLI flags over hidden globals, and document defaults.

## 4a. LLM Agent Workflow Requirements

### Mandatory Todo Lists

**LLM agents MUST maintain a todo list when editing code.** This is mandatory, not optional.

**When todo lists are required:**
- Before editing any code files (Python, JavaScript, CSS, etc.)
- Before creating new modules or significant functionality
- Before refactoring existing code
- Before any multi-step implementation task

**When todo lists are NOT required:**
- Pure conversational responses (answering questions, explaining concepts)
- Single-line spot fixes or typo corrections
- Reading files for context without making changes

**Todo list workflow:**
1. **Plan first**: Create a todo list outlining all planned changes
2. **Confirm major edits**: Before starting major edits, present the todo list for user confirmation
3. **Track progress**: Mark todos as in-progress when starting, completed when done
4. **One at a time**: Work on one todo at a time to maintain focus
5. **Update as needed**: Add or modify todos as scope becomes clearer

### Major vs. Minor Edits

**Major edits (require confirmation before proceeding):**
- Creating new modules or files
- Refactoring existing code structure
- Changes affecting more than ~2 script files
- Edits totaling more than ~100 lines of code
- Adding new dependencies
- Modifying public APIs

**Minor edits (may proceed without confirmation):**
- Fixing typos or syntax errors
- Adding missing imports
- Correcting type hints
- Small bug fixes in single locations
- Changes under ~100 LOC touching ≤2 files

### Test Verification

**LLM agents MUST run tests before completing code edits.** After making changes:
1. Run relevant tests (`python -m pytest <module>/test/` or `python run_tests.py --module <module>`)
2. If tests fail, attempt to fix the issues
3. Only mark the task complete when tests pass
4. If unable to fix, clearly document the failure and remaining issues

5. Repository layout
- `scripts/` – top-level workflows, entry-point scripts, and orchestrators. Keep them lean and focused on composition. Submodules live under `scripts/<module>/` with an `__init__.py` file.
- `scripts/<module>/data/` – module-specific static data: long text strings, LLM prompts, default configurations, lookup tables. See section 7 for guidance.
- `util/` – reusable helpers (path ops, batching, I/O, reports, validation). Reuse before writing new logic.
- `schemas/` – JSON Schema definitions or other contract files describing inputs/outputs.
- `prompt/` – stored prompts used by LLMs (repo-wide); module-specific prompts go in `scripts/<module>/data/`.
- `dependencies/` – native executables and binaries required by scripts (Windows binary files such as `ffmpeg.exe`, `tesseract.exe`) that cannot be installed via pip. The `install.bat` checks for expected native binaries and warns if missing.
- `debug/` – reusable inspection/validation scripts; parameterized CLIs with `argparse`, defaults in dry-run mode.
- `examples/` – minimal demonstrations for each script or pipeline.
- Docs (co-located markdown): place documentation next to the code it describes; use `scripts/<module>/<module>_system.md` for multi-script modules.

6. Module authoring
- Structure: add a module-level docstring summarizing purpose, inputs, outputs, and assumptions. Keep functions short (≤80 lines) and expressive.
- Type hinting: use static type hints for all function arguments, return values, and variables where possible (e.g., `count: int = 0`, `def process(path: Path) -> bool:`). Use `typing.Optional`, `typing.List`, etc. for clarity.
- CLI scripts: expose a `main()` guarded by `if __name__ == '__main__': main()`; parse arguments with `argparse`, document defaults, and support a `--verbose` flag where helpful.
- Configuration: prefer explicit config objects or dicts; validate early, raise `ValueError` or `RuntimeError` with concise reasons, and log context.
- All main code goes in `scripts/`. For multi-script submodules, create `scripts/<module>/` with an `__init__.py` file and organize scripts within.
- **External binary dependencies**: for scripts requiring external executables (e.g., `ffmpeg.exe`, `yt-dlp.exe`):
  - Accept an optional path parameter for each binary (e.g., `ffmpeg_path: Optional[str]`).
  - If not provided, recursively search the `dependencies/` folder for the binary (e.g., find `ffmpeg.exe` anywhere under `dependencies/`, including nested directories).
  - If not found, raise a clear error: `RuntimeError(f"<Binary> not found in dependencies/. Please provide path or place executable in dependencies/ folder")`.
  - Validate the binary exists and is executable before proceeding with the main workflow.
- I/O rules:
  - When creating files, return both the file paths and a JSON-friendly representation (e.g., list/dict) so downstream scripts can reuse them.
  - Provide optional outputs for debug log entries or summary data.
- Logging: use a shared logger (e.g., `logging.getLogger('repo.script')`); avoid `print` except for minimal CLI feedback or progress bars.
- File size: aim for <500 lines per script; factor heavy logic into utilities or helper modules.
- Modular naming: prefer descriptive snake_case filenames and PascalCase for classes (e.g., `FileExporter`, `PromptLoader`).

## 6a. Type Hints Policy

**Type hints are mandatory for all code.** Use static type hints to improve code clarity, enable IDE autocomplete, and catch bugs early.

### Required Type Hints

1. **All function parameters and return types:**
   ```python
   def process_files(paths: list[Path], max_count: int = 10) -> dict[str, int]:
       ...
   ```

2. **Variables where type isn't obvious from assignment:**
   ```python
   count: int = 0                              # Integer counter
   results: list[str] = []                     # List accumulator
   config: dict[str, Any] = {}                 # Configuration dict
   cache: dict[str, Image.Image] | None = None # Optional cache
   ```

3. **Loop variables and accumulators:**
   ```python
   for item in items:
       value: str = item.get('name', '')
       processed: dict[str, Any] = transform(value)
   ```

4. **Class attributes:**
   ```python
   class Processor:
       max_workers: int
       results: list[ProcessResult]
       config: ProcessConfig | None = None
   ```

### Type Hint Syntax

Use modern Python 3.10+ syntax (lowercase generics, `|` for unions):
```python
# Preferred (Python 3.10+)
paths: list[Path]                    # Not List[Path]
config: dict[str, Any]               # Not Dict[str, Any]
result: str | None                   # Not Optional[str]
items: list[str] | tuple[str, ...]   # Union types

# Use Optional only for explicit "None as default" semantics
def process(path: Path, callback: Callable[[int], None] | None = None) -> bool:
    ...
```

### Common Type Patterns

```python
from pathlib import Path
from typing import Any, Callable, TypeVar, Iterator
from collections.abc import Sequence, Mapping

# Basic types
count: int = 0
ratio: float = 0.5
name: str = ""
enabled: bool = False
data: bytes = b""

# Container types
items: list[str] = []
unique: set[int] = set()
mapping: dict[str, Any] = {}
coords: tuple[float, float] = (0.0, 0.0)

# Optional (nullable) types
result: str | None = None
config: dict[str, Any] | None = None

# Callable types
processor: Callable[[Path], bool]
callback: Callable[[int, str], None] | None = None

# Union types
value: int | float | str
path_like: str | Path

# Generic sequences (when accepting any iterable)
def process_items(items: Sequence[str]) -> list[str]:
    ...

# Type variables (for generic functions)
T = TypeVar('T')
def first_or_default(items: Sequence[T], default: T) -> T:
    return items[0] if items else default
```

### When Type Hints Are Optional

- **Obvious literal assignments:** `name = "example"` (clearly a string)
- **Simple loop counters:** `for i in range(10):` (clearly an int)
- **Throwaway variables:** `_ = unused_return_value`

However, even in these cases, adding type hints improves searchability and refactoring safety.

### Benefits of Comprehensive Type Hints

- **IDE autocomplete**: Editors show accurate suggestions
- **Error detection**: Catch type mismatches before runtime
- **Self-documenting**: Code shows intent without docstrings
- **Refactoring safety**: Rename operations track all usages
- **Static analysis**: Tools like pyright catch bugs early

7. Data and constants
- **Externalize large data.** Avoid embedding long strings (LLM prompts, default text, multi-line templates) or extensive datasets directly in code. Instead:
  - Create a `data/` subfolder within the module: `scripts/<module>/data/`
  - Store long text as plain `.txt` files (e.g., `system_prompt.txt`, `default_template.txt`)
  - Store structured data as `.json` files (e.g., `default_config.json`, `lookup_table.json`, `validation_rules.json`)
  - Load data at runtime with a helper function (e.g., `load_module_data("system_prompt.txt")`) or `pathlib` + `json.load()`
- **When to externalize**:
  - Strings longer than ~5 lines or ~300 characters
  - Any LLM prompt or template text
  - Default configurations with more than a few keys
  - Lookup tables, translation mappings, or reference data
  - Data that might be edited independently of code logic
- **Data file naming**: use descriptive snake_case names that indicate purpose (e.g., `classification_prompt.txt`, `supported_formats.json`, `error_messages.json`)
- **Prefer enums for fixed sets.** When a value comes from a known, fixed set of options, use `enum.Enum` or `enum.StrEnum` (Python 3.11+) instead of raw strings:
  ```python
  from enum import Enum, auto
  
  class OutputFormat(Enum):
      JSON = auto()
      CSV = auto()
      MARKDOWN = auto()
  ```
- **Use constants for repeated strings.** When a string is used as a key, identifier, or appears multiple times in a script, define it as a constant near the top of the file:
  ```python
  # Constants
  CONFIG_KEY_OUTPUT_DIR = "output_directory"
  CONFIG_KEY_VERBOSE = "verbose"
  DEFAULT_ENCODING = "utf-8"
  
  # Usage
  output_dir = config.get(CONFIG_KEY_OUTPUT_DIR, ".")
  ```
- **Constant naming**: use UPPER_SNAKE_CASE for module-level constants. Group related constants together with a comment header.
- **Benefits**: centralizing strings prevents typos, enables IDE rename refactoring, and makes the codebase easier to search and maintain.

8. JSON contracts (schemas)
- Policy: any script that consumes JSON must validate against a declared schema, and scripts that emit JSON should describe the schema in docs.
- Authoring: store JSON Schema drafts under `schemas/`; each schema should include an `$id` (e.g., `repo://schemas/<domain>/<name>.json`) and sample data.
- Versioning: when a breaking change happens, introduce a new schema or version field and update docs and examples together.
- Validation helpers: centralize parsing/validation (e.g., `schema_utils.parse_json()`, `construct_json()`); catch `ValueError` and surface concise, actionable errors.
- Tests & docs: reference the schema `$id` in docstrings/docs and include at least one passing and one failing test.

9. Pipelines vs. reusable helpers
- Build pipelines by composing generic helpers rather than hardcoding orchestration logic.
- Keep pipeline scripts thin: orchestrate utilities, validate inputs, and emit documented outputs.
- When a pipeline pattern proves generally useful, promote it to a reusable helper module and update dependent pipeline scripts accordingly.
- Document each pipeline's flow in an adjacent Markdown file (e.g., `video_processing_system.md`).

10. Utilities and imports
- Reuse first: search `util/`, `schemas/`, and existing docs before adding new helpers.
- Adding a new utility: include a concise docstring, a minimal unit test, and mention it in a nearby markdown doc if it surfaces in public scripts.
- Consolidation: when overlapping utilities exist, unify on one implementation and remove duplicates in the same session.
- Imports: prefer relative imports for intra-repo modules and avoid wildcard imports.
- dependencies: treat them as required; install them via `pip install -r requirements.txt` using the prescribed interpreter.
- Avoid try/except import fallbacks; document missing dependencies and fail fast.

11. Dependencies and environment
- **Auto-install is mandatory.** This repository requires a local `.venv` virtual environment and standardized bootstrap for all contributors.
- Before any code execution, run `install.bat` (Windows), which invokes `install.py` to:
  - Create `.venv` in the repository root if not present
  - Upgrade pip
  - Install all dependencies from `requirements.txt`
  - Check for expected native binaries under `dependencies/` and warn if missing
- Use the project's designated Python interpreter from `.venv\Scripts\python.exe`.
- Document command sequences in PowerShell snippets when targeting Windows users; chain commands with `;`, normalize paths with `Resolve-Path`, and quote spaces.
- For native binary dependencies (e.g., `ffmpeg`, `tesseract`, `yt-dlp`, JS runtimes):
  - **GUI exposure**: expose a path field in the GUI for each required binary, allowing manual selection of a specific executable.
  - **Fallback behavior**: if no path is specified, recursively search the `dependencies/` folder for the binary (e.g., find `ffmpeg.exe` anywhere under `dependencies/`, including subdirectories like `dependencies/ffmpeg-master-latest-win64-gpl-shared/bin/ffmpeg.exe`).
  - **Error handling**: if the binary is not found in either location, fail fast with a clear error message logging which binary was missing and where it was searched.
  - Place default executables in the repository `dependencies/` folder. The `install.bat` will not download or install system-native binaries, but it will check and warn if expected binaries are missing.
- For heavy dependencies (e.g., `torch`, `whisper`), note installation guidance in `requirements.txt` comments and fail fast when unavailable.

12. Paths and Windows safety
- Respect Windows path length by sanitizing filenames (`safe_filename()`) and keeping combined paths under ~240 characters.
- Validate and normalize directories before writing; create them with helpers like `ensure_directory_exists()`.
- Prefer `pathlib.Path` operations for readability and safety.
- When documenting samples, show PowerShell commands with `;` for chaining.

13. Performance and resource usage
- Process data in chunks and avoid loading large batches into memory unless necessary.
- Prefer CPU/PIL operations when GPU acceleration isn't required.
- Handle EXIF orientation (`Pillow.ImageOps.exif_transpose`) when working with images and minimize redundant conversions.

14. Errors and logging
- Fail fast on invalid required inputs; provide a `--continue-on-error` flag only when safe.
- Centralize logging via a shared `logging` helper; keep messages concise and include context (e.g., `f"{module}: {message}"`).
- Avoid global `print` statements—emit structured logs or CLI-friendly summaries.

15. Progress reporting
- For long-running scripts, use a progress reporter (custom helper or third-party) with bounded updates (~20 by default).
- Close reporters in `finally` blocks and summarize the work done.

16. Testing
- **Tests are mandatory and self-contained.** Every script or module must have co-located tests.
- **Use pytest.** All tests should be runnable via `pytest`. Use pytest-style test functions (`def test_*`) or unittest-style classes (`class Test*`).
- **Test file naming**: for each `script.py`, create a corresponding `test/script_test.py` in a `test/` subfolder.
- **Test co-location pattern**:
  ```
  scripts/<module>/
      script.py              # Core logic
      another.py             # Another script
      test/
          script_test.py     # Tests for script.py
          another_test.py    # Tests for another.py
          conftest.py        # pytest configuration and fixtures
          data/              # Test fixtures and sample data
              valid_input.txt
              sample_image.png
              expected_output.json
  ```
- **Test data guidelines**:
  - **Inline data**: use for simple/small fixtures (a few strings, numbers, small dicts)
  - **External files**: use for binary files (images, audio, PDFs), large text samples, or complex JSON
  - **Location**: place test data in `test/data/` subfolder
  - **Naming**: use descriptive names (`valid_input.txt`, `edge_case_empty.json`, `corrupted_image.png`)
  - **Minimal fixtures**: keep test data as small as possible while still testing the behavior
  - **Expected outputs**: for transformation tests, include both input and expected output files
- **Test requirements**:
  - Each script needs at least 1 happy path test + 1 edge case test
  - Include Windows-specific edge cases when relevant (path lengths, special characters)
  - Use `pytest` fixtures for shared setup (`@pytest.fixture`)
- **Test timeouts**: use `pytest-timeout` to prevent infinite loops from hanging test runs.
  - Default: 30 seconds per test (set via `conftest.py` or `pyproject.toml`)
  - Override per-test: `@pytest.mark.timeout(60)` for slow tests
  - Disable timeout: `@pytest.mark.timeout(0)` (use sparingly)
  - Copy `templates/conftest_template.py` to repo root or `test/` folders
- **Running tests**:
  ```powershell
  pytest                           # Run all tests (auto-discovers *_test.py)
  pytest scripts/<module>/test/    # Run module tests only
  pytest -k "test_function"        # Run specific test
  pytest -x                        # Stop on first failure
  pytest -v                        # Verbose output
  ```
- **Test templates**: use `templates/module_test_template.py` for individual script tests and `templates/submodule_test_template.py` for aggregated submodule tests.
- Prefer reusable debug tools over one-off scripts; promote quick tests to proper test files before committing.
- **Tests are strictly pass/fail.** Tests verify functional correctness only. Do not include profiling or benchmarking in test files—keep those concerns separate.

## 16a. Profiling and Benchmarking

**Profiling and benchmarking are separate from testing.** Tests verify correctness (pass/fail); profiling measures timing; benchmarking compares performance across parameters.

### When Profiling is Mandatory

**LLM agents MUST suggest adding profiling instrumentation when:**
- Code will be executed in batches (hundreds to thousands of times)
- Code runs in parallel across multiple workers
- Code processes batches of items (images, files, records)
- Code involves expensive operations (ML inference, compression, encoding, network I/O)

### Profiling Approach

**Embedded one-liner profiling with global toggle (preferred):**
- Use `lks_utils.profiling.profile_stage()` context managers in functional code
- Zero-cost when no profiler is set globally
- Enable profiling mode only when analyzing performance

```python
from lks_utils.profiling import profile_stage, set_global_profiler, Profiler

# Enable profiling (off by default)
if enable_profiling:
    set_global_profiler(Profiler("batch_compression"))

def compress_image(path: Path) -> CompressionResult:
    with profile_stage("load_image"):
        image = load_image(path)
    with profile_stage("encode"):
        result = encode_avif(image)
    with profile_stage("save"):
        save_image(result, output_path)
    return result
```

**External profiler scripts for detailed analysis:**
- Place in `<module>/test/<script>_profiler.py`
- Use for comprehensive stage timing and report generation
- Aggregate results from parallel workers

### Profiling File Structure

```
scripts/<module>/
    script.py                    # Core logic with embedded profile_stage() calls
    test/
        script_test.py           # Functional tests (pass/fail)
        script_profiler.py       # Detailed profiling script
        data/                    # Test/benchmark data
```

### Benchmarking

**Benchmarking** measures performance across different parameters using test data.

**Benchmark file structure:**
```
scripts/<module>/
    test/
        <script>_benchmark.py    # Benchmark individual script (if complex)
        <module>_benchmark.py    # Aggregates all script benchmarks OR single benchmark for trivial modules
        benchmark/
            data/                # Benchmark-specific test data
            results/             # Generated reports, graphs, CSVs
benchmark_all.py                 # Root: runs all module benchmarks
benchmark_all.bat                # Batch launcher
```

**Benchmark requirements:**
- Generate or use test data from `test/data/` or `test/benchmark/data/`
- Vary parameters systematically (e.g., file size, batch size, quality level)
- Produce readable output: JSON reports, CSV tables, or plots
- Common visualization: X-axis = parameter, Y-axis = time or throughput

**Benchmark templates:** Use `templates/script_profiler_template.py` and `templates/module_benchmark_template.py`.

### Profiling Suggestion Protocol

When an LLM agent detects high-iteration code, it should:
1. **Identify the pattern**: Note that the code will run many times
2. **Suggest profiling**: Recommend adding `profile_stage()` calls to key stages
3. **Offer implementation**: Provide the profiling instrumentation code
4. **Explain the benefit**: Describe what bottlenecks could be identified

## 16b. Batch Processing

For scripts expected to run in batches or requiring dynamic setup:

### Batcher Scripts

**When to create a batcher:**
- Script will be called hundreds to thousands of times in a batch
- Batch requires dynamic configuration based on system resources
- Results need to be accumulated and summarized across all runs
- Profile data needs aggregation from parallel workers

**Batcher file structure:**
```
scripts/<module>/
    script.py                # Core logic (single item)
    script_batcher.py        # Batch orchestration and result accumulation
```

**Batcher responsibilities:**
- Prepare batch of inputs (file lists, parameter combinations)
- Query system resources via `lks_utils.resources` to determine safe worker counts
- Execute batch using `lks_utils.concurrency` for parallel processing
- Accumulate results and profile data from all runs
- Generate summary report

**Example batcher pattern:**
```python
from lks_utils.resources import get_system_info, calculate_safe_workers, ResourceEstimate
from lks_utils.concurrency import process_in_parallel
from lks_utils.profiling import Profiler, set_global_profiler

def run_batch(input_paths: list[Path], enable_profiling: bool = False) -> BatchResult:
    # Estimate resource usage per item
    estimates = [ResourceEstimate(ram_gb=0.5, identifier=str(p)) for p in input_paths]
    
    # Calculate safe parallelism based on available RAM
    system_info = get_system_info()
    max_workers = calculate_safe_workers(estimates, system_info.available_ram_gb)
    
    # Enable profiling if requested
    if enable_profiling:
        set_global_profiler(Profiler("batch_run"))
    
    # Process in parallel with progress
    results = process_in_parallel(
        process_single_item,
        input_paths,
        max_workers=max_workers,
        progress_callback=update_progress
    )
    
    return accumulate_results(results)
```

**CLI batch commands:**
- Add `batch` subcommand to module CLIs: `python -m scripts.<module> batch --input-dir ./data`
- Support `--workers`, `--profile`, `--dry-run` flags

**Batcher template:** Use `templates/script_batcher_template.py`.

17. Examples
- Example scripts (under `examples/`) should demonstrate minimal workflows and stay in sync with the docs.

18. Documentation
- Document each script or utility next to the code it describes; include purpose, inputs/outputs, configuration, and error modes.
- Documentation is mandatory for multi-script submodules. Use the pattern `scripts/<module>/<module>_system.md` to describe the module scripts and how they relate to one another.
- Keep docs in sync with behavior; delete stale sections when functionality changes.
- Mention relevant schemas or helper modules within the docs.
- **Update `copilot_codebase_router.instructions.md` whenever you add/remove/modify submodules, scripts, or utilities.** The router is a living inventory and should reflect the current state of the codebase.
- **Keep `README.md` "Codebase Router" section in sync.** This repo may be consumed by external LLM agents that won't have `.github/instructions/` auto-loaded. The README's router section provides discoverability for external use.
- **Do not create transient change documents.** Never create markdown files, reports, or summaries that only document changes made in a session (e.g., `CHANGES.md`, `SUMMARY.md`, `implementation_report.md`). Update existing documentation in place instead.

19. Granularity and composition
- Keep modules composable: scripts orchestrate, utilities implement logic, and shared helpers stay agnostic.
- **Script size guideline**: aim to keep scripts under ~500 lines. When a script exceeds this, consider splitting it into multiple component files with descriptive names (e.g., `mesh_tools.py` → `mesh_subdivision.py` + `mesh_validation.py`). Only refactor when the script naturally divides into distinct responsibilities—don't force artificial splits.
- **No compatibility wrappers**: avoid legacy compatibility branches; replace deprecated code, update docs/tests, and remove unused modules during the same change. See Section 24a for full policy on avoiding shims.

20. Configuration and prompts
- Store reusable prompts, templates, or snippets under `prompt/` as `.md` or `.txt`; load them via helper functions (e.g., `prompt_utils.load_prompt`).
- Module-specific prompts and config defaults should go in `scripts/<module>/data/` rather than the repo-wide `prompt/` folder.
- When saving prompts or configs, sanitize filenames, keep contents UTF-8, and version them explicitly (`_v2`, timestamps, or YAML metadata).

21. Templates and boilerplate
- **Prefer templates over copy-paste.** Store reusable code templates under `templates/` to bootstrap new modules, scripts, or GUIs.
- Template usage: copy from `templates/`, rename appropriately, replace placeholder text (e.g., `<module>`), and customize to specific needs.
- Template maintenance: when a pattern proves useful across multiple scripts, promote it to a template. Keep templates minimal and well-commented.
- Available templates: see `templates/README.md` for the current inventory. Common templates include:
  - Module structure templates (core logic + GUI wrapper pattern)
  - Batch launcher templates
  - Configuration persistence templates
  - Test templates (when standardized patterns emerge)
- Template documentation: each template should include inline comments explaining customization points and expected usage patterns.
- **GUI templates for binary dependencies**: when creating GUIs for modules requiring external binaries, include file picker fields for each binary path. Load saved paths from config on startup; save updated paths on execution. Follow the pattern: user-specified path → recursive search in `dependencies/` → clear error if not found.
- Update inventory: when adding/removing templates, update both `templates/README.md` and the router file (`copilot_codebase_router.instructions.md`).

22. Additional best practices
- Deterministic configs: expose a seed and default to stable behavior for any randomness.
- Network timeouts/retries: set sane defaults and surface concise errors.
- Input validation: be strict with required fields and permissive with defaults for optional arguments.
- Include schema references in docs for JSON outputs and keep schemas small.
- Keep import-time work limited to dependency checks; all functional work should live in functions or the main entry.

23. External API adoption
- Before adopting a new external API or pattern, document the version/data format assumptions in PR notes or commit messages.

24. External shared utilities
- **Prefer shared repos over local duplication.** Before writing new utility code, check external shared repos listed in `copilot_external_deps.instructions.md`.
- **Contribute generic code upstream (MANDATORY when lks_utils is a dependency).** If `lks_utils` is installed in this project and you're writing utility code that isn't project-specific, you MUST:
  1. Add the utility to `lks_utils` instead of local `util/`
  2. Follow `lks_utils` style guide and instruction documents
  3. Add tests in `lks_utils` for the new functionality
  4. Add CLI commands if the utility is user-facing
  5. Update `lks_utils` documentation, README router section, and codebase router
  6. Import and use the utility from `lks_utils` in the local project
- **Install shared packages on-demand.** External repos with `pyproject.toml` can be installed via `pip install -e "C:\path\to\repo"`. Add to `requirements.txt` if the dependency is permanent.
- **Reading external repos.** The LLM is authorized to read code in registered external repos. Start with `README.md` for an overview; check `.github/instructions/copilot_codebase_router.instructions.md` if it exists for detailed routing.
- **Keep the external deps router updated.** When external repos add new functionality or when you register a new shared repo, update `copilot_external_deps.instructions.md`.
- **External repo README requirements.** Shared repos should maintain a "Codebase Router" summary section in their README.md so that LLM agents can discover available functionality without relying on auto-loaded instruction files.

24a. No Shims or Compatibility Wrappers
- **Avoid generating shims or wrappers** whose sole purpose is to provide a compatibility layer between old and new interfaces.
- **Always prefer full-stack deprecation**: when an interface changes, update ALL callers in the same session rather than adding wrapper code.
- **Rationale**: This is a single-user, locally-maintained codebase. Compatibility layers add complexity, obscure the actual implementation, and accumulate tech debt. It's better to fix things fully than to paper over changes.
- **When refactoring an interface**:
  1. Identify all callers (use `grep_search` or `list_code_usages`)
  2. Update the interface and all callers in one session
  3. Remove any old interface code entirely
  4. Update tests and documentation to reflect new interface
- **Exception**: Temporary shims are acceptable only when blocked by external dependencies outside this repo's control, and must be documented with a removal plan.

25. Lean-mode addendum (single-user repo)
- Philosophy: validate at boundaries, fail fast with concise errors, and keep scripts small and focused.
- Soft limits: scripts ≤ 500 lines; helper modules ≤ 1000 lines; functions ≤ 80 lines.
- Logging & progress: include a one-line success summary and limit progress updates to long-running loops.
- File I/O: prefer atomic writes (write to `.tmp` then rename), use deterministic naming (stable hash), and sanitize filenames.
- Cooperative cancel: if needed, support a cancel flag path and optional timeout.
- Loop template: preflight → iterate with cancel/progress → finally close → post-check → concise summary.
- Minimal helpers (optional):
  - `util/cancel_utils.py`: `should_cancel(flag_path) -> bool`; `CancelChecker(flag_path, timeout_s)` that raises when canceled.
  - `util/file_io_utils.py`: `atomic_write(path, data)`; `hash_from_config(obj, length=10)`.
  - `util/validation_utils.py`: lightweight `preflight_*` helpers (paths exist, list not empty, schema validate).
- Tests to actually run: per script—1 happy path + 1 boundary case; include a Windows edge case when relevant; optionally add a smoke workflow.

26. Debug scripts (reusable, not disposable)
- Place debugging/inspection scripts under `debug/`; keep them parameterized, documented, and dry-run by default.
- Use `argparse`, include a purpose docstring, and only mutate files when explicit `--write`/`--fix` flags are provided.
- Log via the shared logging utilities and write outputs under `debug/out/` when appropriate.

27. Terminal quick reference (PowerShell, Windows)
- Preferred Python: use the project's designated interpreter. Set an env var (e.g., `$env:PROJECT_PY`) once per session and call modules with `& $env:PROJECT_PY -m ...`.
- **Venv activation is critical.** Before running any Python commands, ensure the correct virtual environment is activated:
  ```powershell
  # Activate venv for current project
  .\.venv\Scripts\Activate.ps1
  
  # Or use full path to python directly
  .\.venv\Scripts\python.exe -m pytest
  ```
- **Multi-folder workspaces**: When working in a VS Code workspace with multiple folders, each folder may have its own `.venv`. Always activate the venv for the folder you're currently working in.
- **Missing dependency errors**: If you encounter `ModuleNotFoundError` or `ImportError`, the FIRST thing to check is whether the correct venv is activated. Do not investigate the codebase deeply until you've confirmed:
  1. The venv exists (`.venv/` folder present)
  2. The venv is activated (run `.\.venv\Scripts\Activate.ps1`)
  3. Dependencies are installed (`pip install -r requirements.txt`)
- Examples:
  ```powershell
  $env:PROJECT_PY = 'C:\path\to\venv\Scripts\python.exe'
  & $env:PROJECT_PY -V
  & $env:PROJECT_PY -m tests.runner --config .\tests\config.yaml
  ```
- Notes (PowerShell v5.1):
  - Chain commands with `;`, not Bash `&&`.
  - Avoid here-docs; use `python -c "..."` for inline scripts.
  - Quote paths with spaces and normalize with `Resolve-Path` when sharing documentation.
