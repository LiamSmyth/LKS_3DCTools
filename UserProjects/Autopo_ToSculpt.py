"""
Autopo To Sculpt

Runs autopo, imports result to sculpt room, and hides original object.

Room: Sculpt
Action: Autopo -> import to sculpt -> hide original
"""
from _utils.autopo_utils import autopo_to_sculpt
import importlib
from _utils import autopo_utils
importlib.reload(autopo_utils)


# Execute
autopo_to_sculpt()
