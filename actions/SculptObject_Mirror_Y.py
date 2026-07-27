"""
Toggle mirror symmetry for the Y axis.

Room: Sculpt
Action: Toggle Y-axis mirror symmetry on/off (no geometry change)
"""
from utils.action_base import action


@action
def main() -> None:
    """Toggle Y-axis mirror symmetry."""
    from ops.SculptObject_Mirror import main as op_main

    op_main(axis="Y")


main()
