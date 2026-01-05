"""
Match polygon density across all sculpt objects using resampling.

Uses the selected object as the reference and resamples all other objects in the
entire sculpt tree to match its polygon density.

Room: Sculpt
Action: Resample all sculpt objects to match reference density
"""
from utils.action_base import action


@action
def main() -> None:
    """Resample all objects to match selected object's density."""
    from ops.SculptObject_UniformDensity import main as op_main, DensityMode
    from utils.scope_utils import Scope

    op_main(scope=Scope.ALL, mode=DensityMode.RESAMPLE)


main()
