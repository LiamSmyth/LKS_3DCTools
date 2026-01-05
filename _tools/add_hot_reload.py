"""
Utility script to add hot-reload pattern to all action scripts.

Run this from the LKS root directory:
    python _tools/add_hot_reload.py

This transforms action scripts from:
    from some_module import something
    
    def main():
        something()
    
    main()

To:
    def main():
        from utils.hot_reload import reload_all
        reload_all()
        
        from some_module import something
        something()
    
    main()
"""
from pathlib import Path
import re


ACTIONS_DIR = Path(__file__).parent.parent / "actions"

# Scripts to skip (lifecycle scripts that shouldn't hot-reload)
SKIP_SCRIPTS = {
    "LKS_Register.py",
    "LKS_Unregister.py",
    "LKS_FullReload.py",
    "LKS_Tools_Panel.py",
    "LKS_ExternalPanel_Launch.py",
    "LKS_ExternalPanel_Stop.py",
}

HOT_RELOAD_IMPORT = '''    # Hot reload all LKS modules to pick up code changes
    from utils.hot_reload import reload_all
    reload_all()

'''


def transform_script(content: str) -> str:
    """Transform a script to use hot-reload pattern."""

    # Check if already has hot reload
    if "from utils.hot_reload import reload_all" in content:
        return content  # Already transformed

    lines = content.split('\n')
    new_lines = []

    # State tracking
    in_docstring = False
    docstring_ended = False
    imports_started = False
    imports_collected = []
    main_def_found = False
    inside_main = False
    main_body_lines = []
    after_main_def = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track docstring at start
        if not docstring_ended:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                if in_docstring:
                    # End of docstring
                    new_lines.append(line)
                    in_docstring = False
                    docstring_ended = True
                elif stripped.count(quote) >= 2:
                    # Single-line docstring
                    new_lines.append(line)
                    docstring_ended = True
                else:
                    # Start of multi-line docstring
                    new_lines.append(line)
                    in_docstring = True
                i += 1
                continue
            elif in_docstring:
                new_lines.append(line)
                i += 1
                continue

        # Collect top-level imports
        if docstring_ended and not main_def_found:
            if stripped.startswith(('from ', 'import ')) and not stripped.startswith('from __future__'):
                imports_collected.append(line)
                imports_started = True
                i += 1
                continue
            elif stripped == '' and imports_started:
                # Blank line between imports or after
                i += 1
                continue
            elif stripped.startswith('def main'):
                main_def_found = True
                # Don't add imports here - they'll go inside main
                new_lines.append('')  # Blank line before def
                new_lines.append('')
                new_lines.append(line)  # def main():
                inside_main = True
                i += 1
                continue
            elif stripped and not stripped.startswith('#'):
                # Non-import, non-comment code at top level before main
                # This is a script without main() - different pattern
                break

        # Inside main function
        if inside_main and main_def_found:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Docstring inside main
                quote = stripped[:3]
                if stripped.count(quote) >= 2:
                    new_lines.append(line)
                else:
                    # Multi-line docstring
                    new_lines.append(line)
                    i += 1
                    while i < len(lines):
                        new_lines.append(lines[i])
                        if quote in lines[i]:
                            break
                        i += 1
                # Add hot reload after docstring
                new_lines.append(HOT_RELOAD_IMPORT.rstrip())
                # Add moved imports
                for imp in imports_collected:
                    # Indent imports to be inside function
                    new_lines.append('    ' + imp.strip())
                if imports_collected:
                    new_lines.append('')
                imports_collected = []  # Clear so we don't add again
                i += 1
                continue
            elif line.startswith('    ') or stripped == '':
                # Body of main - if we haven't added reload yet, add it
                if imports_collected:
                    new_lines.append(HOT_RELOAD_IMPORT.rstrip())
                    for imp in imports_collected:
                        new_lines.append('    ' + imp.strip())
                    new_lines.append('')
                    imports_collected = []
                new_lines.append(line)
                i += 1
                continue
            else:
                # End of main function
                inside_main = False
                new_lines.append(line)
                i += 1
                continue

        new_lines.append(line)
        i += 1

    return '\n'.join(new_lines)


def process_file(filepath: Path) -> bool:
    """Process a single file. Returns True if modified."""
    content = filepath.read_text(encoding='utf-8')

    # Check for patterns that indicate non-standard scripts
    if 'def main' not in content:
        print(f"  SKIP (no main): {filepath.name}")
        return False

    if "from utils.hot_reload import reload_all" in content:
        print(f"  SKIP (already done): {filepath.name}")
        return False

    new_content = transform_script(content)

    if new_content != content:
        filepath.write_text(new_content, encoding='utf-8')
        print(f"  UPDATED: {filepath.name}")
        return True
    else:
        print(f"  SKIP (no changes): {filepath.name}")
        return False


def main():
    print(f"Processing action scripts in: {ACTIONS_DIR}")
    print("-" * 60)

    updated = 0
    skipped = 0

    for py_file in sorted(ACTIONS_DIR.glob("*.py")):
        if py_file.name in SKIP_SCRIPTS:
            print(f"  SKIP (lifecycle): {py_file.name}")
            skipped += 1
            continue

        if process_file(py_file):
            updated += 1
        else:
            skipped += 1

    print("-" * 60)
    print(f"Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
