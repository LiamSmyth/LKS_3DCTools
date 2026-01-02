---
applyTo: '**'
---

# Python Script Workspace Router

A ledger of existing code, utilities, and resources. This file provides quick links to what currently exists in the repository—not instructions for what to build. For engineering rules and patterns, see `copilot_style_guide.instructions.md`.

## 🚦 Start Here
- `copilot_style_guide.instructions.md`: canonical engineering rules and Python scripting policy.
- `copilot_external_deps.instructions.md`: external shared repos, installation, and contribution rules.
- `README.md`: workspace overview and install/setup pointers.
- `requirements.txt`: authoritative dependency list for `pip install -r requirements.txt`.
- `install.bat` / `install.py`: mandatory auto-install bootstrap—creates `.venv`, upgrades pip, installs dependencies, checks for binaries in `bin/`.

## 🖥️ Environment Defaults
- Windows + PowerShell (`powershell.exe` v5.1). Chain commands with `;`, normalize paths with `Resolve-Path`, and prefer double quotes around strings with spaces.
- Auto-install and venv: this repository requires a local `.venv` virtual environment. Contributors must run `install.bat` which will create/activate a `.venv`, upgrade pip, and install dependencies from `requirements.txt`.
- Native binaries: place required executables (e.g., `ffmpeg.exe`, `tesseract.exe`) under `Dependencies/` at the repository root. The `install.bat` will check for expected native binaries and warn if missing—it will not download or install system-native tools.

## 🗺️ Folder Structure
- `scripts/` – main code and submodules. Submodules live under `scripts/<module>/` with an `__init__.py` file. Tests live in `scripts/<module>/test/` as `*_test.py` files with fixtures in `test/data/`.
- `scripts/<module>/data/` – module-specific static data: long text strings (LLM prompts, templates), default configs, and lookup tables stored as `.txt` or `.json` files. See style guide section 7.
- `util/` – reusable helpers (path ops, logging, JSON, validation). Reuse before writing new logic.
- `schemas/` – JSON Schema definitions that describe config/input/output contracts.
- `prompt/` – stored prompts, templates, or snippets used by scripts (repo-wide); module-specific prompts go in `scripts/<module>/data/`.
- `templates/` – code templates for bootstrapping new modules, GUIs, tests, profilers, benchmarks, and batchers. Copy, rename, and customize.
- `Dependencies/` – native executables and binaries required by scripts (Windows binary files such as `ffmpeg.exe`, `tesseract.exe`) that cannot be installed via pip.
- `debug/` – inspection and validation scripts; parameterized and dry-run by default.
- `examples/` – minimal demos illustrating common flows.
- `run_tests.py` – recursive test runner that discovers and runs all `*_test.py` files.
- `run_tests.bat` – batch launcher for running all tests.
- `benchmark_all.py` – recursive benchmark runner that discovers and runs all `*_benchmark.py` files.
- `benchmark_all.bat` – batch launcher for running all benchmarks.
- `template_cleanup.py` – removes template content while preserving folder structure (for new projects).
- `template_cleanup.bat` – batch launcher for template cleanup.

## 🧩 Scripts & Submodules

### Current Submodules
_No submodules yet—this section will list each `scripts/<module>/` directory once created._

### Standalone Scripts
_No standalone scripts yet—this section will list individual scripts in `scripts/` when added._

## 🛠️ Utility Modules

### Current Utilities
_No utilities yet—this section will list each module in `util/` once created._

Add utilities here as they're built. Include:
- Module name (e.g., `path_utils.py`)
- Brief description (1-2 sentences)
- Key functions/classes

## 📦 Schemas
_No schemas yet—this section will list each schema file in `schemas/` with its `$id` and purpose._

## 📋 Templates

Ready-to-use code templates for bootstrapping new components. Copy from `templates/`, customize placeholders (e.g., `<module>`), and adapt to your needs.

### Module Templates
- **`module_template.py`** - Core business logic with CLI interface using argparse. Pure functions, no GUI dependencies, fully testable via command line.
- **`module_gui_template.py`** - GUI wrapper using ttkbootstrap. Calls core logic from `<module>.py`. Implements `create_gui_panel(parent)` for tab integration and standalone `main()`.
- **`main_gui_template.py`** - Main tabbed GUI container using ttkbootstrap Notebook. Hosts multiple module GUIs as tabs.

### Configuration Templates
- **`gui_config_template.py`** - Configuration persistence and preset management for GUIs with 5+ properties. Includes `GUIConfig` class, auto-save/restore, and preset controls.

### Batch Launchers
- **`run_main_gui.bat`** - Launch main tabbed GUI application.
- **`run_module_gui.bat`** - Launch individual module GUI standalone.

### Test Templates
- **`module_test_template.py`** - Co-located test file for individual scripts. Pure pytest-style test functions with fixtures, example happy path + edge case tests.
- **`submodule_test_template.py`** - Integration test file for entire submodules. pytest auto-discovers all `*_test.py` files. Use for tests that exercise multiple scripts together.
- **`conftest_template.py`** - Pytest configuration with default 30-second timeout. Prevents infinite loops from hanging test runs.

### Profiling and Benchmarking Templates
- **`script_profiler_template.py`** - Profile individual script execution using `lks_utils.profiling.Profiler`. Place in `<module>/test/<script>_profiler.py`. Generates JSON reports with stage breakdowns.
- **`module_benchmark_template.py`** - Parameterized benchmark suite for modules. Place in `<module>/test/<module>_benchmark.py`. Varies parameters and generates CSV/JSON/plot outputs.

### Batch Processing Templates
- **`script_batcher_template.py`** - Resource-aware batch execution orchestrator. Uses `lks_utils.resources` for RAM-aware worker calculation and `lks_utils.concurrency` for parallel processing.

### Package Configuration
- **`pyproject_template.toml`** - pip-installable package config. Copy to repo root as `pyproject.toml` when this repo is a shared utility module. See `copilot_external_deps.instructions.md` for setup guidance.

See `templates/README.md` for detailed usage instructions and architecture principles.

## 🧪 Debug Scripts
_No debug scripts yet—this section will list parameterized inspection tools in `debug/`._

## 📄 Documentation
- Co-locate docs with code: place markdown next to the scripts it describes.
- Multi-script submodules: use `scripts/<module>/<module>_system.md` to describe how module scripts relate.

## 🔗 External Shared Repos

See `copilot_external_deps.instructions.md` for:
- Registered external utility repos and what they provide
- Installation instructions (pip editable installs)
- Decision tree: write locally vs. contribute upstream
- How to read and contribute to external repos

_External repos should maintain a "Codebase Router" section in their README.md for LLM discovery._

---

## ⚠️ Keeping This Router Updated

**This is a living inventory, not a design template.** Update this file whenever you:
- Add a new submodule under `scripts/<module>/`
- Create a standalone script in `scripts/`
- Add a utility module to `util/`
- Define a new schema in `schemas/`
- Create a debug script in `debug/`
- Add or remove a template in `templates/`

When in doubt, add a short bullet describing your new component so the next editor can discover it instantly.
