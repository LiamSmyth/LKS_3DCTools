"""
Setup a 3x3 tiling grid with a plane primitive.

Room: Sculpt
Action: Creates center plane with 8 surrounding instances and translation symmetry.
"""
from utils.Scene_tiling_utils import (
    TilingParams,
    PrimitiveType,
    setup_tiling_grid,
)

# Configure and run
params: TilingParams = TilingParams(
    base_size=64,
    primitive_type=PrimitiveType.PLANE,
)

setup_tiling_grid(params)
