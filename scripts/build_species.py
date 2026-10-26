import bpy
import math
import os

MODELS_DIR = r"D:\tecplore\assets\models"
os.makedirs(MODELS_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_pbr_material(name, base_color, roughness=0.8, metallic=0.0, specular=0.5, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = roughness
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = metallic
        if 'Specular' in bsdf.inputs:
            bsdf.inputs['Specular'].default_value = specular
        elif 'Specular IOR Level' in bsdf.inputs:
            bsdf.inputs['Specular IOR Level'].default_value = specular
        if emission and 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat

# =============================================================
# 1. ROYAL BENGAL TIGER (Panthera tigris)
# =============================================================
def build_tiger():
    reset_scene()
    print("Building Royal Bengal Tiger...")

    # Materials
    mat_orange = create_pbr_material("TigerFurMat", (0.85, 0.42, 0.08, 1.0), roughness=0.75, specular=0.3)
    mat_white = create_pbr_material("TigerWhiteFurMat", (0.95, 0.93, 0.88, 1.0), roughness=0.8, specular=0.2)
    mat_stripe = create_pbr_material("TigerStripeMat", (0.07, 0.06, 0.05, 1.0), roughness=0.85, specular=0.1)
    mat_nose = create_pbr_material("TigerNoseMat", (0.35, 0.18, 0.18, 1.0), roughness=0.4, specular=0.6)
    mat_eye = create_pbr_material("TigerEyeMat", (0.95, 0.75, 0.05, 1.0), roughness=0.15, specular=0.9)
    mat_pupil = create_pbr_material("TigerPupilMat", (0.02, 0.02, 0.02, 1.0), roughness=0.1, specular=0.9)
    mat_claw = create_pbr_material("TigerClawMat", (0.2, 0.18, 0.16, 1.0), roughness=0.5, specular=0.4)

    parts = []

    # --- Torso / Chest (Muscular predatory feline) ---
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0, location=(0, 0, 1.45))
    torso = bpy.context.active_object
    torso.scale = (0.78, 1.65, 0.88)
    torso.data.materials.append(mat_orange)
    parts.append(torso)

    # Chest front swelling
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.72, location=(0, 0.9, 1.42))
    chest = bpy.context.active_object
    chest.scale = (0.82, 0.95, 0.95)
    chest.data.materials.append(mat_white)
    parts.append(chest)

    # Pelvic / Rear flank
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.68, location=(0, -0.95, 1.48))
    pelvis = bpy.context.active_object
    pelvis.scale = (0.75, 0.85, 0.85)
    pelvis.data.materials.append(mat_orange)
    parts.append(pelvis)

    # Underbelly white patch
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.6, location=(0, -0.1, 1.15))
    belly = bpy.context.active_object
    belly.scale = (0.65, 1.4, 0.45)
    belly.data.materials.append(mat_white)
    parts.append(belly)

    # --- Neck & Head ---
    # Neck
    bpy.ops.mesh.primitive_cylinder_add(radius=0.44, depth=0.9, vertices=16, location=(0, 1.5, 1.72))
    neck = bpy.context.active_object
    neck.rotation_euler = (math.radians(-32), 0, 0)
    neck.scale = (0.88, 1.0, 1.15)
    neck.data.materials.append(mat_orange)
    parts.append(neck)

    # White throat ruff
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.45, location=(0, 1.62, 1.55))
    ruff = bpy.context.active_object
    ruff.scale = (0.8, 0.7, 0.7)
    ruff.data.materials.append(mat_white)
    parts.append(ruff)

    # Skull
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=16, radius=0.52, location=(0, 1.95, 2.05))
    head = bpy.context.active_object
    head.scale = (0.95, 1.1, 0.9)
    head.data.materials.append(mat_orange)
    parts.append(head)

    # White cheeks
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.28, location=(side * 0.36, 1.9, 1.92))
        cheek = bpy.context.active_object
        cheek.scale = (0.6, 0.9, 0.6)
        cheek.data.materials.append(mat_white)
        parts.append(cheek)

    # Snout / Muzzle
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.34, location=(0, 2.32, 1.94))
    muzzle = bpy.context.active_object
    muzzle.scale = (0.75, 1.0, 0.65)
    muzzle.data.materials.append(mat_white)
    parts.append(muzzle)

    # Nose pad
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.1, vertices=10, location=(0, 2.58, 2.02))
    nose = bpy.context.active_object
    nose.rotation_euler = (math.radians(50), 0, 0)
    nose.scale = (1.2, 0.8, 0.8)
    nose.data.materials.append(mat_nose)
    parts.append(nose)

    # Lower Jaw / Chin
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.24, location=(0, 2.22, 1.76))
    jaw = bpy.context.active_object
    jaw.scale = (0.7, 0.9, 0.45)
    jaw.data.materials.append(mat_white)
    parts.append(jaw)

    # Eyes & Pupils
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.1, location=(side * 0.28, 2.22, 2.15))
        eye = bpy.context.active_object
        eye.scale = (0.9, 0.9, 0.9)
        eye.data.materials.append(mat_eye)
        parts.append(eye)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.06, vertices=8, location=(side * 0.3, 2.3, 2.15))
        pupil = bpy.context.active_object
        pupil.rotation_euler = (math.radians(90), 0, 0)
        pupil.data.materials.append(mat_pupil)
        parts.append(pupil)

        # White eye patch above eye
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.12, location=(side * 0.24, 2.15, 2.28))
        eyepatch = bpy.context.active_object
        eyepatch.scale = (0.7, 0.6, 0.3)
        eyepatch.data.materials.append(mat_white)
        parts.append(eyepatch)

    # Ears (Rounded feline ears with black backs and white spot)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.08, vertices=12, location=(side * 0.38, 1.75, 2.45))
        ear = bpy.context.active_object
        ear.rotation_euler = (math.radians(-25), math.radians(side * 28), 0)
        ear.scale = (1.0, 0.6, 1.1)
        ear.data.materials.append(mat_stripe)
        parts.append(ear)

        # Inner ear
        bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.04, vertices=10, location=(side * 0.38, 1.78, 2.45))
        inner_ear = bpy.context.active_object
        inner_ear.rotation_euler = (math.radians(-25), math.radians(side * 28), 0)
        inner_ear.data.materials.append(mat_white)
        parts.append(inner_ear)

    # --- Legs (Powerful Quadruped Feline Limbs) ---
    leg_coords = [
        # (name, side, x, y, hip_z)
        ("Front_L", -1, -0.48, 0.85, 1.3),
        ("Front_R",  1,  0.48, 0.85, 1.3),
        ("Rear_L",  -1, -0.46, -0.85, 1.4),
        ("Rear_R",   1,  0.46, -0.85, 1.4),
    ]

    for name, side, lx, ly, lz in leg_coords:
        is_rear = "Rear" in name

        # Shoulder / Hip Thigh
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.34, location=(lx, ly, lz))
        hip = bpy.context.active_object
        hip.scale = (0.65, 0.9, 1.3)
        hip.data.materials.append(mat_orange)
        parts.append(hip)

        # Upper Leg
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.65, vertices=12, location=(lx, ly + (0.05 if is_rear else -0.05), lz - 0.42))
        uleg = bpy.context.active_object
        uleg.rotation_euler = (math.radians(12 if is_rear else -8), 0, 0)
        uleg.data.materials.append(mat_orange)
        parts.append(uleg)

        # Lower Leg / Hock
        bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.6, vertices=12, location=(lx, ly + (-0.1 if is_rear else 0.05), lz - 0.88))
        lleg = bpy.context.active_object
        lleg.rotation_euler = (math.radians(-15 if is_rear else 5), 0, 0)
        lleg.data.materials.append(mat_orange)
        parts.append(lleg)

        # Paw (Large broad tiger paw)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.22, location=(lx, ly + (0.05 if is_rear else 0.1), 0.16))
        paw = bpy.context.active_object
        paw.scale = (0.9, 1.25, 0.55)
        paw.data.materials.append(mat_white)
        parts.append(paw)

        # Claws
        for c in range(3):
            cx = lx + (c - 1) * 0.09
            bpy.ops.mesh.primitive_cone_add(radius1=0.03, depth=0.12, vertices=6, location=(cx, ly + (0.28 if is_rear else 0.32), 0.08))
            claw = bpy.context.active_object
            claw.rotation_euler = (math.radians(70), 0, 0)
            claw.data.materials.append(mat_claw)
            parts.append(claw)

    # --- Tail (Gracefully curved feline tail with dark rings) ---
    tail_segments = 9
    for i in range(tail_segments):
        t_prog = i / tail_segments
        ty = -1.5 - (i * 0.22)
        tz = 1.35 + math.sin(t_prog * math.pi) * 0.45 - (t_prog * 0.7)
        tx = math.sin(t_prog * 2.5) * 0.18

        bpy.ops.mesh.primitive_cylinder_add(radius=0.11 - (t_prog * 0.04), depth=0.26, vertices=10, location=(tx, ty, tz))
        tseg = bpy.context.active_object
        tseg.rotation_euler = (math.radians(35 + i * 8), math.radians(math.sin(i) * 12), 0)
        # Alternate rings
        tseg.data.materials.append(mat_stripe if (i % 2 == 1 or i >= tail_segments - 2) else mat_orange)
        parts.append(tseg)

    # --- Characteristic Tiger Stripes (Feline Ribbons) ---
    stripe_configs = [
        # (x_scale, y_loc, z_loc, rot_z, thickness)
        (0.82, 0.65, 1.55, 0, 0.07),
        (0.84, 0.45, 1.58, 8, 0.08),
        (0.83, 0.25, 1.56, -6, 0.08),
        (0.82, 0.05, 1.54, 5, 0.09),
        (0.80, -0.18, 1.52, -10, 0.08),
        (0.78, -0.42, 1.50, 12, 0.08),
        (0.76, -0.65, 1.48, -8, 0.07),
        (0.72, -0.88, 1.45, 6, 0.07),
    ]

    for sx, sy, sz, rot, thick in stripe_configs:
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.72 * sx, minor_radius=thick,
            major_segments=24, minor_segments=8,
            location=(0, sy, sz)
        )
        stripe = bpy.context.active_object
        stripe.scale = (0.9, 0.45, 1.05)
        stripe.rotation_euler = (math.radians(90), math.radians(rot), 0)
        stripe.data.materials.append(mat_stripe)
        parts.append(stripe)

    # Select and join all parts
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()
    torso.name = "RoyalBengalTiger"

    # Shade smooth
    bpy.ops.object.shade_smooth()

    # Export to GLB
    out = os.path.join(MODELS_DIR, "tiger.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Successfully exported tiger.glb")

