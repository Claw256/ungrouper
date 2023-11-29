# Ungrouper
A fully functional Blender 3 add-on that ungroups nested Node Groups into a single flat node tree hierarchy.

# What does it do
TLDR: It ungroups node groups on every material in your scene.

Longer explanation: It goes through every object in your Blender scene, cross references it for linked materials, then goes through each node group & nested node groups in the material, then removes the reroute junction nodes (As they cause way too much trouble for Python scripting), adds dummy nodes to raw literal values of node group inputs if there are any, as without the dummy nodes the node group's raw literal values are lost in the ungrouping process (Could be a Blender bug, not sure of the cause of this behaviour).

The order of execution of the addon code goes: 

Remove reroute nodes --> Add dummy nodes --> Ungroup the node groups (Starting from the inner most group, BFS algorithm)

# How to use
TLDR: Download this repo, install & activate the Addon, then press the "Ungroup" button in the 3D Viewport N-Panel

Steps:

1. Download this repo as a zip, or just download the single `__init__.py` in this repo.
2. Install & Activate the Blender Addon
3. ***VERY IMPORTANT:*** Switch to the "Shading" workspace tab on the very top of Blender, then open the N-Panel to run the addon from that 3D Viewport window only. This is essential as the addon searches for the Node Editor window before executing the logic, and it will fail if you don't execute the addon in the right workspace (With the context being the  Shader Node Editor).
4. Press the "Ungroup All Objects" on the "Ungrouper" tab in the N-Panel in the 3D Viewport
5. Wait for your nodes to all ungroup. In a very large heavy Hanamura map with around over 380 materials and 11,000 objects, it took ~25 minutes with my Ryzen 5 5600X CPU. Again, with processing time is dependent on how big your scene is, and how complex your materials are. YMMV.
6. ???
7. Profit.

# Note
While the script will attempt to ungroup all node groups, it can get stuck on 1 or 2 node groups on a material, such as the complex dust material found on the Hanamura road dust objects. You could just run the script again and it should ungroup those node groups. I'm working on debugging and fixing this minor issue.

# Contributing
Any assistance, issue reporting, pull requests, are all welcome :)
