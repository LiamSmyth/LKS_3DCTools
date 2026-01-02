"""
Autopo To Multiresolution

Runs autopo and imports result as multiresolution lowest level.

Room: Sculpt
Action: Autopo -> import as multiresolution
"""
from _utils.autopo_utils import autopo_to_multiresolution
import importlib
from _utils import autopo_utils
importlib.reload(autopo_utils)


# Execute
autopo_to_multiresolution()