# =============================================================
# 2. INDIAN PEACOCK (Pavo cristatus)
# =============================================================
def build_peacock():
    reset_scene()
    print("Building Indian Peacock...")

    # Iridescent & Vibrant PBR Materials
    mat_blue = create_pbr_material("PeacockBlueMat", (0.03, 0.22, 0.65, 1.0), roughness=0.25, metallic=0.6, specular=0.8)
    mat_green = create_pbr_material("PeacockEmeraldMat", (0.04, 0.45, 0.22, 1.0), roughness=0.3, metallic=0.5, specular=0.7)
    mat_gold = create_pbr_material("PeacockGoldMat", (0.85, 0.62, 0.1, 1.0), roughness=0.35, metallic=0.7, specular=0.8)
    mat_wing = create_pbr_material("PeacockWingMat", (0.35, 0.28, 0.22, 1.0), roughness=0.8, specular=0.2)
    mat_beak = create_pbr_material("PeacockBeakMat", (0.6, 0.58, 0.52, 1.0), roughness=0.4, specular=0.4)
    mat_eye = create_pbr_material("PeacockEyeMat", (0.05, 0.05, 0.05, 1.0), roughness=0.1, specular=0.9)
    mat_leg = create_pbr_material("PeacockLegMat", (0.45, 0.42, 0.38, 1.0), roughness=0.7, specular=0.3)

    parts = []

    # --- Body & Breast ---
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=16, radius=0.65, location=(0, 0, 1.1))
    body = bpy.context.active_object
    body.scale = (0.75, 1.25, 0.85)
    body.data.materials.append(mat_blue)
    parts.append(body)

    # --- S-Curved Neck & Head ---
    neck_segs = 6
    for i in range(neck_segs):
        t = i / neck_segs
        ny = 0.55 + math.sin(t * math.pi) * 0.35
        nz = 1.35 + (i * 0.22)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.16 - (t * 0.04), depth=0.25, vertices=12, location=(0, ny, nz))
        nseg = bpy.context.active_object
        nseg.rotation_euler = (math.radians(-18 + i * 8), 0, 0)
        nseg.data.materials.append(mat_blue)
        parts.append(nseg)

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.22, location=(0, 0.85, 2.58))
    head = bpy.context.active_object
    head.scale = (0.85, 1.15, 0.95)
    head.data.materials.append(mat_blue)
    parts.append(head)

    # Beak
    bpy.ops.mesh.primitive_cone_add(radius1=0.08, depth=0.32, vertices=8, location=(0, 1.12, 2.54))
    beak = bpy.context.active_object
    beak.rotation_euler = (math.radians(78), 0, 0)
    beak.data.materials.append(mat_beak)
    parts.append(beak)

    # Eyes
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.05, location=(side * 0.16, 0.88, 2.62))
        eye = bpy.context.active_object
        eye.data.materials.append(mat_eye)
        parts.append(eye)

        # White eye stripe
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.12, vertices=6, location=(side * 0.17, 0.86, 2.62))
        stripe = bpy.context.active_object
        stripe.rotation_euler = (math.radians(90), 0, 0)
        stripe.data.materials.append(mat_beak)
        parts.append(stripe)

    # Crown Crest (5 fan feather pins)
    for c in range(5):
        c_angle = (c - 2) * 12
        cx = math.sin(math.radians(c_angle)) * 0.1
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.26, vertices=6, location=(cx, 0.8, 2.82))
        stem = bpy.context.active_object
        stem.rotation_euler = (math.radians(-15), math.radians(c_angle), 0)
        stem.data.materials.append(mat_blue)
        parts.append(stem)

        # Fan tuft top
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.045, location=(cx * 1.5, 0.77, 2.95))
        tuft = bpy.context.active_object
        tuft.scale = (0.8, 0.3, 1.2)
        tuft.data.materials.append(mat_green)
        parts.append(tuft)

    # --- Wings ---
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=0.45, location=(side * 0.42, -0.1, 1.15))
        wing = bpy.context.active_object
        wing.scale = (0.35, 1.1, 0.65)
        wing.rotation_euler = (math.radians(15), math.radians(side * 8), 0)
        wing.data.materials.append(mat_wing)
        parts.append(wing)

    # --- Magnificent Cascading Train (Ocelli Tail Feathers) ---
    train_layers = 12
    for t in range(train_layers):
        prog = t / train_layers
        ty = -0.8 - (t * 0.32)
        tz = 0.95 - (prog * 0.7)
        width = 0.7 + (prog * 1.4)

        # Feather train tier
        bpy.ops.mesh.primitive_cylinder_add(radius=width * 0.5, depth=0.35, vertices=16, location=(0, ty, tz))
        tier = bpy.context.active_object
        tier.rotation_euler = (math.radians(35), 0, 0)
        tier.scale = (1.2, 0.15, 1.0)
        tier.data.materials.append(mat_green)
        parts.append(tier)

        # Ocelli (Eyed spots)
        num_eyes = 2 + int(prog * 5)
        for e in range(num_eyes):
            ex = ((e / (num_eyes - 1)) - 0.5) * (width * 0.85)
            # Outer gold ring
            bpy.ops.mesh.primitive_circle_add(radius=0.1, fill_type='NGON', location=(ex, ty - 0.12, tz + 0.05))
            gold_eye = bpy.context.active_object
            gold_eye.rotation_euler = (math.radians(-50), 0, 0)
            gold_eye.data.materials.append(mat_gold)
            parts.append(gold_eye)

            # Inner blue pupil
            bpy.ops.mesh.primitive_circle_add(radius=0.05, fill_type='NGON', location=(ex, ty - 0.13, tz + 0.06))
            blue_pupil = bpy.context.active_object
            blue_pupil.rotation_euler = (math.radians(-50), 0, 0)
            blue_pupil.data.materials.append(mat_blue)
            parts.append(blue_pupil)

    # --- Legs & Spurred Claws ---
    for side in (-1, 1):
        lx = side * 0.22
        # Leg shaft
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.8, vertices=8, location=(lx, 0, 0.45))
        leg = bpy.context.active_object
        leg.data.materials.append(mat_leg)
        parts.append(leg)

        # 3 front toes + 1 spur
        for toe_angle in (-25, 0, 25):
            bpy.ops.mesh.primitive_cone_add(radius1=0.03, depth=0.25, vertices=6, location=(lx, 0.1, 0.06))
            toe = bpy.context.active_object
            toe.rotation_euler = (math.radians(85), 0, math.radians(toe_angle))
            toe.data.materials.append(mat_leg)
            parts.append(toe)

    # Select all and join
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = "IndianPeacock"
    bpy.ops.object.shade_smooth()

    # Export
    out = os.path.join(MODELS_DIR, "peacock.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Successfully exported peacock.glb")

