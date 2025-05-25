import coat
from _utils.object_utils import ObjectUtils


def main():
    el = coat.Scene.current()
    # Scale up by 100 means using a scale factor of 100.0
    ObjectUtils.scale_selected_element(el, 100.0)

    # Show summary message to user
    coat.ui.showInfoMessage("Object scaled up 100x", 3000)


main()
