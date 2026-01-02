# Iterate over the sculpt tree, show the basic stats - square, volume
import coat
import math
# This class represents the one line in the info box, the square and volume of one sculpt object


class OneLine:
    def __init__(self):
        self.name = ""
        self.Square = 0
        self.Volume = 0

    def __init__(self, el):
        self.name = el.name()
        self.Square = el.Volume().getSquare()
        self.Volume = el.Volume().getVolume()

    def ui(self):
        return [
            "[3]",
            "name,'!name'",  # "!identifier" means that it is readonly and it's name does not appear in UI
            "Square,'!Square'",
            "Volume,'!Volume'"
        ]

# This is the class to represent the information about all volumes


class Stats:
    def __init__(self):
        self.lines = []

    def Calculate(self):
        # get the sculpt root
        r = coat.Scene.sculptRoot()
        # iterate through all sculpt objects

        def walker(el):
            # adding the element to ClassArray to represent in UI
            line = OneLine(el)
            if el.isSculptObject():
                self.lines.append(line)
            print(line.name, line.Square, line.Volume)
            return False

        r.iterateVisibleSubtree(walker)
        print(self.lines)

    # This is the list of volumes, ClassArray is the array of pointers to BaseClass-derived items
    def ui(self):
        return [
            # making the header, 3 columns
            "[3]",
            # "*name" means it is left-aligned text
            "#*Name",
            "#*Square",
            "#*Volume",
            "---",
            "lines",
            "---"
        ]

# stats = Stats()
# calculate the stats
# stats.Calculate()
# coat.dialog().ok().params(stats).show()

# Using above code as reference for our custom subtree reduce code

# First we need to prepare the action that occurs when the subtree is iterated


active_element: coat.SceneElement = coat.Scene.current()

# reduce_element_half(active_element)

print("Start Reduce: ", active_element.name())


def reduce_element_half(el: coat.SceneElement):
    el.selectOne()
    if el.isSculptObject():
        vol: coat.Volume = el.Volume()
        if not vol.isSurface():
            vol.toSurface()

        ratio = 0.5
        cur_polycount: int = vol.getPolycount()
        tgt_poylcount: int = math.floor(cur_polycount * ratio)

        def ui_command():
            coat.ui.setEditBoxValue(
                "$ResampleParams::RequiredPolycount", tgt_poylcount)
            coat.ui.setSliderValue("$ResampleParams::ResamplingScale", ratio)
            coat.ui.cmd("$DialogButton#1")
            # coat.ui.apply()

        coat.ui.cmd("$Resample", ui_command)

        print("Decimated $s from $s polys to $s polys",
              [el.name(), cur_polycount, tgt_poylcount])

        return False


reduce_element_half(active_element)

active_element.iterateSubtree(reduce_element_half)

active_element.selectOne()
"""
// cmd - based script:
cmd("$ResampleParams::RequiredPolycount");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$ResampleParams::RequiredPolycount");
// class - based interface, need to declare the variable Vox vox;
vox.resample()

// cmd - based script:
cmd("$ResampleParams::ResamplingScale");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$ResampleParams::ResamplingScale");
// class - based interface, need to declare the variable Vox vox;
vox.resample()
// cmd - based script:
cmd("$ResampleParams::ResamplingScale");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$ResampleParams::ResamplingScale");
// class - based interface, need to declare the variable Vox vox;
vox.resample()

// cmd - based script:
cmd("$DialogButton#1");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$DialogButton#1");


coat.ui.setSliderValue()

	// cmd - based script:
cmd("$Decimate");
// UI - based script, need to define the variable somewhere before: UI ui;
ui("$Decimate");

		coat::Volume vol = el.Volume();
vol.toSurface();
int cur_polycount = vol.getPolycount();
//vol.toVoxels();
el.selectOne();
coat::ui::cmd("$Resample",
	[cur_polycount]
	{
		//coat::ui::setEditBoxValue("$ResampleParams::RequiredPolycount", tgt_polycount);
		float scale = 0.5f;
		coat::ui::setSliderValue("$ResampleParams::ResamplingScale", scale);

		coat::ui::cmd("$DialogButton#1");
		//coat::ui::apply();

	}
"""