# =============================================================
# 3. INDIAN WILD BOAR (Sus scrofa cristatus)
# =============================================================
def build_boar():
    reset_scene()
    print("Building Indian Wild Boar...")

    mat_coat = create_pbr_material("BoarBristleMat", (0.24, 0.17, 0.12, 1.0), roughness=0.92, specular=0.2)
    mat_ridge = create_pbr_material("BoarManeMat", (0.12, 0.09, 0.07, 1.0), roughness=0.95, specular=0.1)
    mat_snout = create_pbr_material("BoarSnoutMat", (0.42, 0.28, 0.22, 1.0), roughness=0.6, specular=0.3)
    mat_tusk = create_pbr_material("BoarTuskMat", (0.92, 0.9, 0.82, 1.0), roughness=0.35, specular=0.6)
    mat_eye = create_pbr_material("BoarEyeMat", (0.05, 0.04, 0.03, 1.0), roughness=0.2, specular=0.8)
    mat_hoof = create_pbr_material("BoarHoofMat", (0.15, 0.12, 0.1, 1.0), roughness=0.6, specular=0.4)

    parts = []

    # --- Torso (Robust, Barrel-chested, Arched dorsal spine) ---
    bpy.ops.mesh.primitive_uv_sphere_add(segments=22, ring_count=16, radius=0.95, location=(0, 0, 1.05))
    torso = bpy.context.active_object
    torso.scale = (0.75, 1.45, 0.92)
    torso.data.materials.append(mat_coat)
    parts.append(torso)

    # Muscular front shoulders
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=0.78, location=(0, 0.72, 1.15))
    shoulder = bpy.context.active_object
    shoulder.scale = (0.82, 0.85, 0.95)
    shoulder.data.materials.append(mat_coat)
    parts.append(shoulder)

    # Dorsal Ridge / Bristly Spine Mane
    for m in range(7):
        my = 0.9 - (m * 0.3)
        bpy.ops.mesh.primitive_cone_add(radius1=0.08, depth=0.35, vertices=6, location=(0, my, 1.8 - (m * 0.04)))
        mane = bpy.context.active_object
        mane.scale = (0.5, 1.3, 1.0)
        mane.rotation_euler = (math.radians(-15), 0, 0)
        mane.data.materials.append(mat_ridge)
        parts.append(mane)

    # --- Head & Snout ---
    # Neck
    bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.75, vertices=14, location=(0, 1.15, 1.12))
    neck = bpy.context.active_object
    neck.rotation_euler = (math.radians(20), 0, 0)
    neck.data.materials.append(mat_coat)
    parts.append(neck)

    # Wedge Head
    bpy.ops.mesh.primitive_cone_add(radius1=0.52, depth=1.1, vertices=12, location=(0, 1.75, 0.98))
    head = bpy.context.active_object
    head.rotation_euler = (math.radians(72), 0, 0)
    head.scale = (0.82, 0.85, 1.0)
    head.data.materials.append(mat_coat)
    parts.append(head)

    # Snout Disc (Flat cartilaginous rooting disc)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.12, vertices=14, location=(0, 2.32, 0.78))
    snout = bpy.context.active_object
    snout.rotation_euler = (math.radians(72), 0, 0)
    snout.scale = (1.1, 0.85, 1.0)
    snout.data.materials.append(mat_snout)
    parts.append(snout)

    # Nostrils
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.06, vertices=8, location=(side * 0.07, 2.38, 0.77))
        nostril = bpy.context.active_object
        nostril.rotation_euler = (math.radians(72), 0, 0)
        nostril.data.materials.append(mat_ridge)
        parts.append(nostril)

    # Upward Curving Ivory Tusks
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.35, vertices=8, location=(side * 0.22, 2.05, 0.82))
        tusk = bpy.context.active_object
        tusk.rotation_euler = (math.radians(-45), math.radians(side * 35), math.radians(side * 20))
        tusk.data.materials.append(mat_tusk)
        parts.append(tusk)

    # Eyes
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.08, location=(side * 0.32, 1.62, 1.22))
        eye = bpy.context.active_object
        eye.data.materials.append(mat_eye)
        parts.append(eye)

    # Pointed Ears
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(radius1=0.14, depth=0.38, vertices=8, location=(side * 0.36, 1.35, 1.48))
        ear = bpy.context.active_object
        ear.rotation_euler = (math.radians(-25), math.radians(side * 35), math.radians(side * 15))
        ear.scale = (0.7, 1.0, 1.0)
        ear.data.materials.append(mat_coat)
        parts.append(ear)

    # --- Sturdy Quadruped Limbs & Hooves ---
    leg_pos = [
        ("FL", -0.42,  0.65, 0.85),
        ("FR",  0.42,  0.65, 0.85),
        ("RL", -0.38, -0.65, 0.85),
        ("RR",  0.38, -0.65, 0.85),
    ]

    for name, lx, ly, lz in leg_pos:
        # Leg Upper
        bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=0.55, vertices=10, location=(lx, ly, lz - 0.2))
        l_up = bpy.context.active_object
        l_up.data.materials.append(mat_coat)
        parts.append(l_up)

        # Leg Lower
        bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=0.45, vertices=10, location=(lx, ly, lz - 0.58))
        l_low = bpy.context.active_object
        l_low.data.materials.append(mat_coat)
        parts.append(l_low)

        # Cloven Hoof
        for h in (-0.05, 0.05):
            bpy.ops.mesh.primitive_cone_add(radius1=0.06, depth=0.16, vertices=6, location=(lx + h, ly + 0.04, 0.08))
            hoof = bpy.context.active_object
            hoof.rotation_euler = (math.radians(15), 0, 0)
            hoof.data.materials.append(mat_hoof)
            parts.append(hoof)

    # Tail (Short tufted tail)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.42, vertices=8, location=(0, -1.35, 0.88))
    tail = bpy.context.active_object
    tail.rotation_euler = (math.radians(-65), 0, 0)
    tail.data.materials.append(mat_coat)
    parts.append(tail)

    # Join and smooth
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()
    torso.name = "IndianWildBoar"
    bpy.ops.object.shade_smooth()

    # Export
    out = os.path.join(MODELS_DIR, "boar.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Successfully exported boar.glb")

