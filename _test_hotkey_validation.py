"""Test script to validate and clean up hotkeys file."""
import hotkey_utils
import sys
from pathlib import Path

# Add LKS utils directly to avoid coat imports
lks_root = Path(__file__).parent
utils_path = lks_root / "utils"
sys.path.insert(0, str(utils_path))

# Import only hotkey_utils (doesn't require coat)


def main():
    # Load the file
    hotkeys_path = Path(
        r"c:\BTS_SSD\3DCoat_Userprefs_SSD_2025\MyDocuments\UserPrefs\Preferences\Options_Hotkeys.xml")

    print(f"Loading: {hotkeys_path}")
    hotkeys = hotkey_utils.parse_hotkeys_file(hotkeys_path)

    print(f"\nParsed {len(hotkeys.entries)} entries")

    if hotkeys.parse_errors:
        print(f"\n⚠️ Parse errors:")
        for err in hotkeys.parse_errors:
            print(f"  - {err}")

    # Validate
    print("\nValidating...")
    hotkey_utils.validate_all(hotkeys)

    # Show stats
    duplicates = sum(1 for e in hotkeys.entries if e.is_duplicate)
    conflicts = sum(1 for e in hotkeys.entries if e.conflict_ids)
    orphans = sum(1 for e in hotkeys.entries if e.is_orphan_room)
    unassigned = sum(1 for e in hotkeys.entries if not e.is_assigned)

    print(f"\nStats:")
    print(f"  - Duplicates: {duplicates}")
    print(f"  - Conflicts: {conflicts}")
    print(f"  - Orphan rooms: {orphans}")
    print(f"  - Unassigned: {unassigned}")

    # Try removing duplicates
    print("\nRemoving duplicates...")
    unique, removed = hotkey_utils.remove_duplicates(hotkeys.entries)
    print(f"  Removed {removed} duplicates")
    hotkeys.entries = unique

    # Re-validate
    hotkey_utils.validate_all(hotkeys)

    # Try to save to test file
    test_output = hotkeys_path.parent / "Options_Hotkeys_TEST_OUTPUT.xml"
    print(f"\nSaving to: {test_output}")
    hotkey_utils.save_hotkeys_file(
        hotkeys, test_output, create_backup_first=False)

    # Try to parse it back to validate XML structure
    print("\nValidating output XML...")
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(test_output)
        root = tree.getroot()
        hotkey_count = len(root.findall('.//OneHotKey'))
        print(f"✓ Valid XML! Found {hotkey_count} hotkey entries")
    except ET.ParseError as e:
        print(f"✗ Invalid XML: {e}")
        return False

    print("\n✓ Test complete!")
    return True


if __name__ == "__main__":
    main()
