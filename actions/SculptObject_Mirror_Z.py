"""
Toggle mirror symmetry for the Z axis.

Room: Sculpt
Action: Toggle Z-axis mirror symmetry on/off (no geometry change)
"""
from utils.action_base import action


@action
def main() -> None:
    """Toggle Z-axis mirror symmetry."""
    from ops.SculptObject_Mirror import main as op_main

    op_main(axis="Z")


main()
