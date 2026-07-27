"""
Toggle mirror symmetry for the X axis.

Room: Sculpt
Action: Toggle X-axis mirror symmetry on/off (no geometry change)
"""
from utils.action_base import action


@action
def main() -> None:
    """Toggle X-axis mirror symmetry."""
    from ops.SculptObject_Mirror import main as op_main

    op_main(axis="X")


main()
