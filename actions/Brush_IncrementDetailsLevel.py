"""
Increment Details Level

Increments the brush details level by 1 and applies to current brush.
Use 'Apply to Brushes' in LKS panel to apply to all brush types.

Room: Sculpt
Action: Increment details level, apply to current brush
"""
from utils.action_base import action


@action
def main() -> None:
    """Increment brush details level."""
    from ops.Brush_DetailsLevel import adjust_details_level, DetailsLevelMode, ApplyScope

    adjust_details_level(
        mode=DetailsLevelMode.INCREMENT,
        apply_scope=ApplyScope.CURRENT,
    )


main()
