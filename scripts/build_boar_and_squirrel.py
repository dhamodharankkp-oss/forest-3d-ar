import bpy
import bmesh
import math
import os
import numpy as np

MODELS_DIR = r"D:\tecplore\assets\models"
DEER_GLB = os.path.join(MODELS_DIR, "deer.glb")
OUT_BOAR_GLB = os.path.join(MODELS_DIR, "boar.glb")
OUT_SQUIRREL_GLB = os.path.join(MODELS_DIR, "squirrel.glb")
SCRATCH_DIR = r"C:\Users\dhamu\.gemini\antigravity\brain\81c2be10-66ba-4885-a2f1-70ceb803663e\scratch"
os.makedirs(SCRATCH_DIR, exist_ok=True)

def smoothstep(edge0, edge1, x):
    if edge1 == edge0:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)

def box_blur_2d(arr, r=6):
    pad = np.pad(arr, ((r, r), (r, r)), mode='edge')
    cs_x = np.cumsum(pad, axis=1)
    blur_x = (cs_x[:, 2*r:] - cs_x[:, :-2*r]) / (2 * r)
    cs_y = np.cumsum(blur_x, axis=0)
    blur_y = (cs_y[2*r:, :] - cs_y[:-2*r, :]) / (2 * r)
    return blur_y

