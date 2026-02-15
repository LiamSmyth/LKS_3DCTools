"""
Batch convert action scripts to use @action decorator pattern.

This converts scripts from various patterns to the canonical pattern:

    from utils.action_base import action

    @action
    def main() -> None:
        '''Original docstring.'''
        from ops.SomeOp import main as op_main
        op_main(...)

    main()

Run from LKS root:
    python _tools/convert_to_decorator.py [--dry-run]
"""
from pathlib import Path
import re
import sys

ACTIONS_DIR = Path(__file__).parent.parent / "actions"

# Scripts to skip entirely (lifecycle/special scripts)
SKIP_SCRIPTS = {
    "LKS_Register.py",
    "LKS_Unregister.py",
    "LKS_FullReload.py",
    "LKS_Tools_Panel.py",
    "LKS_ExternalPanel_Launch.py",
    "LKS_ExternalPanel_Stop.py",
}


def extract_docstring(content: str) -> tuple[str, str]:
    """Extract module docstring and return (docstring, rest_of_content)."""
    # Match triple-quoted docstring at start of file
    match = re.match(r'^("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*\n', content)
    if match:
        return match.group(1), content[match.end():]
    return '', content


def already_has_decorator(content: str) -> bool:
    """Check if script already uses @action decorator."""
    return '@action' in content and 'from utils.action_base import action' in content


def has_main_function(content: str) -> bool:
    """Check if script has a main() function."""
    return re.search(r'^def main\s*\(', content, re.MULTILINE) is not None


def is_inline_script(content: str) -> bool:
    """Check if script has inline execution without main()."""
    lines = [l.strip() for l in content.split('\n') if l.strip()
             and not l.strip().startswith('#')]
    # Has imports and ends with function call(s)
    has_import = any(l.startswith(('from ', 'import ')) for l in lines)

    # Check if last meaningful lines are function calls (not def/class)
    for line in reversed(lines):
        if line.startswith(('def ', 'class ', 'from ', 'import ', '"""', "'''")):
            continue
        # Looks like a function call
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
            return True
        break
    return False


def convert_inline_to_main(content: str) -> tuple[str, str]:
    """
    Convert an inline script (no main function) to use @action decorator.

    Pattern:
        '''docstring'''
        from something import func
        func()

    Becomes:
        '''docstring'''
        from utils.action_base import action

        @action
        def main() -> None:
            from something import func
            func()

        main()
    """
    # Extract docstring
    docstring, rest = extract_docstring(content)

    lines = rest.split('\n')
    imports = []
    body_lines = []

    # Separate imports from execution
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('from ', 'import ')):
            imports.append(stripped)
        elif stripped.startswith('#'):
            # Keep comments with body
            body_lines.append(stripped)
        else:
            body_lines.append(stripped)

    if not body_lines:
        return content, "SKIP (no executable code)"

    # Build new script
    result_lines = []

    if docstring:
        result_lines.append(docstring)

    result_lines.append('from utils.action_base import action')
    result_lines.append('')
    result_lines.append('')
    result_lines.append('@action')
    result_lines.append('def main() -> None:')
    result_lines.append('    """Execute the action."""')

    # Add imports inside main
    for imp in imports:
        result_lines.append(f'    {imp}')

    if imports:
        result_lines.append('')

    # Add body
    for line in body_lines:
        result_lines.append(f'    {line}')

    result_lines.append('')
    result_lines.append('')
    result_lines.append('main()')
    result_lines.append('')

    return '\n'.join(result_lines), "CONVERTED (inline)"


def find_main_function_call(content: str) -> bool:
    """Check if script calls main() at the end."""
    # Look for main() call at module level (not indented)
    lines = content.strip().split('\n')
    for line in reversed(lines):
        stripped = line.strip()
        if stripped == 'main()':
            return True
        if stripped and not stripped.startswith('#'):
            break
    return False


def extract_function_body(content: str, func_name: str) -> tuple[str, int, int]:
    """Extract function body and return (body, start_line, end_line)."""
    lines = content.split('\n')
    in_function = False
    func_indent = 0
    body_lines = []
    start_line = -1
    end_line = -1

    for i, line in enumerate(lines):
        if re.match(rf'^def {func_name}\s*\(', line):
            in_function = True
            start_line = i
            # Get base indentation
            func_indent = len(line) - len(line.lstrip())
            continue

        if in_function:
            if line.strip() == '':
                body_lines.append(line)
                continue

            line_indent = len(line) - len(line.lstrip())
            if line_indent > func_indent:
                body_lines.append(line)
            else:
                end_line = i
                break

    if end_line == -1:
        end_line = len(lines)

    return '\n'.join(body_lines), start_line, end_line


