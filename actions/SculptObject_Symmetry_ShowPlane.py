"""
Toggle symmetry plane visibility.

Room: Sculpt
Action: Toggle the symmetry plane visualization, persisted to LKS settings
"""
from utils.action_base import action


@action
def main() -> None:
    """Toggle symmetry plane visibility on/off."""
    from utils.symmetry_utils import toggle_show_symmetry_plane

    toggle_show_symmetry_plane()


main()