# =============================================================================
# 1. PHOTOREALISTIC INDIAN WILD BOAR (Sus scrofa cristatus)
# =============================================================================
def build_realistic_boar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=DEER_GLB)

    obj = bpy.data.objects.get("deer.002_Material_0")
    if not obj:
        obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

    orig_img = bpy.data.images.get("Image_0")
    W, H = orig_img.size[0], orig_img.size[1]
    orig_pixels = np.array(orig_img.pixels[:], dtype=np.float32).reshape((H, W, 4))

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    obj.matrix_world.identity()

    verts_pool = set(bm.verts)
    islands = []
    while verts_pool:
        v0 = next(iter(verts_pool))
        q = [v0]
        comp = {v0}
        verts_pool.remove(v0)
        while q:
            curr = q.pop()
            for e in curr.link_edges:
                ov = e.other_vert(curr)
                if ov in verts_pool:
                    verts_pool.remove(ov)
                    comp.add(ov)
                    q.append(ov)
        islands.append(comp)

    islands.sort(key=lambda c: -len(c))

    antler_indices = {4, 6, 10, 11, 12, 13, 16, 17, 22, 23}
    verts_to_delete = []
    for idx in antler_indices:
        if idx < len(islands):
            verts_to_delete.extend(list(islands[idx]))

    vert_part = {}
    for idx, comp in enumerate(islands):
        if idx in antler_indices:
            continue
        if idx == 0:
            part = 'body'
        elif idx in (1, 2):
            part = 'rear_leg'
        elif idx in (3, 5):
            part = 'front_leg'
        elif idx in (7, 8):
            part = 'ear_outer'
        elif idx in (14, 15):
            part = 'ear_inner'
        elif idx == 9:
            part = 'tail'
        elif idx in (18, 19, 20, 21):
            part = 'paw'
        elif idx in (24, 25):
            part = 'eye'
        else:
            part = 'body'
        for v in comp:
            vert_part[v] = (part, idx)

    bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    pos_groups = {}
    for v in bm.verts:
        key = (round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3))
        pos_groups.setdefault(key, []).append(v)

    # Un-rotate neck yaw and store canonical coordinates
    anat_coords = {}
    for v in bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        t = smoothstep(-0.2, 1.4, x) * smoothstep(0.5, 1.7, z)
        ang = math.radians(14.8) * t
        xp, yp = 0.18, 0.0
        dx, dy = x - xp, y - yp
        v.co.x = xp + dx * math.cos(ang) - dy * math.sin(ang)
        v.co.y = yp + dx * math.sin(ang) + dy * math.cos(ang)
        if 1.55 < v.co.x < 2.05 and v.co.z > 3.55 and abs(v.co.y) < 0.28:
            v.co.z = 3.55 + (v.co.z - 3.55) * 0.22
        anat_coords[v] = (v.co.x, v.co.y, v.co.z)

    leg_defs = [
        ([3, 18],  1.25,  0.18),
        ([5, 20],  1.05, -0.38),
        ([2, 21], -1.02,  0.22),
        ([1, 19], -1.38, -0.31),
    ]
    z_samples = np.linspace(0.0, 1.85, 20)
    leg_curves = []
    for idxs, def_x, def_y in leg_defs:
        lv = [v for v in bm.verts if vert_part.get(v, (None, -1))[1] in idxs]
        cx_arr, cy_arr = [], []
        for zs in z_samples:
            nv = [v for v in lv if abs(v.co.z - zs) < 0.15]
            if not nv:
                nv = sorted(lv, key=lambda v: abs(v.co.z - zs))[:8]
            cx_arr.append(sum(v.co.x for v in nv) / len(nv))
            cy_arr.append(sum(v.co.y for v in nv) / len(nv))
        leg_curves.append((idxs, np.array(cx_arr), np.array(cy_arr)))

    # Sculpt Short Bristled Boar Tail (Island 9)
    tail_verts = [v for v in bm.verts if vert_part.get(v, (None, -1))[0] == 'tail']
    if tail_verts:
        zs = [v.co.z for v in tail_verts]
        z_min, z_max = min(zs), max(zs)
        for v in tail_verts:
            s = max(0.0, min(1.0, (z_max - v.co.z) / (z_max - z_min + 1e-6)))
            w_tail = smoothstep(0.0, 0.20, s)
            v.co.x -= 0.28 * s * w_tail
            v.co.z += 0.12 * s * w_tail
            vert_part[v] = ('tail', s)

    # Continuous 3D Spatial Morph Field for Indian Wild Boar
    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        # 1. Forward-angled bristly Wild Boar Ears
        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.21, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.35 * w_ear) + 0.05 * w_ear
            y = yb + (y - yb) * (1.0 - 0.35 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.15 * w_ear)

        # 2. Wedge-Shaped Wild Boar Head & Flat Cartilaginous Rooting Snout Disc
        w_head = smoothstep(1.65, 1.98, x) * smoothstep(2.70, 3.05, z)
        if w_head > 0.0:
            # Elongate and thicken conical boar snout, flattening the very tip into a disc!
            w_snout = smoothstep(2.10, 2.65, x)
            y *= (1.0 + w_head * (0.48 - 0.15 * w_snout))
            # Deep heavy boar jowls and wedge skull
            if z < 3.40:
                z -= 0.22 * w_head * (1.0 - 0.35 * w_snout)
            else:
                # Straight sloping boar forehead-to-snout profile + dorsal crest ridge
                z -= 0.12 * w_head * w_snout

            # Flatten the nose tip (x > 2.66) into a flat tilted rooting disc!
            if x > 2.66:
                x = 2.66 + (x - 2.66) * 0.25

        # 3. Pitch the Neck & Head strongly downward (-38 deg) into a stocky rooting boar stance!
        w_neck_rot = smoothstep(0.75, 1.50, x) * smoothstep(1.50, 2.10, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.05, 2.25
            ang1 = math.radians(-38.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1)
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)

        # 4. Massive Thick Boar Neck (merging shoulders straight into skull without a dip!)
        w_neck = smoothstep(0.85, 1.35, x) * (1.0 - smoothstep(1.85, 2.25, x)) * smoothstep(1.55, 2.00, z)
        if w_neck > 0.0:
            y *= (1.0 + 0.55 * w_neck)
            if z < 2.35:
                z -= 0.24 * w_neck

        # 5. Sturdy Stocky Legs below torso seam (z < 1.55)
        if part in ('front_leg', 'rear_leg', 'paw') and z < 1.58:
            for idxs, cx_arr, cy_arr in leg_curves:
                if isl_idx in idxs:
                    cx = float(np.interp(z, z_samples, cx_arr))
                    cy = float(np.interp(z, z_samples, cy_arr))
                    dx = x - cx
                    dy = y - cy
                    w_leg = 1.0 - smoothstep(1.10, 1.55, z)
                    thick = 1.0 + 0.48 * w_leg
                    x = cx + dx * thick
                    y = cy + dy * thick
                    break

        # 6. Barrel-Chested, Humped-Shoulder Wild Boar Proportions
        x *= 0.96
        y *= 1.42
        # High muscular shoulder hump (x in [0.2, 1.3]) & bristly dorsal spine ridge (|y| < 0.14)
        w_torso_top = smoothstep(2.15, 2.55, z) * smoothstep(-1.3, -0.8, x) * (1.0 - smoothstep(1.5, 2.0, x))
        shoulder_hump = math.exp(-((x - 0.78) / 0.55) ** 2) * 0.22 * w_torso_top
        dorsal_crest = math.exp(-(y / 0.10) ** 2) * 0.12 * w_torso_top * smoothstep(-0.6, 0.4, x)
        # Deep barrel belly
        w_belly = math.exp(-((x - 0.15) / 0.95) ** 2) * smoothstep(1.35, 1.80, z) * (1.0 - smoothstep(2.05, 2.40, z))
        z = z + shoulder_hump + dorsal_crest - 0.20 * w_belly

        # Low-slung stocky boar height
        z *= 0.68
        if z < 0.0:
            z = 0.0

        v.co.x, v.co.y, v.co.z = x, y, z

    # Weld coincident UV-seam vertices
    for key, v_list in pos_groups.items():
        if len(v_list) > 1:
            mx = sum(v.co.x for v in v_list) / len(v_list)
            my = sum(v.co.y for v in v_list) / len(v_list)
            mz = sum(v.co.z for v in v_list) / len(v_list)
            for v in v_list:
                v.co.x, v.co.y, v.co.z = mx, my, mz

    # Add 2 Sculpted Upward-Curving Ivory Tusks on the sides of the lower jaw!
    # Find the snout tip in morphed coordinates to position tusks with millimeter precision
    snout_verts = [v for v in bm.verts if anat_coords.get(v, (0,0,0))[0] > 2.50]
    sx = sum(v.co.x for v in snout_verts) / len(snout_verts)
    sz = sum(v.co.z for v in snout_verts) / len(snout_verts)

    uv_layer = bm.loops.layers.uv.active
    for side in (-1.0, 1.0):
        # Create curved conical tusk using 5 rings of 8 vertices
        rings = []
        n_seg = 8
        for r_idx in range(5):
            t = r_idx / 4.0
            rad = 0.032 * (1.0 - 0.82 * t)
            # Curve outward (Y), forward (X), and sharply upward (Z)
            rcx = sx - 0.14 + 0.10 * t
            rcy = side * (0.14 + 0.09 * t)
            rcz = sz - 0.06 + 0.22 * (t ** 1.35)
            ring_v = []
            for k in range(n_seg):
                ang = k * 2.0 * math.pi / n_seg
                vx = rcx + rad * math.cos(ang) * 0.7
                vy = rcy + rad * math.sin(ang) * 0.7
                vz = rcz + rad * math.cos(ang) * 0.4
                nv = bm.verts.new((vx, vy, vz))
                anat_coords[nv] = (3.0, side * 0.5, 3.0) # Tag as tusk in canonical coords
                vert_part[nv] = ('tusk', 99)
                ring_v.append(nv)
            rings.append(ring_v)
        # Bridge rings into triangles and assign UV in an unused corner (0.92, 0.92)
        for r_idx in range(4):
            r0, r1 = rings[r_idx], rings[r_idx + 1]
            for k in range(n_seg):
                k1 = (k + 1) % n_seg
                for tri in [(r0[k], r0[k1], r1[k1]), (r0[k], r1[k1], r1[k])]:
                    f = bm.faces.new(tri)
                    for loop in f.loops:
                        loop[uv_layer].uv = (0.94, 0.94)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.update()

    # Bake 1024x1024 Photorealistic Indian Wild Boar Texture
    print("Baking 1024x1024 Photorealistic Indian Wild Boar Texture...")
    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.52, 1.48)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.80 + 0.28 * (lum_smooth / (lum_macro + 0.05)), 0.62, 1.15)

    uv_ax = np.zeros((H, W), dtype=np.float32)
    uv_ay = np.zeros((H, W), dtype=np.float32)
    uv_az = np.zeros((H, W), dtype=np.float32)
    uv_part = np.zeros((H, W), dtype=np.int32)

    part_code_map = {
        'body': 1, 'rear_leg': 2, 'front_leg': 2, 'paw': 3,
        'ear_outer': 4, 'ear_inner': 5, 'tail': 6, 'eye': 7, 'tusk': 8
    }

    for face in bm.faces:
        loops = face.loops
        if len(loops) != 3:
            continue
        v0, v1, v2 = loops[0].vert, loops[1].vert, loops[2].vert
        uv0, uv1, uv2 = loops[0][uv_layer].uv, loops[1][uv_layer].uv, loops[2][uv_layer].uv
        u0, v_0 = uv0.x * (W - 1), uv0.y * (H - 1)
        u1, v_1 = uv1.x * (W - 1), uv1.y * (H - 1)
        u2, v_2 = uv2.x * (W - 1), uv2.y * (H - 1)
        min_u = max(0, int(math.floor(min(u0, u1, u2))) - 1)
        max_u = min(W - 1, int(math.ceil(max(u0, u1, u2))) + 1)
        min_v = max(0, int(math.floor(min(v_0, v_1, v_2))) - 1)
        max_v = min(H - 1, int(math.ceil(max(v_0, v_1, v_2))) + 1)
        denom = (v_1 - v_2) * (u0 - u2) + (u2 - u1) * (v_0 - v_2)
        if abs(denom) < 1e-5:
            continue
        p_code = part_code_map.get(vert_part.get(v0, ('body', 0))[0], 1)
        a0, a1, a2 = anat_coords[v0], anat_coords[v1], anat_coords[v2]
        us = np.arange(min_u, max_u + 1, dtype=np.float32)
        vs = np.arange(min_v, max_v + 1, dtype=np.float32)
        uu, vv = np.meshgrid(us, vs)
        w0 = ((v_1 - v_2) * (uu - u2) + (u2 - u1) * (vv - v_2)) / denom
        w1 = ((v_2 - v_0) * (uu - u2) + (u0 - u2) * (vv - v_2)) / denom
        w2 = 1.0 - w0 - w1
        mask = (w0 >= -0.08) & (w1 >= -0.08) & (w2 >= -0.08)
        if not np.any(mask):
            continue
        cw0, cw1, cw2 = np.clip(w0[mask], 0, 1), np.clip(w1[mask], 0, 1), np.clip(w2[mask], 0, 1)
        csum = cw0 + cw1 + cw2 + 1e-6
        cw0 /= csum; cw1 /= csum; cw2 /= csum
        ys_idx, xs_idx = np.where(mask)
        ys_idx += min_v; xs_idx += min_u
        uv_ax[ys_idx, xs_idx] = cw0 * a0[0] + cw1 * a1[0] + cw2 * a2[0]
        uv_ay[ys_idx, xs_idx] = cw0 * a0[1] + cw1 * a1[1] + cw2 * a2[1]
        uv_az[ys_idx, xs_idx] = cw0 * a0[2] + cw1 * a1[2] + cw2 * a2[2]
        uv_part[ys_idx, xs_idx] = p_code

    for _ in range(8):
        unassigned = (uv_part == 0)
        if not np.any(unassigned):
            break
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            shifted_part = np.roll(uv_part, shift=(dy, dx), axis=(0, 1))
            fill = unassigned & (shifted_part > 0)
            if np.any(fill):
                uv_part[fill] = shifted_part[fill]
                uv_ax[fill] = np.roll(uv_ax, shift=(dy, dx), axis=(0, 1))[fill]
                uv_ay[fill] = np.roll(uv_ay, shift=(dy, dx), axis=(0, 1))[fill]
                uv_az[fill] = np.roll(uv_az, shift=(dy, dx), axis=(0, 1))[fill]
                unassigned = (uv_part == 0)

    AX, AY, AZ, P = uv_ax, uv_ay, uv_az, uv_part

    # Grizzled Dark Umber-Charcoal Boar Coat with Silver-Grey Shoulder/Cheek Bristles
    dark_boar   = np.array([0.19, 0.14, 0.11], dtype=np.float32)
    black_mane  = np.array([0.07, 0.05, 0.04], dtype=np.float32)
    grizzle_gry = np.array([0.48, 0.43, 0.37], dtype=np.float32)
    snout_pink  = np.array([0.58, 0.36, 0.32], dtype=np.float32)

    # Dorsal black mane & dark lower stockings
    mane_zone = np.clip((AZ - 2.65) / 0.25, 0.0, 1.0) * np.exp(-(AY / 0.15) ** 2)
    sock_zone = np.clip((0.95 - AZ) / 0.35, 0.0, 1.0) * ((P == 2) | (P == 3))
    dark_mask = np.clip(mane_zone + sock_zone, 0.0, 1.0)

    # Grizzled grey-brown cheek crest & flank bristles (amplified where fur_detail > 1.08)
    grizzle_zone = np.clip((fur_detail - 1.04) * 3.2, 0.0, 1.0) * (1.0 - 0.7 * dark_mask)

    r = dark_boar[0] * (1.0 - dark_mask) + black_mane[0] * dark_mask
    g = dark_boar[1] * (1.0 - dark_mask) + black_mane[1] * dark_mask
    b = dark_boar[2] * (1.0 - dark_mask) + black_mane[2] * dark_mask

    r = r * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[0] * (0.55 * grizzle_zone)
    g = g * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[1] * (0.55 * grizzle_zone)
    b = b * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[2] * (0.55 * grizzle_zone)

    # Leathery Rooting Snout Disc & Two Dark Nostrils at tip of snout (AX > 2.60)
    disc_zone = (P == 1) & (AX > 2.60) & (AZ > 3.24) & (AZ < 3.49)
    nostril_zone = disc_zone & (AX > 2.64) & (np.abs( np.abs(AY) - 0.045 ) < 0.024) & (AZ > 3.33) & (AZ < 3.42)
    r = np.where(nostril_zone, 0.06, np.where(disc_zone, snout_pink[0], r))
    g = np.where(nostril_zone, 0.04, np.where(disc_zone, snout_pink[1], g))
    b = np.where(nostril_zone, 0.04, np.where(disc_zone, snout_pink[2], b))

    # Apply coarse photographic bristle micro-detail
    shade = np.clip(fur_detail * 1.15 - 0.15, 0.45, 1.50) * macro_ao
    r = np.clip(r * shade, 0.0, 1.0)
    g = np.clip(g * shade, 0.0, 1.0)
    b = np.clip(b * shade, 0.0, 1.0)

    # Ivory Tusks (UV corner [0.88..1.0, 0.88..1.0] or P == 8)
    uu_norm, vv_norm = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    tusk_mask = (P == 8) | ((uu_norm > 0.88) & (vv_norm > 0.88))
    r = np.where(tusk_mask, 0.95, r)
    g = np.where(tusk_mask, 0.92, g)
    b = np.where(tusk_mask, 0.83, b)

    # Preserve photorealistic dark amber eyes
    eye_uv_mask = (P == 7) | ((vv_norm > 0.76) & (vv_norm < 0.96) & (((uu_norm > 0.11) & (uu_norm < 0.25)) | ((uu_norm > 0.45) & (uu_norm < 0.58))))
    r = np.where(eye_uv_mask, orig_pixels[:, :, 0] * 0.9, r)
    g = np.where(eye_uv_mask, orig_pixels[:, :, 1] * 0.8, g)
    b = np.where(eye_uv_mask, orig_pixels[:, :, 2] * 0.6, b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = r; out_pixels[:, :, 1] = g; out_pixels[:, :, 2] = b

    boar_img = bpy.data.images.new("BoarPBRTex", width=W, height=H, alpha=False)
    boar_img.pixels[:] = out_pixels.ravel().tolist()
    boar_img.filepath_raw = os.path.join(SCRATCH_DIR, "boar_tex.png")
    boar_img.file_format = 'PNG'
    boar_img.save()
    boar_img.pack()

    mat = obj.data.materials[0]
    mat.name = "IndianWildBoarMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            node.image = boar_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs:
                node.inputs['Roughness'].default_value = 0.88

    bm.free()
    obj.name = "IndianWildBoar"
    bpy.ops.export_scene.gltf(filepath=OUT_BOAR_GLB, export_format='GLB')
    print(f"✓ Exported photorealistic Indian Wild Boar to {OUT_BOAR_GLB}")


# =============================================================================
# 2. PHOTOREALISTIC INDIAN GIANT FLYING SQUIRREL (Petaurista philippensis)
# =============================================================================
def build_realistic_squirrel():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=DEER_GLB)

    obj = bpy.data.objects.get("deer.002_Material_0")
    if not obj:
        obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

    orig_img = bpy.data.images.get("Image_0")
    W, H = orig_img.size[0], orig_img.size[1]
    orig_pixels = np.array(orig_img.pixels[:], dtype=np.float32).reshape((H, W, 4))

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    obj.matrix_world.identity()

    verts_pool = set(bm.verts)
    islands = []
    while verts_pool:
        v0 = next(iter(verts_pool))
        q = [v0]
        comp = {v0}
        verts_pool.remove(v0)
        while q:
            curr = q.pop()
            for e in curr.link_edges:
                ov = e.other_vert(curr)
                if ov in verts_pool:
                    verts_pool.remove(ov)
                    comp.add(ov)
                    q.append(ov)
        islands.append(comp)

    islands.sort(key=lambda c: -len(c))

    antler_indices = {4, 6, 10, 11, 12, 13, 16, 17, 22, 23}
    verts_to_delete = []
    for idx in antler_indices:
        if idx < len(islands):
            verts_to_delete.extend(list(islands[idx]))

    vert_part = {}
    for idx, comp in enumerate(islands):
        if idx in antler_indices:
            continue
        if idx == 0:
            part = 'body'
        elif idx in (1, 2):
            part = 'rear_leg'
        elif idx in (3, 5):
            part = 'front_leg'
        elif idx in (7, 8):
            part = 'ear_outer'
        elif idx in (14, 15):
            part = 'ear_inner'
        elif idx == 9:
            part = 'tail'
        elif idx in (18, 19, 20, 21):
            part = 'paw'
        elif idx in (24, 25):
            part = 'eye'
        else:
            part = 'body'
        for v in comp:
            vert_part[v] = (part, idx)

    bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    pos_groups = {}
    for v in bm.verts:
        key = (round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3))
        pos_groups.setdefault(key, []).append(v)

    anat_coords = {}
    for v in bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        t = smoothstep(-0.2, 1.4, x) * smoothstep(0.5, 1.7, z)
        ang = math.radians(14.8) * t
        xp, yp = 0.18, 0.0
        dx, dy = x - xp, y - yp
        v.co.x = xp + dx * math.cos(ang) - dy * math.sin(ang)
        v.co.y = yp + dx * math.sin(ang) + dy * math.cos(ang)
        if 1.55 < v.co.x < 2.05 and v.co.z > 3.55 and abs(v.co.y) < 0.28:
            v.co.z = 3.55 + (v.co.z - 3.55) * 0.22
        anat_coords[v] = (v.co.x, v.co.y, v.co.z)

    # Sculpt Huge Plumed Bushy Cylindrical Flying Squirrel Tail (Island 9)
    tail_verts = [v for v in bm.verts if vert_part.get(v, (None, -1))[0] == 'tail']
    if tail_verts:
        zs = [v.co.z for v in tail_verts]
        z_min, z_max = min(zs), max(zs)
        s_bins = np.linspace(0.0, 1.0, 16)
        orig_cx, orig_cy, orig_rad = [], [], []
        for sb in s_bins:
            zt = z_max - sb * (z_max - z_min)
            nv = sorted(tail_verts, key=lambda v: abs(v.co.z - zt))[:10]
            mx = sum(v.co.x for v in nv) / len(nv)
            my = sum(v.co.y for v in nv) / len(nv)
            mr = sum(math.hypot(v.co.x - mx, v.co.y - my) for v in nv) / len(nv)
            orig_cx.append(mx)
            orig_cy.append(my)
            orig_rad.append(max(mr, 0.03))

        for v in tail_verts:
            s = max(0.0, min(1.0, (z_max - v.co.z) / (z_max - z_min + 1e-6)))
            ocx = float(np.interp(s, s_bins, orig_cx))
            ocy = float(np.interp(s, s_bins, orig_cy))
            orad = float(np.interp(s, s_bins, orig_rad))

            ux = (v.co.x - ocx) / orad
            uy = (v.co.y - ocy) / orad
            unorm = math.hypot(ux, uy)
            if unorm > 1e-4:
                ux /= unorm; uy /= unorm

            # Huge fluffy plume radius (up to 0.34 wide!) tapering at root and rounded tip
            plume_env = math.sin(max(0.08, min(0.96, s)) * math.pi) ** 0.55
            target_r = 0.32 * plume_env

            w_tail = smoothstep(0.0, 0.14, s)
            # Graceful squirrel tail arch sweeping back and curling upward
            tx = -1.35 - 2.05 * (s ** 0.88)
            ty = 0.0
            tz = 2.40 + 0.55 * math.sin(s * math.pi) - 0.15 * s

            new_x = tx + ux * target_r * 0.45
            new_y = ty + uy * target_r * 1.15
            new_z = tz + ux * target_r * 0.95

            v.co.x = v.co.x * (1.0 - w_tail) + new_x * w_tail
            v.co.y = v.co.y * (1.0 - w_tail) + new_y * w_tail
            v.co.z = v.co.z * (1.0 - w_tail) + new_z * w_tail
            vert_part[v] = ('tail', s)

    # Continuous 3D Spatial Morph Field for Indian Giant Flying Squirrel
    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        # 1. Rounded Squirrel Ears
        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.20, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.45 * w_ear)
            y = yb + (y - yb) * (1.0 - 0.55 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.35 * w_ear)

        # 2. Cute Rounded Rodent Skull, Big Nocturnal Eyes, & Short Curved Snout
        w_head = smoothstep(1.68, 2.00, x) * smoothstep(2.75, 3.10, z)
        if w_head > 0.0:
            # Shorten snout significantly into a cute rounded squirrel muzzle
            if x > 2.02:
                x = 2.02 + (x - 2.02) * (1.0 - 0.48 * w_head)
            # Round out the cheeks and skull dome
            y *= (1.0 + 0.28 * w_head)
            z -= 0.14 * w_head * smoothstep(2.00, 2.45, x)

        # 3. Pitch neck forward/down (-32 deg) so the head nestles close to the shoulders like a squirrel
        w_neck_rot = smoothstep(0.75, 1.50, x) * smoothstep(1.50, 2.10, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.05, 2.25
            ang1 = math.radians(-32.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1)
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)
            # Compress neck length slightly so head sits close to torso
            x -= 0.22 * w_neck_rot

        # 4. Patagium Gliding Membrane along the lower flanks between front and rear limbs!
        w_patagium = math.exp(-((x - (-0.05)) / 0.82) ** 2) * math.exp(-((z - 1.92) / 0.26) ** 2) * smoothstep(0.18, 0.38, abs(y))
        if part == 'body' and w_patagium > 0.0:
            y += math.copysign(0.38 * w_patagium, y)
            z -= 0.12 * w_patagium

        # 5. Arched Rodent Back & Compact Crouched Limbs
        w_arch = math.exp(-((x - (-0.15)) / 0.85) ** 2) * smoothstep(2.10, 2.55, z)
        z += 0.22 * w_arch

        # Compress leg height below belly (z < 1.55) into agile crouching arboreal limbs
        if z < 1.65:
            z = 1.65 - (1.65 - z) * 0.52
        else:
            z = 1.65 * 0.48 + (z - 1.65) * 0.78
        z -= 1.65 * 0.48
        if z < 0.0:
            z = 0.0

        y *= 1.25
        v.co.x, v.co.y, v.co.z = x, y, z

    # Weld coincident UV-seam vertices
    for key, v_list in pos_groups.items():
        if len(v_list) > 1:
            mx = sum(v.co.x for v in v_list) / len(v_list)
            my = sum(v.co.y for v in v_list) / len(v_list)
            mz = sum(v.co.z for v in v_list) / len(v_list)
            for v in v_list:
                v.co.x, v.co.y, v.co.z = mx, my, mz

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.update()

    # Bake 1024x1024 Photorealistic Indian Giant Flying Squirrel Texture
    print("Baking 1024x1024 Photorealistic Indian Giant Flying Squirrel Texture...")
    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.55, 1.45)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.80 + 0.28 * (lum_smooth / (lum_macro + 0.05)), 0.65, 1.15)

    uv_ax = np.zeros((H, W), dtype=np.float32)
    uv_ay = np.zeros((H, W), dtype=np.float32)
    uv_az = np.zeros((H, W), dtype=np.float32)
    uv_part = np.zeros((H, W), dtype=np.int32)
    uv_tail_s = np.zeros((H, W), dtype=np.float32)

    part_code_map = {
        'body': 1, 'rear_leg': 2, 'front_leg': 2, 'paw': 3,
        'ear_outer': 4, 'ear_inner': 5, 'tail': 6, 'eye': 7
    }

    uv_layer = bm.loops.layers.uv.active
    for face in bm.faces:
        loops = face.loops
        if len(loops) != 3:
            continue
        v0, v1, v2 = loops[0].vert, loops[1].vert, loops[2].vert
        uv0, uv1, uv2 = loops[0][uv_layer].uv, loops[1][uv_layer].uv, loops[2][uv_layer].uv
        u0, v_0 = uv0.x * (W - 1), uv0.y * (H - 1)
        u1, v_1 = uv1.x * (W - 1), uv1.y * (H - 1)
        u2, v_2 = uv2.x * (W - 1), uv2.y * (H - 1)
        min_u = max(0, int(math.floor(min(u0, u1, u2))) - 1)
        max_u = min(W - 1, int(math.ceil(max(u0, u1, u2))) + 1)
        min_v = max(0, int(math.floor(min(v_0, v_1, v_2))) - 1)
        max_v = min(H - 1, int(math.ceil(max(v_0, v_1, v_2))) + 1)
        denom = (v_1 - v_2) * (u0 - u2) + (u2 - u1) * (v_0 - v_2)
        if abs(denom) < 1e-5:
            continue
        p_code = part_code_map.get(vert_part.get(v0, ('body', 0))[0], 1)
        ts0 = float(vert_part.get(v0, ('body', 0.0))[1]) if p_code == 6 else 0.0
        ts1 = float(vert_part.get(v1, ('body', 0.0))[1]) if p_code == 6 else 0.0
        ts2 = float(vert_part.get(v2, ('body', 0.0))[1]) if p_code == 6 else 0.0
        a0, a1, a2 = anat_coords[v0], anat_coords[v1], anat_coords[v2]
        us = np.arange(min_u, max_u + 1, dtype=np.float32)
        vs = np.arange(min_v, max_v + 1, dtype=np.float32)
        uu, vv = np.meshgrid(us, vs)
        w0 = ((v_1 - v_2) * (uu - u2) + (u2 - u1) * (vv - v_2)) / denom
        w1 = ((v_2 - v_0) * (uu - u2) + (u0 - u2) * (vv - v_2)) / denom
        w2 = 1.0 - w0 - w1
        mask = (w0 >= -0.08) & (w1 >= -0.08) & (w2 >= -0.08)
        if not np.any(mask):
            continue
        cw0, cw1, cw2 = np.clip(w0[mask], 0, 1), np.clip(w1[mask], 0, 1), np.clip(w2[mask], 0, 1)
        csum = cw0 + cw1 + cw2 + 1e-6
        cw0 /= csum; cw1 /= csum; cw2 /= csum
        ys_idx, xs_idx = np.where(mask)
        ys_idx += min_v; xs_idx += min_u
        uv_ax[ys_idx, xs_idx] = cw0 * a0[0] + cw1 * a1[0] + cw2 * a2[0]
        uv_ay[ys_idx, xs_idx] = cw0 * a0[1] + cw1 * a1[1] + cw2 * a2[1]
        uv_az[ys_idx, xs_idx] = cw0 * a0[2] + cw1 * a1[2] + cw2 * a2[2]
        uv_part[ys_idx, xs_idx] = p_code
        if p_code == 6:
            uv_tail_s[ys_idx, xs_idx] = cw0 * ts0 + cw1 * ts1 + cw2 * ts2

    for _ in range(8):
        unassigned = (uv_part == 0)
        if not np.any(unassigned):
            break
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            shifted_part = np.roll(uv_part, shift=(dy, dx), axis=(0, 1))
            fill = unassigned & (shifted_part > 0)
            if np.any(fill):
                uv_part[fill] = shifted_part[fill]
                uv_ax[fill] = np.roll(uv_ax, shift=(dy, dx), axis=(0, 1))[fill]
                uv_ay[fill] = np.roll(uv_ay, shift=(dy, dx), axis=(0, 1))[fill]
                uv_az[fill] = np.roll(uv_az, shift=(dy, dx), axis=(0, 1))[fill]
                uv_tail_s[fill] = np.roll(uv_tail_s, shift=(dy, dx), axis=(0, 1))[fill]
                unassigned = (uv_part == 0)

    AX, AY, AZ, P = uv_ax, uv_ay, uv_az, uv_part

    # Rich Indian Giant Flying Squirrel Palette: Deep Maroon-Chestnut Dorsum, Russet Patagium Border, Warm Cream Belly
    maroon_back  = np.array([0.46, 0.13, 0.08], dtype=np.float32)
    russet_flank = np.array([0.68, 0.25, 0.12], dtype=np.float32)
    cream_belly  = np.array([0.94, 0.86, 0.74], dtype=np.float32)
    dark_tip     = np.array([0.14, 0.06, 0.05], dtype=np.float32)

    dorsal_t = np.clip((AZ - 2.15) / 0.55, 0.0, 1.0)
    r = russet_flank[0] * (1.0 - dorsal_t) + maroon_back[0] * dorsal_t
    g = russet_flank[1] * (1.0 - dorsal_t) + maroon_back[1] * dorsal_t
    b = russet_flank[2] * (1.0 - dorsal_t) + maroon_back[2] * dorsal_t

    # Cream underbelly, throat, & cheeks
    throat_line = 1.95 + 1.25 * np.clip((AX - 1.15) / 0.95, 0.0, 1.0)
    belly_w = np.clip((throat_line - AZ) / 0.24, 0.0, 1.0) * (P == 1)
    r = r * (1.0 - belly_w) + cream_belly[0] * belly_w
    g = g * (1.0 - belly_w) + cream_belly[1] * belly_w
    b = b * (1.0 - belly_w) + cream_belly[2] * belly_w

    # Dark chocolate-maroon paws, outer ears, eye rings, and bushy tail tip
    dark_zone = np.clip((0.55 - AZ) / 0.25, 0.0, 1.0) * ((P == 2) | (P == 3))
    dark_zone = np.where(P == 4, 0.85, dark_zone)
    dark_zone = np.where(P == 6, np.clip((uv_tail_s - 0.35) / 0.45, 0.15, 0.92), dark_zone)
    r = r * (1.0 - dark_zone) + dark_tip[0] * dark_zone
    g = g * (1.0 - dark_zone) + dark_tip[1] * dark_zone
    b = b * (1.0 - dark_zone) + dark_tip[2] * dark_zone

    # Pink nose pad
    nose_tip = (P == 1) & (AX > 2.63) & (np.abs(AY) < 0.07) & (AZ > 3.33) & (AZ < 3.46)
    r = np.where(nose_tip, 0.86, r)
    g = np.where(nose_tip, 0.48, g)
    b = np.where(nose_tip, 0.46, b)

    shade = np.where(P == 6, np.clip(fur_detail, 0.78, 1.22), fur_detail * macro_ao)
    r = np.clip(r * shade, 0.0, 1.0)
    g = np.clip(g * shade, 0.0, 1.0)
    b = np.clip(b * shade, 0.0, 1.0)

    # Large Glossy Dark Nocturnal Eyes
    uu_norm, vv_norm = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    eye_uv_mask = (P == 7) | ((vv_norm > 0.76) & (vv_norm < 0.96) & (((uu_norm > 0.11) & (uu_norm < 0.25)) | ((uu_norm > 0.45) & (uu_norm < 0.58))))
    r = np.where(eye_uv_mask, orig_pixels[:, :, 0] * 0.45, r)
    g = np.where(eye_uv_mask, orig_pixels[:, :, 1] * 0.35, g)
    b = np.where(eye_uv_mask, orig_pixels[:, :, 2] * 0.35, b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = r; out_pixels[:, :, 1] = g; out_pixels[:, :, 2] = b

    sq_img = bpy.data.images.new("SquirrelPBRTex", width=W, height=H, alpha=False)
    sq_img.pixels[:] = out_pixels.ravel().tolist()
    sq_img.filepath_raw = os.path.join(SCRATCH_DIR, "squirrel_tex.png")
    sq_img.file_format = 'PNG'
    sq_img.save()
    sq_img.pack()

    mat = obj.data.materials[0]
    mat.name = "GiantFlyingSquirrelMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            node.image = sq_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs:
                node.inputs['Roughness'].default_value = 0.76

    bm.free()
    obj.name = "IndianGiantFlyingSquirrel"
    bpy.ops.export_scene.gltf(filepath=OUT_SQUIRREL_GLB, export_format='GLB')
    print(f"✓ Exported photorealistic Indian Giant Flying Squirrel to {OUT_SQUIRREL_GLB}")

if __name__ == "__main__":
    build_realistic_boar()
    build_realistic_squirrel()
