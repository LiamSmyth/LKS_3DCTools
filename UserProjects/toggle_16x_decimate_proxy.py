# This is just a wrapper to always cache to 16x decimation
import coat


coat.ui.cmd("$Decimate16X")
coat.ui.cmd("$ToggleCachingVolume")

# Show summary message to user
coat.ui.showInfoMessage("16x decimation proxy toggled", 3000)
