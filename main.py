import bpy


def create_node_group_dummy_nodes(node, node_tree):

    col_input_sockets = [socket for socket in node.inputs if socket.bl_idname == "NodeSocketColor" and len(socket.links) == 0]
    float_input_sockets = [socket for socket in node.inputs if
                           (socket.bl_idname == "NodeSocketFloatFactor" or socket.bl_idname == "NodeSocketFloat") and len(
                               socket.links) == 0]
    for socket in col_input_sockets:
        val = socket.default_value
        rgb = node_tree.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = val
        node_tree.links.new(rgb.outputs[0], socket)
        print(f"Set RGB value {val} for input {socket.name} on {node.name}")

    for socket in float_input_sockets:
        val = socket.default_value
        vnode = node_tree.nodes.new("ShaderNodeValue")
        vnode.outputs[0].default_value = val
        node_tree.links.new(vnode.outputs[0], socket)
        print(f"Set float value {val} for input {socket.name} on {node.name}")


def deselect_all_nodes(node):
    if hasattr(node, "node_tree"):
        for node in node.node_tree.nodes:
            node.select = False
            yield from deselect_all_nodes(node)
    else:
        node.select = False
        yield None


def groups_in_tree(parent_node_tree):
    for potential_group_node in parent_node_tree.nodes:
        if potential_group_node.bl_idname == "ShaderNodeGroup":
            potential_group_node.select = False
            yield from groups_in_tree(potential_group_node.node_tree)
    for potential_group_node in parent_node_tree.nodes:
        if potential_group_node.bl_idname == "ShaderNodeGroup":
            potential_group_node.select = False
            yield potential_group_node, parent_node_tree


def remove_reroutes(group_node):
    reroute_nodes = [n for n in group_node.node_tree.nodes if n.bl_idname == "NodeReroute"]

    for node in reroute_nodes:
        if len(node.inputs[0].links) == 0:
            group_node.node_tree.nodes.remove(node)
            continue

        origin_socket = node.inputs[0].links[0].from_socket
        output_links = [l for l in node.outputs[0].links]

        for l in output_links:
            dest_socket = l.to_socket
            group_node.node_tree.links.new(origin_socket, dest_socket)

    [group_node.node_tree.nodes.remove(n) for n in group_node.node_tree.nodes if n.bl_idname == "NodeReroute"]


def fix_node_groups(child_node, parent_node_tree):
    print(f"Group node name: {child_node.name} ({child_node.label})")
    create_node_group_dummy_nodes(child_node, parent_node_tree)
    remove_reroutes(child_node)


def ungroup(node, parent_node_tree):
    old_type = bpy.context.area.type
    area_type = 'NODE_EDITOR'
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]
    with bpy.context.temp_override(
            window=bpy.context.window,
            area=areas[0],
            regions=[region for region in areas[0].regions if region.type == 'WINDOW'][0],
            screen=bpy.context.window.screen
    ):
        parent_node_tree.nodes.active = node
        bpy.ops.node.group_ungroup()
    bpy.context.area.type = old_type


def main():
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        print(f"\nNow running on Object: {obj.name}")
        for slot in obj.material_slots:
            mat = slot.material
            print(f"Material Slot: {slot}")
            deselect_all_nodes(mat)
            print(f"\nNow running on Material: {mat}")
            for node, parent_node_tree in groups_in_tree(mat.node_tree):
                print(f"Current Tree {node}: {node.name} ({node.bl_label})")
                fix_node_groups(node, parent_node_tree)
                ungroup(node, parent_node_tree)


main()
