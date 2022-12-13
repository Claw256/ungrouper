# Ungrouper
A Python script to batch ungroup material nodes in Blender

# Note
This script currently only works on a single material slot basis after each execution, until I or someone else figures out how to have it iterate through all the material slots.
If you have multiple objects selected the script should auto select your next object, and you should be able to press the Run Script button until the Node Groups are ungrouped.
The script is a bit hacky, so you may to run it a few times on a material slot in order for some groups to be fully ungrouped

# Usage
TLDR: Run the Script on your object until all node groups are ungrouped.

1. Open your Blender Scene, to to the Scripting Tab on the top.
2. Open this Script in the script file browser
3. Select the model in the outliner or 3D viewport you wish to Ungroup the Node Groups from.
4. In the same Scripting Tab your currently in, open a new Shader Editor window area by locating a window on your screen, and pressing the top left icon to change the current area type. This step is important as this script does an area context override for the ungrouping.
5. Make sure your object is selected, and press the Run Script button until all node groups are ungrouped.
6. ???
7. Profit.

# Contributing
This script is quite messy so any help with cleaning it up and optimizing it further, and adding features is greatly appreciated.
