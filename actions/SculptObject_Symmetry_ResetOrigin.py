"""
Reset symmetry origin to world center (preserve active axes).

Room: Sculpt
Action: Open symmetry pane, ResetSymm, then restore cached mirror axes
"""
from utils.action_base import action


@action
def main() -> None:
    """Reset symmetry pivot to world origin without clearing axis state."""
    from utils.symmetry_utils import reset_symmetry_origin_to_world

    reset_symmetry_origin_to_world()


main()