def strip_old_reload_pattern(body: str) -> str:
    """Remove old hot-reload import and call from function body."""
    # Remove the reload_all pattern
    patterns = [
        r'^\s*# Hot reload all LKS modules.*\n\s*from utils\.hot_reload import reload_all\n\s*reload_all\(\)\n*',
        r'^\s*from utils\.hot_reload import reload_all\n\s*reload_all\(\)\n*',
    ]
    for pattern in patterns:
        body = re.sub(pattern, '', body, flags=re.MULTILINE)
    return body


def convert_script(content: str) -> tuple[str, str]:
    """
    Convert a script to use @action decorator pattern.

    Returns:
        (converted_content, status_message)
    """
    if already_has_decorator(content):
        return content, "SKIP (already has @action)"

    if not has_main_function(content):
        # Try to convert inline script
        if is_inline_script(content):
            return convert_inline_to_main(content)
        return content, "SKIP (no main() or inline pattern)"

    # Extract docstring
    docstring, rest = extract_docstring(content)

    # Extract main function body
    body, start, end = extract_function_body(rest, 'main')

    if not body:
        return content, "SKIP (empty main function)"

    # Clean up the body - remove old reload pattern
    clean_body = strip_old_reload_pattern(body)

    # Get the main() signature from original
    lines = rest.split('\n')
    main_def_line = ''
    for line in lines:
        if re.match(r'^def main\s*\(', line):
            main_def_line = line
            break

    # Check if has return type annotation
    if '-> None' not in main_def_line and '->' not in main_def_line:
        main_def_line = main_def_line.rstrip(':') + ' -> None:'

    # Extract function docstring from body if present
    func_docstring = ''
    body_lines = clean_body.split('\n')
    first_content = ''
    for i, line in enumerate(body_lines):
        stripped = line.strip()
        if stripped:
            first_content = stripped
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Found docstring
                quote = stripped[:3]
                if stripped.count(quote) >= 2:
                    # Single line docstring
                    func_docstring = stripped
                    body_lines = body_lines[i+1:]
                else:
                    # Multi-line - find end
                    ds_lines = [stripped]
                    for j in range(i+1, len(body_lines)):
                        ds_lines.append(body_lines[j].strip())
                        if quote in body_lines[j]:
                            body_lines = body_lines[j+1:]
                            break
                    func_docstring = '\n    '.join(ds_lines)
            break

    clean_body = '\n'.join(body_lines)

    # Build new script
    result_lines = []

    # Module docstring
    if docstring:
        result_lines.append(docstring)

    # Import
    result_lines.append('from utils.action_base import action')
    result_lines.append('')
    result_lines.append('')

    # Decorated function
    result_lines.append('@action')
    result_lines.append(main_def_line)

    if func_docstring:
        result_lines.append(f'    {func_docstring}')

    # Re-indent body if needed
    for line in clean_body.split('\n'):
        if line.strip():
            result_lines.append(line)
        else:
            result_lines.append('')

    result_lines.append('')
    result_lines.append('')
    result_lines.append('main()')
    result_lines.append('')

    return '\n'.join(result_lines), "CONVERTED"


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("DRY RUN - no files will be modified\n")

    scripts = sorted(ACTIONS_DIR.glob("*.py"))

    converted = 0
    skipped = 0

    for script_path in scripts:
        if script_path.name in SKIP_SCRIPTS:
            print(f"SKIP (lifecycle): {script_path.name}")
            skipped += 1
            continue

        content = script_path.read_text(encoding='utf-8')
        new_content, status = convert_script(content)

        if status.startswith("CONVERTED"):
            if not dry_run:
                script_path.write_text(new_content, encoding='utf-8')
            print(f"{status}: {script_path.name}")
            converted += 1
        else:
            print(f"{status}: {script_path.name}")
            skipped += 1

    print(f"\nSummary: {converted} converted, {skipped} skipped")


if __name__ == "__main__":
    main()
