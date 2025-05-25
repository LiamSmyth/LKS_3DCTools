import coat
from _utils.object_utils import ObjectUtils


def main():
    el = coat.Scene.current()
    # Scale down by 100 means using a scale factor of 0.01.
    ObjectUtils.scale_selected_element(el, 0.01)

    # Show summary message to user
    coat.ui.showInfoMessage("Object scaled down 100x", 3000)


main()