# =============================================================
# 4. INDIAN GIANT FLYING SQUIRREL (Petaurista philippensis)
# =============================================================
def build_squirrel():
    reset_scene()
    print("Building Indian Giant Flying Squirrel...")

    mat_fur = create_pbr_material("SquirrelChestnutFurMat", (0.52, 0.18, 0.08, 1.0), roughness=0.75, specular=0.3)
    mat_belly = create_pbr_material("SquirrelCreamMat", (0.92, 0.86, 0.75, 1.0), roughness=0.8, specular=0.2)
    mat_membrane = create_pbr_material("SquirrelPatagiumMat", (0.45, 0.16, 0.08, 1.0), roughness=0.7, specular=0.3)
    mat_eye = create_pbr_material("SquirrelEyeMat", (0.04, 0.03, 0.03, 1.0), roughness=0.1, specular=0.95)
    mat_nose = create_pbr_material("SquirrelNoseMat", (0.85, 0.5, 0.52, 1.0), roughness=0.4, specular=0.5)

    parts = []

    # --- Torso (Agile arboreal mammal body) ---
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=14, radius=0.45, location=(0, 0, 0.45))
    body = bpy.context.active_object
    body.scale = (0.75, 1.45, 0.65)
    body.data.materials.append(mat_fur)
    parts.append(body)

    # Cream underbelly
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.38, location=(0, 0, 0.35))
    belly = bpy.context.active_object
    belly.scale = (0.68, 1.35, 0.45)
    belly.data.materials.append(mat_belly)
    parts.append(belly)

    # --- Broad Patagium (Gliding Skin Membrane between limbs) ---
    for side in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(side * 0.55, 0.05, 0.4))
        patagium = bpy.context.active_object
        patagium.scale = (0.45, 0.95, 1.0)
        patagium.rotation_euler = (0, math.radians(side * -12), 0)
        patagium.data.materials.append(mat_membrane)
        parts.append(patagium)

    # --- Head & Alert Face ---
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=0.28, location=(0, 0.72, 0.62))
    head = bpy.context.active_object
    head.scale = (0.88, 1.15, 0.92)
    head.data.materials.append(mat_fur)
    parts.append(head)

    # Snout
    bpy.ops.mesh.primitive_cone_add(radius1=0.12, depth=0.22, vertices=10, location=(0, 0.96, 0.56))
    snout = bpy.context.active_object
    snout.rotation_euler = (math.radians(75), 0, 0)
    snout.data.materials.append(mat_fur)
    parts.append(snout)

    # Pink Nose
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.04, location=(0, 1.08, 0.55))
    nose = bpy.context.active_object
    nose.data.materials.append(mat_nose)
    parts.append(nose)

    # Large Nocturnal Dark Eyes (Big glossy squirrel eyes)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=10, radius=0.08, location=(side * 0.18, 0.78, 0.68))
        eye = bpy.context.active_object
        eye.data.materials.append(mat_eye)
        parts.append(eye)

    # Rounded Furry Ears
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.04, vertices=10, location=(side * 0.22, 0.62, 0.85))
        ear = bpy.context.active_object
        ear.rotation_euler = (math.radians(-25), math.radians(side * 35), 0)
        ear.data.materials.append(mat_fur)
        parts.append(ear)

    # --- Limbs & Paws ---
    paws = [
        (-0.45,  0.55, 0.38),
        ( 0.45,  0.55, 0.38),
        (-0.42, -0.55, 0.38),
        ( 0.42, -0.55, 0.38),
    ]
    for px, py, pz in paws:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.35, vertices=8, location=(px, py, pz))
        leg = bpy.context.active_object
        leg.rotation_euler = (0, math.radians(px * 35), 0)
        leg.data.materials.append(mat_fur)
        parts.append(leg)

        # Tiny claws
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.07, location=(px * 1.15, py, pz - 0.15))
        paw = bpy.context.active_object
        paw.data.materials.append(mat_belly)
        parts.append(paw)

    # --- Bushy Cylindrical Tail (Iconic Flying Squirrel Tail) ---
    tail_segs = 10
    for i in range(tail_segs):
        t = i / tail_segs
        ty = -0.65 - (i * 0.22)
        tz = 0.5 + math.sin(t * math.pi) * 0.35
        tx = math.sin(t * 3.0) * 0.08
        rad = 0.14 + math.sin(t * math.pi) * 0.06

        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=10, radius=rad, location=(tx, ty, tz))
        tseg = bpy.context.active_object
        tseg.scale = (1.0, 1.4, 1.0)
        tseg.data.materials.append(mat_fur)
        parts.append(tseg)

    # Join and smooth
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = "GiantFlyingSquirrel"
    bpy.ops.object.shade_smooth()

    # Export
    out = os.path.join(MODELS_DIR, "squirrel.glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print("✓ Successfully exported squirrel.glb")

# Run all 4 species builders
build_tiger()
build_peacock()
build_boar()
build_squirrel()
print("All 4 Species successfully modeled and exported!")
