import bpy


def create_node_group_dummy_nodes(node, node_tree):
    nodes = node_tree.nodes

    col_input_sockets = [s for s in node.inputs if s.bl_idname == "NodeSocketColor" and len(s.links) == 0]
    float_input_sockets = [s for s in node.inputs if
                           (s.bl_idname == "NodeSocketFloatFactor" or s.bl_idname == "NodeSocketFloat") and len(
                               s.links) == 0]
    vector_input_sockets = [s for s in node.inputs if s.bl_idname == "NodeSocketVector" and len(s.links) == 0]

    for s in col_input_sockets:
        val = s.default_value
        rgb = node_tree.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = val
        node_tree.links.new(rgb.outputs[0], s)

    for s in float_input_sockets:
        val = s.default_value
        vnode = node_tree.nodes.new("ShaderNodeValue")
        vnode.outputs[0].default_value = val
        node_tree.links.new(vnode.outputs[0], s)

    return True


def groups_in_tree(node):
    if node.bl_idname == "ShaderNodeGroup":
        print(f"Node: {node}")
        yield node
    for the_other_node in node.node_tree.nodes:
        the_other_node.select = False
        if the_other_node.bl_idname == "ShaderNodeGroup":
            print(f"Node: {the_other_node}")
            yield the_other_node
            yield from groups_in_tree(the_other_node)

def remove_reroutes(nodes, node_tree):
    reroute_nodes = [n for n in nodes if n.bl_idname == "NodeReroute"]

    for node in reroute_nodes:
        # Nothing plugged in
        if len(node.inputs[0].links) == 0:
            nodes.remove(node)
            continue

        # Otherwise...
        origin_socket = node.inputs[0].links[0].from_socket  # Can only be one input
        output_links = [l for l in node.outputs[0].links]

        for l in output_links:
            dest_socket = l.to_socket
            node_tree.links.new(origin_socket, dest_socket)

    # Remove all reroute nodes, as now all bypassed
    [nodes.remove(n) for n in nodes if n.bl_idname == "NodeReroute"]


def has_node_groups(mat):
    node_tree = mat.node_tree
    nodes = node_tree.nodes

    result = False
    node_group_nodes = [n for n in nodes if n.bl_idname == "ShaderNodeGroup"]

    for n in node_group_nodes:
        ss = [s for s in n.outputs if s.bl_idname == "NodeSocketShader"
              and len(s.links) > 0]
        if len(ss) > 0: result = True

    return result


def ungroup_nodes(node_tree, context):
    print(f"Ungrouping nodes on Object: {bpy.context.view_layer.objects.active}")
    for node in node_tree.nodes:
        node.select = False
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeGroup":
            # Get all output sockets that are type shader and linked to something
            ss = [s for s in node.outputs if s.bl_idname == "NodeSocketShader" and len(s.links) > 0]
            if len(ss) > 0:
                # We care about this node group node
                create_node_group_dummy_nodes(node, node_tree)
                node.select = True
                node_tree.nodes.active = node
    area_type = 'NODE_EDITOR'
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    with bpy.context.temp_override(
            window=bpy.context.window,
            area=areas[0],
            regions=[region for region in areas[0].regions if region.type == 'WINDOW'][0],
            screen=bpy.context.window.screen
    ):
        bpy.ops.node.group_ungroup()
        # break  # Just one per cycle or Blender gets grumpy


# for obj in bpy.context.selected_objects:
#     bpy.context.view_layer.objects.active = obj
#     print(f"Now running on Object: {obj}")
#     for slot in obj.material_slots:
#         print(f"Now running on Material Slot: {slot}")
#         node_tree = slot.material.node_tree
#         nodes = node_tree.nodes
#         ungroup_nodes(node_tree, bpy.context)
#         remove_reroutes(nodes, node_tree)

for obj in bpy.context.selected_objects:
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    print(f"Now running on Object: {obj.name}")
    if hasattr(obj.data, 'materials'):
        for mat in obj.data.materials:
            print(f"Now running on Material: {mat}")
            old_type = bpy.context.area.type
            for the_node in mat.node_tree.nodes:
                the_node.select = False
                if the_node.bl_idname == "ShaderNodeGroup":
                    for the_group_node in groups_in_tree(the_node):
                        print(f"Group node name: {the_group_node}")
                        the_group_node.select = True
                        mat.node_tree.nodes.active = the_group_node
                        bpy.context.area.type = 'NODE_EDITOR'
                        bpy.ops.node.group_ungroup()
                        bpy.context.area.type = old_type
                        remove_reroutes(mat.node_tree.nodes, mat.node_tree)
                    mat.node_tree.nodes.active = the_node
# if mat.use_nodes:
#     for the_node_tree in groups_in_tree(mat.node_tree):
#         ungroup_nodes(the_node_tree)
# bpy.context.area.type = 'NODE_EDITOR'
# bpy.context.area.ui_type = 'ShaderNodeTree'
# nodes.select = True
# mat.node_tree.nodes.active = nodes
# bpy.ops.node.group_ungroup()
# bpy.context.area.type = initial_area_type
# bpy.context.area.ui_type = intial_ui_type
# print(f"Material {counter}, Node: {nodes.name}")

#            groups_in_tree.active = node
#            counter += 1
#            bpy.ops.node.group_ungroup('INVOKE_DEFAULT')
