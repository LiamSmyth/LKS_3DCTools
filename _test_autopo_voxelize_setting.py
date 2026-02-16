"""
Test script to discover the correct autopo voxelize polycount magic string.

Usage:
1. Open 3DCoat with a sculpt object
2. Run this script from Scripts menu
3. Check console output to see which setting names work
4. Update autopo_utils.py with the correct magic string

To discover the actual UI element ID:
- Open autopo dialog manually (Mesh > Auto retopology)
- Enable "Voxelize" checkbox
- RMB+MMB on the polycount input field
- The magic string ID will be copied to clipboard
"""
import coat


def main() -> None:
    """Test various possible magic strings for autopo voxelize polycount."""
    print("\n" + "=" * 60)
    print("Testing Autopo Voxelize Polycount Magic Strings")
    print("=" * 60)

    # Test value (1000 = 1M polys in K units)
    test_value: int = 1000

    # Candidate magic strings to test
    candidates: list[tuple[str, str]] = [
        ("$QuadragulationTask::VoxelizedObjectPolycount1", "Current (line 47)"),
        ("$QuadragulationTask::VoxelizePolycount", "Alternative 1"),
        ("$QuadragulationTask::VoxelizePolycount1", "Alternative 2"),
        ("$QuadragulationTask::VoxelizedPolycount", "Alternative 3"),
        ("$QuadragulationTask::VoxelDensity", "Alternative 4"),
        ("$QuadragulationTask::VoxelResolution", "Alternative 5"),
        ("$QuadragulationTask::VoxelSize", "Alternative 6"),
    ]

    print(f"\nTest value: {test_value} (K polys)\n")

    results: list[tuple[str, str, bool]] = []

    for magic_string, description in candidates:
        # Try setEditBoxValue with int
        result: bool = coat.ui.setEditBoxValue(magic_string, test_value)
        results.append((magic_string, description, result))

        status: str = "✓ SUCCESS" if result else "✗ FAILED"
        print(f"{status} | {description:20s} | {magic_string}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    success: list[tuple[str, str, bool]] = [
        (s, d, r) for s, d, r in results if r]
    if success:
        print("\nWorking magic strings:")
        for magic_string, description, _ in success:
            print(f"  - {magic_string}")
            print(f"    Update line 47 in autopo_utils.py")
    else:
        print("\n❌ No working magic strings found!")
        print("\nNext steps:")
        print("1. Open autopo dialog manually (Mesh > Auto retopology)")
        print("2. Enable 'Voxelize' checkbox")
        print("3. RMB+MMB on the polycount input field")
        print("4. Paste clipboard to see actual magic string ID")

    print("\n" + "=" * 60)

    # Try reading back values to verify
    print("\nVerifying by reading back values:")
    for magic_string, description, set_result in results:
        if set_result:
            # Try reading it back (if there's a corresponding get method)
            # Note: coat.pyi may not have a getEditBoxValue method
            try:
                # Most get methods don't exist in coat API
                print(f"  {magic_string}: (no way to verify - no getter in API)")
            except Exception as e:
                print(f"  {magic_string}: Cannot verify - {e}")

    coat.ui.showInfoMessage("Check console for test results", 3000)


if __name__ == "__main__":
    main()
