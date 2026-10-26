import bpy
import math
import os

MODELS_DIR = r"D:\tecplore\assets\models"
os.makedirs(MODELS_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# -------------------------------------------------------------
# 1. BUILD FOREST FIRE (Campfire Hazard)
# -------------------------------------------------------------
def build_forest_fire():
    reset_scene()

    # Materials
    mat_stone = bpy.data.materials.new(name="StoneMat")
    bsdf_stone = mat_stone.node_tree.nodes.get("Principled BSDF")
    if bsdf_stone:
        bsdf_stone.inputs['Base Color'].default_value = (0.2, 0.22, 0.21, 1.0)
        bsdf_stone.inputs['Roughness'].default_value = 0.9

    mat_char = bpy.data.materials.new(name="CharredWoodMat")
    bsdf_char = mat_char.node_tree.nodes.get("Principled BSDF")
    if bsdf_char:
        bsdf_char.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf_char.inputs['Roughness'].default_value = 0.95

    mat_ember = bpy.data.materials.new(name="EmberMat")
    bsdf_ember = mat_ember.node_tree.nodes.get("Principled BSDF")
    if bsdf_ember:
        bsdf_ember.inputs['Base Color'].default_value = (1.0, 0.25, 0.02, 1.0)
        if 'Emission Color' in bsdf_ember.inputs:
            bsdf_ember.inputs['Emission Color'].default_value = (1.0, 0.28, 0.02, 1.0)
            bsdf_ember.inputs['Emission Strength'].default_value = 2.5

    # Stone Ring
    stones = []
    num_stones = 12
    for i in range(num_stones):
        angle = (i / num_stones) * math.pi * 2
        r = 1.1 + (math.sin(i * 3) * 0.1)
        sx = math.cos(angle) * r
        sy = math.sin(angle) * r
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.22, location=(sx, sy, 0.15))
        st = bpy.context.active_object
        st.scale = (1.2, 0.9, 0.8)
        st.data.materials.append(mat_stone)
        stones.append(st)

    # Ember Bed
    bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.15, vertices=16, location=(0, 0, 0.08))
    ember = bpy.context.active_object
    ember.data.materials.append(mat_ember)

    # Charred Logs
    logs = []
    for i in range(5):
        angle = (i / 5) * math.pi
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.6, vertices=12, location=(0, 0, 0.18 + i * 0.04))
        lg = bpy.context.active_object
        lg.rotation_euler = (math.radians(85), 0, angle + 0.2)
        lg.data.materials.append(mat_char)
        logs.append(lg)

    # Select all and join
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = ember
    bpy.ops.object.join()
    ember.name = "ForestFireModel"

    # Export
    out = os.path.join(MODELS_DIR, "forest_fire.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Exported forest_fire.glb")

# -------------------------------------------------------------
# 2. BUILD ILLEGAL LOGGING (Hardwood Stump & Woodcutter Axe)
# -------------------------------------------------------------
def build_illegal_logging():
    reset_scene()

    # Materials
    mat_bark = bpy.data.materials.new(name="BarkMat")
    bsdf_bark = mat_bark.node_tree.nodes.get("Principled BSDF")
    if bsdf_bark:
        bsdf_bark.inputs['Base Color'].default_value = (0.28, 0.18, 0.11, 1.0)
        bsdf_bark.inputs['Roughness'].default_value = 0.92

    mat_heartwood = bpy.data.materials.new(name="HeartwoodMat")
    bsdf_heart = mat_heartwood.node_tree.nodes.get("Principled BSDF")
    if bsdf_heart:
        bsdf_heart.inputs['Base Color'].default_value = (0.75, 0.58, 0.38, 1.0)
        bsdf_heart.inputs['Roughness'].default_value = 0.85

    mat_steel = bpy.data.materials.new(name="SteelMat")
    bsdf_steel = mat_steel.node_tree.nodes.get("Principled BSDF")
    if bsdf_steel:
        bsdf_steel.inputs['Base Color'].default_value = (0.8, 0.82, 0.85, 1.0)
        bsdf_steel.inputs['Metallic'].default_value = 0.95
        bsdf_steel.inputs['Roughness'].default_value = 0.2

    mat_handle = bpy.data.materials.new(name="AxeHandleMat")
    bsdf_h = mat_handle.node_tree.nodes.get("Principled BSDF")
    if bsdf_h:
        bsdf_h.inputs['Base Color'].default_value = (0.55, 0.32, 0.14, 1.0)
        bsdf_h.inputs['Roughness'].default_value = 0.65

    # 1. Main Tree Stump
    bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=1.3, vertices=24, location=(0, 0, 0.65))
    stump = bpy.context.active_object
    stump.data.materials.append(mat_bark)

    # Cut top face disc
    bpy.ops.mesh.primitive_circle_add(radius=1.08, fill_type='NGON', location=(0, 0, 1.305))
    top_disc = bpy.context.active_object
    top_disc.data.materials.append(mat_heartwood)

    # 2. Felled Fallen Log
    bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=6.5, vertices=20, location=(3.8, 0.8, 0.55))
    log_mesh = bpy.context.active_object
    log_mesh.rotation_euler = (0, math.radians(90), math.radians(18))
    log_mesh.data.materials.append(mat_bark)

    # 3. Woodcutter Axe (Embedded into stump)
    # Handle
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=1.2, vertices=12, location=(0.3, 0.1, 1.65))
    handle = bpy.context.active_object
    handle.rotation_euler = (math.radians(-25), 0, math.radians(15))
    handle.data.materials.append(mat_handle)

    # Blade
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.18, 0.05, 1.32))
    blade = bpy.context.active_object
    blade.scale = (0.28, 0.06, 0.22)
    blade.rotation_euler = (math.radians(-25), 0, math.radians(15))
    blade.data.materials.append(mat_steel)

    # Join All
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = stump
    bpy.ops.object.join()
    stump.name = "IllegalLoggingModel"

    # Export
    out = os.path.join(MODELS_DIR, "illegal_logging.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Exported illegal_logging.glb")

