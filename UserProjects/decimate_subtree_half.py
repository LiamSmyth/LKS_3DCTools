
import coat
import math


def decimate_half(el: coat.SceneElement):
    # Check if there was a Layer 1 or Layer1 before decimate.
    # If there was not, make sure to delete it after decimating

    layers_that_exist = []

    # Check for existence of layers 0-9, cache any that are found
    for i in range(0, 10):
        strings_to_check = [f"Layer {i}", f"Layer{i}"]
        for string in strings_to_check:
            if coat.Scene.getLayer(string, False) != -1:
                layers_that_exist.append(string)

    print(f"Found layers before decimate: {layers_that_exist}")

    if not el.isSculptObject():
        print("Not a sculpt object")
        return False

    vol: coat.Volume = el.Volume()
    if not vol.isSurface():
        vol.toSurface()

    def decimate_ui():
        # Set the reduction percent to 50 and press OK
        coat.ui.setSliderValue("$DecimationParams::ReductionPercent", 50)
        coat.ui.cmd("$DialogButton#1")

    coat.ui.cmd("$Decimate", decimate_ui)

    coat.Scene.removeEmptyLayers()

    # Remove any layers that were not present before decimate
    for i in range(0, 10):
        strings_to_check = [f"Layer {i}", f"Layer{i}"]
        for string in strings_to_check:
            if coat.Scene.getLayer(string, False) != -1:
                print(f"Found layer {string}")
                if string not in layers_that_exist:
                    print(f"Removing {string}")
                    coat.Scene.removeLayer(string)

    return False  # To continue iteration


active_element: coat.SceneElement = coat.Scene.current()

decimate_half(active_element)
active_element.iterateSubtree(decimate_half)

coat.SceneElement.selectOne(active_element)
coat.Scene.removeEmptyLayers()
coat.Scene.setActiveLayer(0)
