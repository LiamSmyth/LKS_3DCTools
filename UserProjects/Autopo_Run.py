"""
Run Autopo

Runs autopo on current sculpt object using cached settings.

Room: Sculpt
Action: Execute autopo with density/options from settings cache
"""
from _utils.autopo_utils import run_autopo_with_settings
import importlib
from _utils import autopo_utils
importlib.reload(autopo_utils)


# Execute
run_autopo_with_settings()