# -------------------------------------------------------------
# 3. BUILD POACHING WIRE SNARE
# -------------------------------------------------------------
def build_wire_snare():
    reset_scene()

    mat_sapling = bpy.data.materials.new(name="SaplingMat")
    bsdf_sap = mat_sapling.node_tree.nodes.get("Principled BSDF")
    if bsdf_sap:
        bsdf_sap.inputs['Base Color'].default_value = (0.35, 0.22, 0.14, 1.0)
        bsdf_sap.inputs['Roughness'].default_value = 0.85

    mat_cable = bpy.data.materials.new(name="SteelCableMat")
    bsdf_cab = mat_cable.node_tree.nodes.get("Principled BSDF")
    if bsdf_cab:
        bsdf_cab.inputs['Base Color'].default_value = (0.85, 0.88, 0.9, 1.0)
        bsdf_cab.inputs['Metallic'].default_value = 0.98
        bsdf_cab.inputs['Roughness'].default_value = 0.15

    # Bent Anchor Sapling
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.2, vertices=12, location=(-0.6, 0, 1.3))
    sapling = bpy.context.active_object
    sapling.rotation_euler = (0, math.radians(-38), 0)
    sapling.data.materials.append(mat_sapling)

    # Steel Wire Loop (Torus)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.55, minor_radius=0.02,
        major_segments=32, minor_segments=8,
        location=(0.8, 0, 0.22)
    )
    wire = bpy.context.active_object
    wire.rotation_euler = (math.radians(90), 0, 0)
    wire.data.materials.append(mat_cable)

    # Trigger anchor peg in ground
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.7, vertices=8, location=(0.8, 0, 0.35))
    peg = bpy.context.active_object
    peg.data.materials.append(mat_sapling)

    # Join
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = wire
    bpy.ops.object.join()
    wire.name = "WireSnareModel"

    # Export
    out = os.path.join(MODELS_DIR, "wire_snare.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Exported wire_snare.glb")

# -------------------------------------------------------------
# 4. BUILD PLASTIC TRASH DUMP
# -------------------------------------------------------------
def build_plastic_trash():
    reset_scene()

    mat_plastic = bpy.data.materials.new(name="PlasticClearMat")
    bsdf_p = mat_plastic.node_tree.nodes.get("Principled BSDF")
    if bsdf_p:
        bsdf_p.inputs['Base Color'].default_value = (0.45, 0.75, 0.95, 1.0)
        bsdf_p.inputs['Roughness'].default_value = 0.15
        if 'Transmission Weight' in bsdf_p.inputs:
            bsdf_p.inputs['Transmission Weight'].default_value = 0.85
        elif 'Transmission' in bsdf_p.inputs:
            bsdf_p.inputs['Transmission'].default_value = 0.85

    mat_can = bpy.data.materials.new(name="SodaCanMat")
    bsdf_can = mat_can.node_tree.nodes.get("Principled BSDF")
    if bsdf_can:
        bsdf_can.inputs['Base Color'].default_value = (0.9, 0.15, 0.15, 1.0)
        bsdf_can.inputs['Metallic'].default_value = 0.9
        bsdf_can.inputs['Roughness'].default_value = 0.25

    # 1. Discarded Bottles
    items = []
    for b in range(8):
        bx = (math.sin(b * 1.5) * 0.7) + (b * 0.1)
        by = (math.cos(b * 1.8) * 0.6)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.48, vertices=12, location=(bx, by, 0.1))
        bot = bpy.context.active_object
        bot.rotation_euler = (math.radians(85), math.radians(b * 35), math.radians(b * 50))
        bot.data.materials.append(mat_plastic)
        items.append(bot)

    # 2. Crushed Aluminum Soda Cans
    for c in range(3):
        cx = (c * 0.35) - 0.4
        cy = (c * 0.2) + 0.3
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.35, vertices=12, location=(cx, cy, 0.08))
        can = bpy.context.active_object
        can.scale = (1.2, 0.6, 0.8) # crushed
        can.rotation_euler = (math.radians(90), 0, math.radians(c * 60))
        can.data.materials.append(mat_can)
        items.append(can)

    # Join
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = items[0]
    bpy.ops.object.join()
    items[0].name = "PlasticTrashModel"

    # Export
    out = os.path.join(MODELS_DIR, "plastic_trash.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Exported plastic_trash.glb")

# Run all builders
build_forest_fire()
build_illegal_logging()
build_wire_snare()
build_plastic_trash()
print("All 3D Threats successfully built!")
