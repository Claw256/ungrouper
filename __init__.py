import bpy
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from bpy.types import Context, Event, Material, Mesh, Node, NodeSocket, NodeTree, Object, Timer, Operator, Panel

bl_info = {
    "name": "Ungrouper",
    "description": "Ungroups shader node groups in materials for selected objects.",
    "author": "Claw256",
    "version": (2, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Ungrouper",
    "category": "3D View"
}

class RerouteNodeProcessor:
    def process_reroute_nodes(self, node_tree: NodeTree) -> None:
        print("Processing reroute nodes...")
        for node in node_tree.nodes:
            if node.bl_idname == 'NodeReroute':
                self.bypass_reroute_node(node, node_tree)
            elif node.bl_idname == 'ShaderNodeGroup':
                self.process_reroute_nodes(node.node_tree)  # Recursively process nested node groups

    def bypass_reroute_node(self, node: Node, node_tree: NodeTree) -> None:
        for input_socket in node.inputs:
            for output_socket in node.outputs:
                if input_socket.is_linked and output_socket.is_linked:
                    for input_link in input_socket.links:
                        for output_link in output_socket.links:
                            node_tree.links.new(input_link.from_socket, output_link.to_socket)
        node_tree.nodes.remove(node)

class DummyNodeCreator:
    def create_dummy_nodes(self, node_tree: NodeTree) -> None:
        print("Creating dummy nodes...")
        for node in node_tree.nodes:
            if node.bl_idname == 'ShaderNodeGroup':
                self.create_dummy_nodes(node.node_tree)  # Recursively process nested node groups
                for input_socket in node.inputs:
                    if not input_socket.is_linked:
                        dummy_node = self.create_dummy_node_for_socket(node_tree, input_socket)
                        if dummy_node:
                            node_tree.links.new(dummy_node.outputs[0], input_socket)

    def create_dummy_node_for_socket(self, node_tree: NodeTree, socket: NodeSocket) -> Optional[Node]:
        socket_type = socket.type
        if socket_type == 'VALUE':
            return self.create_value_node(node_tree, socket)
        elif socket_type == 'VECTOR':
            return self.create_vector_node(node_tree, socket)
        elif socket_type == 'RGBA':
            return self.create_rgba_node(node_tree, socket)
        # Add more cases for other socket types as needed
        return None

    def create_value_node(self, node_tree: NodeTree, socket: NodeSocket) -> Node:
        value_node = node_tree.nodes.new(type='ShaderNodeValue')
        value_node.outputs[0].default_value = socket.default_value if hasattr(socket, 'default_value') else 0.0
        return value_node

    def create_vector_node(self, node_tree: NodeTree, socket: NodeSocket) -> Node:
        vector_node = node_tree.nodes.new(type='ShaderNodeVectorMath')
        vector_node.operation = 'ADD'
        vector_node.inputs[1].default_value = socket.default_value if hasattr(socket, 'default_value') else (0.0, 0.0, 0.0)
        return vector_node

    def create_rgba_node(self, node_tree: NodeTree, socket: NodeSocket) -> Node:
        rgba_node = node_tree.nodes.new(type='ShaderNodeRGB')
        rgba_node.outputs[0].default_value = socket.default_value if hasattr(socket, 'default_value') else (1.0, 1.0, 1.0, 1.0)
        return rgba_node

class NodeGroupUngrouper:
    def ungroup_node_groups(self, node_tree: NodeTree, context: Context) -> None:
        for node in node_tree.nodes:
            if node.bl_idname == 'ShaderNodeGroup':
                self.ungroup_node(node, node_tree, context)

    def ungroup_node(self, node: Node, node_tree: NodeTree, context: Context) -> None:
        node_tree.nodes.active = node
        node.select = True

        win = context.window
        scr = win.screen
        areas = [area for area in scr.areas if area.type == 'NODE_EDITOR']
        if areas:
            areas[0].spaces.active.node_tree = node_tree
            regions = [region for region in areas[0].regions if region.type == 'WINDOW']
            if regions:
                try:
                    with context.temp_override(window=win, area=areas[0], region=regions[0], screen=scr):
                        bpy.ops.node.group_ungroup('INVOKE_DEFAULT')
                except RuntimeError as e:
                    logging.error(f"Failed to ungroup node: {e}")

class UVMapFixer:
    def fix_uv_maps_in_scene(self) -> None:
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.uv_layers:
                first_uv_map_name = obj.data.uv_layers[0].name
                for material in obj.data.materials:
                    if material and material.use_nodes:
                        self.fix_uv_maps(material.node_tree, obj, first_uv_map_name)

    def fix_uv_maps(self, node_tree: NodeTree, obj: Object, first_uv_map_name: str) -> None:
        for node in node_tree.nodes:
            if node.type == 'UVMAP':
                if not node.uv_map or node.uv_map not in obj.data.uv_layers:
                    node.uv_map = first_uv_map_name

class SceneObjectProcessor:
    def __init__(self, context: Context):
        self.context = context
        self.reroute_processor = RerouteNodeProcessor()
        self.dummy_creator = DummyNodeCreator()
        self.ungrouper = NodeGroupUngrouper()

    def process_all_objects(self, obj: Object) -> None:
        if obj.type == 'MESH' and obj.material_slots:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    self.process_node_tree(slot.material.node_tree)

    def process_node_tree(self, node_tree: NodeTree) -> None:
        self.reroute_processor.process_reroute_nodes(node_tree)
        self.dummy_creator.create_dummy_nodes(node_tree)
        self.ungrouper.ungroup_node_groups(node_tree, self.context)

class OBJECT_OT_UngroupSceneModal(Operator):
    bl_idname = "object.ungroup_scene_modal"
    bl_label = "Ungroup All Objects"
    bl_options = {'REGISTER', 'UNDO'}

    _timer: Optional[Timer] = None
    object_index: int = 0

    def __init__(self):
        self.processed_materials: Dict[str, int] = {}
        self.total_materials: int = 0
        self.processed_count: int = 0

    def modal(self, context: Context, event: Event) -> Set[str]:
        if event.type == 'TIMER':
            print("Modal operator running...")
            objects = bpy.data.objects
            progress = self.processed_count / self.total_materials * 100 if self.total_materials > 0 else 0
            progress_bar = "[" + "=" * int(progress // 5) + " " * (20 - int(progress // 5)) + "]"
            self.report({'INFO'}, f"Processing materials: {progress_bar} {progress:.2f}% done")
            if self.object_index >= len(objects):
                print("Finished processing all objects.")
                self.finish(context)
                return {'FINISHED'}

            obj = objects[self.object_index]
            if obj.type == 'MESH' and obj.material_slots:
                for slot in obj.material_slots:
                    if slot.material and slot.material.use_nodes:
                        mat_name = slot.material.name
                        # Check if the material has been processed on a previous object
                        if mat_name in self.processed_materials and \
                                self.processed_materials[mat_name] < self.object_index:
                            continue
                        self.processed_materials[mat_name] = self.object_index

                        uv_fixer = UVMapFixer()
                        uv_fixer.fix_uv_maps_in_scene()

                        object_processor = SceneObjectProcessor(context)
                        object_processor.process_all_objects(obj)
                        self.processed_count += 1
            self.object_index += 1
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def execute(self, context: Context) -> Set[str]:
        self.object_index = 0
        self.total_materials = len({mat_slot.material.name for obj in bpy.data.objects if obj.type == 'MESH' for mat_slot in obj.material_slots if mat_slot.material})
        self.processed_count = 0
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def finish(self, context: Context) -> None:
        print("Finishing modal operator.")
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

class OBJECT_PT_UngroupSceneAddonPanel(Panel):
    bl_label = "Scene Ungrouper"
    bl_idname = "OBJECT_PT_ungroup_scene_addon"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ungrouper"

    def draw(self, context: Context) -> None:
        self.layout.operator("object.ungroup_scene_modal")

def register() -> None:
    bpy.utils.register_class(OBJECT_OT_UngroupSceneModal)
    bpy.utils.register_class(OBJECT_PT_UngroupSceneAddonPanel)

def unregister() -> None:
    bpy.utils.unregister_class(OBJECT_OT_UngroupSceneModal)
    bpy.utils.unregister_class(OBJECT_PT_UngroupSceneAddonPanel)

if __name__ == "__main__":
    register()
