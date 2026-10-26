import bpy
import math

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Create Industrial Barrel (Chemical Waste Drum)
# Create cylinder base
bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.35, vertices=32, location=(0, 0, 0.675))
barrel = bpy.context.active_object
barrel.name = "ChemicalDrum"

# Add ribbed reinforcing rings
for z_offset in [0.35, 0.675, 1.0]:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.46, minor_radius=0.02,
        major_segments=32, minor_segments=12,
        location=(0, 0, z_offset)
    )
    ring = bpy.context.active_object
    # Join with barrel
    ring.select_set(True)
    barrel.select_set(True)
    bpy.context.view_layer.objects.active = barrel
    bpy.ops.object.join()

# Create Toxic Sludge Puddle at the base
bpy.ops.mesh.primitive_circle_add(radius=1.2, fill_type='NGON', location=(0.3, 0, 0.02))
puddle = bpy.context.active_object
puddle.name = "ToxicPuddle"

# Materials
# Barrel Material (Hazard Yellow Metal)
mat_drum = bpy.data.materials.new(name="HazardDrumMat")
mat_drum.use_nodes = True
nodes = mat_drum.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.9, 0.65, 0.05, 1.0) # Yellow
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.35
barrel.data.materials.append(mat_drum)

# Sludge Material (Luminescent Green)
mat_sludge = bpy.data.materials.new(name="ToxicSludgeMat")
mat_sludge.use_nodes = True
p_nodes = mat_sludge.node_tree.nodes
p_bsdf = p_nodes.get("Principled BSDF")
if p_bsdf:
    p_bsdf.inputs['Base Color'].default_value = (0.1, 0.85, 0.2, 1.0)
    p_bsdf.inputs['Roughness'].default_value = 0.1
    # Emission for glow
    if 'Emission Color' in p_bsdf.inputs:
        p_bsdf.inputs['Emission Color'].default_value = (0.1, 0.9, 0.2, 1.0)
        p_bsdf.inputs['Emission Strength'].default_value = 1.5
puddle.data.materials.append(mat_sludge)

# Tilt barrel as if tipped over leaking
barrel.rotation_euler = (0, math.radians(72), 0)
barrel.location = (0, 0, 0.25)

# Join into single object
barrel.select_set(True)
puddle.select_set(True)
bpy.context.view_layer.objects.active = barrel
bpy.ops.object.join()

# Export to GLB
output_path = r"D:\tecplore\assets\models\chemical_waste.glb"
bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')
print("Successfully exported chemical_waste.glb!")
