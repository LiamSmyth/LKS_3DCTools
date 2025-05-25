"""
UI Dialog Utilities

Common utility functions for 3DCoat UI dialog operations.
This module provides static functions for common dialog patterns.

Note: Files starting with "_" are hidden from the Addons menu per 3DCoat convention.
"""
import coat
from typing import Callable, Optional


class UIDialogUtils:
    """Static utility functions for 3DCoat UI dialog operations"""

    @staticmethod
    def execute_resample_dialog(target_polycount: int, resample_scale: float = 0.5) -> None:
        """
        Execute the resample dialog with specified parameters.

        Args:
            target_polycount: Target polygon count
            resample_scale: Resampling scale factor (default 0.5)
        """
        def ui_command():
            coat.ui.setEditBoxValue(
                "$ResampleParams::RequiredPolycount", target_polycount)
            coat.ui.setSliderValue(
                "$ResampleParams::ResamplingScale", resample_scale)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$Resample", ui_command)

    @staticmethod
    def execute_decimation_dialog(target_polycount: Optional[int] = None, reduction_percent: Optional[float] = None) -> None:
        """
        Execute the decimation dialog with specified parameters.

        Args:
            target_polycount: Target polygon count (optional)
            reduction_percent: Reduction percentage (optional)
        """
        def ui_command():
            if target_polycount is not None:
                coat.ui.setEditBoxValue(
                    "$DecimationParams::ReducedPolycount", target_polycount)
            if reduction_percent is not None:
                coat.ui.setSliderValue(
                    "$DecimationParams::ReductionPercent", reduction_percent)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$Decimate", ui_command)

    @staticmethod
    def execute_voxel_conversion_dialog(suggested_polycount: int) -> None:
        """
        Execute voxel conversion with suggested polycount.

        Args:
            suggested_polycount: Suggested polygon count for voxelization
        """
        def ui_command():
            coat.ui.setEditBoxValue(
                "$VoxelizeParams::SuggestedPolycount", suggested_polycount)
            coat.ui.cmd("$DialogButton#1")

        coat.ui.cmd("$ToVoxels", ui_command)

    @staticmethod
    def execute_decimate_to_half() -> None:
        """Execute decimation to approximately half the polycount (80% reduction)."""
        UIDialogUtils.execute_decimation_dialog(reduction_percent=80.0)

    @staticmethod
    def execute_resample_to_half(current_polycount: int) -> None:
        """
        Execute resampling to half the current polycount.

        Args:
            current_polycount: Current polygon count
        """
        target_polycount = current_polycount // 2
        UIDialogUtils.execute_resample_dialog(target_polycount, 0.5)

    @staticmethod
    def execute_resample_to_polycount(initial_polycount: int, tgt_polycount: int) -> None:
        """
        Execute resampling to half the current polycount.

        Args:
            current_polycount: Current polygon count
        """
        ratio = tgt_polycount / initial_polycount

        UIDialogUtils.execute_resample_dialog(
            tgt_polycount + 1000, ratio * 1.1)

        print(" Resampling: Initial polycount: %s Target polycount: %s Ratio: %s" %
              (initial_polycount, tgt_polycount, ratio))

    @staticmethod
    def execute_resample_element_to_polycount(element: coat.SceneElement, tgt_polycount: int) -> None:
        """
        Execute resampling to half the current polycount.

        Args:
            current_polycount: Current polygon count
        """
        initial_polycount = element.Volume().getPolycount()
        ratio = tgt_polycount / initial_polycount

        # The 1000 polys and 1.1 are to avoid the resample being skipped
        # by 3dcoat
        UIDialogUtils.execute_resample_dialog(
            tgt_polycount + 1000, ratio * 1.1)

        print(" Resampling: Initial polycount: %s Target polycount: %s Ratio: %s" %
              (initial_polycount, tgt_polycount, ratio))
