import bpy
import bmesh
import math
import os
import numpy as np

MODELS_DIR = r"D:\tecplore\assets\models"
DEER_GLB = os.path.join(MODELS_DIR, "deer.glb")
OUT_TIGER_GLB = os.path.join(MODELS_DIR, "tiger.glb")
SCRATCH_DIR = r"C:\Users\dhamu\.gemini\antigravity\brain\81c2be10-66ba-4885-a2f1-70ceb803663e\scratch"
os.makedirs(SCRATCH_DIR, exist_ok=True)

def smoothstep(edge0, edge1, x):
    if edge1 == edge0:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)

def build_realistic_tiger():
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

    # Step 1: Un-rotate the deer's -14.8 deg neck/head yaw around (xp=0.18, yp=0.0)
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

    # Step 2: Sculpt Tail (Island 9)
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

            tip_round = math.sqrt(max(0.04, 1.0 - max(0.0, (s - 0.88) / 0.12) ** 2))
            target_r = (0.115 * (1.0 - 0.25 * s)) * tip_round

            w_tail = smoothstep(0.0, 0.15, s)
            tx = -1.42 - 1.55 * (s ** 0.95)
            ty = 0.0
            tz = 2.48 - 1.85 * math.sin(s * 0.72 * math.pi) + 0.30 * (s ** 2.4)

            s2 = min(1.0, s + 0.02)
            tx2 = -1.42 - 1.55 * (s2 ** 0.95)
            tz2 = 2.48 - 1.85 * math.sin(s2 * 0.72 * math.pi) + 0.30 * (s2 ** 2.4)
            tang_x, tang_z = tx2 - tx, tz2 - tz
            tlen = math.hypot(tang_x, tang_z) or 1.0
            nx_xz, nz_xz = -tang_z / tlen, tang_x / tlen

            new_x = tx + ux * target_r * nx_xz
            new_y = ty + uy * target_r
            new_z = tz + ux * target_r * nz_xz

            v.co.x = v.co.x * (1.0 - w_tail) + new_x * w_tail
            v.co.y = v.co.y * (1.0 - w_tail) + new_y * w_tail
            v.co.z = v.co.z * (1.0 - w_tail) + new_z * w_tail
            vert_part[v] = ('tail', s)

    # Step 3: Continuous 3D Spatial Morph Field W(x, y, z)
    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        # 3a. Rounded Upright Tiger Ears
        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.20, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.55 * w_ear)
            y = yb + (y - yb) * (1.0 - 0.52 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.15 * w_ear) + 0.06 * w_ear

        # 3b. Feline Skull, Forward-Facing Predator Eyes, Cheek Ruffs, & Muzzle
        w_head = smoothstep(1.70, 2.00, x) * smoothstep(2.75, 3.10, z)
        if w_head > 0.0:
            # Shorten snout into compact feline muzzle
            if x > 2.10:
                x = 2.10 + (x - 2.10) * (1.0 - 0.35 * w_head)

            # High rounded Tiger forehead / crown dome between and in front of the ears!
            w_crown = math.exp(-((x - 1.98) / 0.22) ** 2) * math.exp(-(y / 0.18) ** 2) * smoothstep(3.38, 3.52, z)
            z += 0.14 * w_crown * w_head

            # Forward-facing binocular predator eye placement: pull eye sockets slightly inward and forward
            w_eye_socket = math.exp(-((x - 2.18) / 0.14) ** 2) * math.exp(-((z - 3.54) / 0.12) ** 2)
            y *= (1.0 - 0.14 * w_eye_socket)
            x += 0.04 * w_eye_socket * (1.0 - smoothstep(0.10, 0.24, abs(y)))

            # Widen zygomatic cheekbones & cheek ruffs (jowls) below the eyes (z < 3.44)
            w_cheek_zone = (1.0 - smoothstep(3.36, 3.52, z)) * (1.0 - 0.55 * smoothstep(2.15, 2.48, x))
            y *= (1.0 + 0.34 * w_head * w_cheek_zone)

            w_ruff = math.exp(-((x - 1.98) / 0.15) ** 2) * math.exp(-((z - 3.22) / 0.18) ** 2) * smoothstep(0.08, 0.18, abs(y))
            y += math.copysign(0.12 * w_ruff, y)

            # Slope nasal bridge slightly downward and deepen the feline chin/jaw
            z -= 0.15 * w_head * smoothstep(2.05, 2.52, x)
            if z < 3.36:
                z -= 0.14 * w_head * smoothstep(1.95, 2.35, x) * smoothstep(3.36, 3.18, z)

        # 3c. Skeletal FK Neck & Head Rotation:
        w_neck_rot = smoothstep(0.85, 1.55, x) * smoothstep(1.55, 2.15, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.10, 2.30
            ang1 = math.radians(-27.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1)
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)

        # 3d. Thicken muscular Tiger neck & throat
        w_neck = smoothstep(1.05, 1.40, x) * (1.0 - smoothstep(1.90, 2.20, x)) * smoothstep(1.65, 2.05, z)
        if w_neck > 0.0:
            y *= (1.0 + 0.30 * w_neck)
            if z < 2.45:
                z -= 0.14 * w_neck * smoothstep(2.45, 1.85, z)

        # 3e. Thicken Legs & Paws strictly below torso seam (z < 1.55)
        if part in ('front_leg', 'rear_leg', 'paw') and z < 1.58:
            for idxs, cx_arr, cy_arr in leg_curves:
                if isl_idx in idxs:
                    cx = float(np.interp(z, z_samples, cx_arr))
                    cy = float(np.interp(z, z_samples, cy_arr))
                    dx = x - cx
                    dy = y - cy

                    w_leg = 1.0 - smoothstep(1.10, 1.55, z)
                    thick = 1.0 + 0.56 * w_leg
                    w_paw = 1.0 - smoothstep(0.02, 0.18, z)
                    paw_x_scale = thick + 0.24 * w_paw
                    paw_y_scale = thick + 0.20 * w_paw

                    x = cx + dx * paw_x_scale + 0.035 * w_paw
                    y = cy + dy * paw_y_scale
                    break

        # 3f. Global Feline Proportions
        x *= 1.10
        y *= 1.24
        w_chest = math.exp(-((x - 0.35) / 0.85) ** 2) * smoothstep(1.35, 1.85, z) * (1.0 - smoothstep(2.05, 2.45, z))
        z -= 0.12 * w_chest
        z *= 0.82
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

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.update()

    # =========================================================================
    # Step 4: Bake 1024x1024 Photorealistic Royal Bengal Tiger Texture
    # =========================================================================
    print("Baking 1024x1024 Photorealistic Royal Bengal Tiger Texture...")

    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    def box_blur_2d(arr, r=6):
        pad = np.pad(arr, ((r, r), (r, r)), mode='edge')
        cs_x = np.cumsum(pad, axis=1)
        blur_x = (cs_x[:, 2*r:] - cs_x[:, :-2*r]) / (2 * r)
        cs_y = np.cumsum(blur_x, axis=0)
        blur_y = (cs_y[2*r:, :] - cs_y[:-2*r, :]) / (2 * r)
        return blur_y

    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.60, 1.40)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.82 + 0.25 * (lum_smooth / (lum_macro + 0.05)), 0.68, 1.14)

    uv_ax = np.zeros((H, W), dtype=np.float32)
    uv_ay = np.zeros((H, W), dtype=np.float32)
    uv_az = np.zeros((H, W), dtype=np.float32)
    uv_nx = np.zeros((H, W), dtype=np.float32)
    uv_ny = np.zeros((H, W), dtype=np.float32)
    uv_nz = np.zeros((H, W), dtype=np.float32)
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
        uv0 = loops[0][uv_layer].uv
        uv1 = loops[1][uv_layer].uv
        uv2 = loops[2][uv_layer].uv

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

        p_info = vert_part.get(v0, ('body', 0))
        p_code = part_code_map.get(p_info[0], 1)
        ts0 = float(vert_part.get(v0, ('body', 0.0))[1]) if p_code == 6 else 0.0
        ts1 = float(vert_part.get(v1, ('body', 0.0))[1]) if p_code == 6 else 0.0
        ts2 = float(vert_part.get(v2, ('body', 0.0))[1]) if p_code == 6 else 0.0

        a0 = anat_coords[v0]
        a1 = anat_coords[v1]
        a2 = anat_coords[v2]

        us = np.arange(min_u, max_u + 1, dtype=np.float32)
        vs = np.arange(min_v, max_v + 1, dtype=np.float32)
        uu, vv = np.meshgrid(us, vs)

        w0 = ((v_1 - v_2) * (uu - u2) + (u2 - u1) * (vv - v_2)) / denom
        w1 = ((v_2 - v_0) * (uu - u2) + (u0 - u2) * (vv - v_2)) / denom
        w2 = 1.0 - w0 - w1

        mask = (w0 >= -0.08) & (w1 >= -0.08) & (w2 >= -0.08)
        if not np.any(mask):
            continue

        cw0 = np.clip(w0[mask], 0.0, 1.0)
        cw1 = np.clip(w1[mask], 0.0, 1.0)
        cw2 = np.clip(w2[mask], 0.0, 1.0)
        csum = cw0 + cw1 + cw2 + 1e-6
        cw0 /= csum; cw1 /= csum; cw2 /= csum

        ys_idx, xs_idx = np.where(mask)
        ys_idx += min_v
        xs_idx += min_u

        uv_ax[ys_idx, xs_idx] = cw0 * a0[0] + cw1 * a1[0] + cw2 * a2[0]
        uv_ay[ys_idx, xs_idx] = cw0 * a0[1] + cw1 * a1[1] + cw2 * a2[1]
        uv_az[ys_idx, xs_idx] = cw0 * a0[2] + cw1 * a1[2] + cw2 * a2[2]
        uv_nx[ys_idx, xs_idx] = cw0 * v0.normal.x + cw1 * v1.normal.x + cw2 * v2.normal.x
        uv_ny[ys_idx, xs_idx] = cw0 * v0.normal.y + cw1 * v1.normal.y + cw2 * v2.normal.y
        uv_nz[ys_idx, xs_idx] = cw0 * v0.normal.z + cw1 * v1.normal.z + cw2 * v2.normal.z
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
                uv_nx[fill] = np.roll(uv_nx, shift=(dy, dx), axis=(0, 1))[fill]
                uv_ny[fill] = np.roll(uv_ny, shift=(dy, dx), axis=(0, 1))[fill]
                uv_nz[fill] = np.roll(uv_nz, shift=(dy, dx), axis=(0, 1))[fill]
                uv_tail_s[fill] = np.roll(uv_tail_s, shift=(dy, dx), axis=(0, 1))[fill]
                unassigned = (uv_part == 0)

    AX, AY, AZ = uv_ax, uv_ay, uv_az
    NX, NY, NZ = uv_nx, uv_ny, uv_nz
    P = uv_part

    spine_dark_orange = np.array([0.82, 0.34, 0.04], dtype=np.float32)
    flank_orange      = np.array([0.93, 0.46, 0.09], dtype=np.float32)
    cream_white       = np.array([0.97, 0.95, 0.90], dtype=np.float32)
    stripe_black      = np.array([0.06, 0.04, 0.03], dtype=np.float32)
    nose_pink         = np.array([0.85, 0.43, 0.39], dtype=np.float32)

    dorsal_t = np.clip((AZ - 2.35) / 0.55, 0.0, 1.0) * np.clip(NZ, 0.0, 1.0)
    base_r = flank_orange[0] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[0] * (0.50 * dorsal_t)
    base_g = flank_orange[1] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[1] * (0.50 * dorsal_t)
    base_b = flank_orange[2] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[2] * (0.50 * dorsal_t)

    # 1. White Fur Zones in Canonical Rest Coordinates (AX, AY, AZ)
    white_mask = np.zeros((H, W), dtype=np.float32)

    # Underbelly, Chest, & Lower Throat
    throat_belly_line = 1.92 + 1.25 * np.clip((AX - 1.15) / 0.95, 0.0, 1.0)
    belly_w = np.clip((throat_belly_line - AZ) / 0.22, 0.0, 1.0) * (P == 1)
    white_mask = np.maximum(white_mask, belly_w * 0.95)

    # Wide White Tiger Cheek Ruffs (AX in [1.78, 2.35], |AY| > 0.13, AZ in [2.85, 3.44])
    cheek_w = np.clip((AX - 1.75) / 0.18, 0.0, 1.0) * np.clip((2.42 - AX) / 0.12, 0.0, 1.0) * np.clip((np.abs(AY) - 0.11) / 0.08, 0.0, 1.0) * np.clip((3.44 - AZ) / 0.12, 0.0, 1.0)
    white_mask = np.maximum(white_mask, cheek_w * 0.95)

    # Two Puffy White Whisker Cushions on front/sides of Muzzle & Chin (AX > 2.30, AZ < 3.39)
    whisker_w = np.clip((AX - 2.28) / 0.14, 0.0, 1.0) * np.clip((3.39 - AZ) / 0.06, 0.0, 1.0)
    white_mask = np.maximum(white_mask, whisker_w * 0.95)

    # White Supraorbital Eye Patches
    eyepatch_w = np.exp(-((AX - 2.22) / 0.11)**2 - ((np.abs(AY) - 0.17) / 0.07)**2 - ((AZ - 3.63) / 0.06)**2)
    white_mask = np.maximum(white_mask, np.clip(eyepatch_w * 1.5, 0.0, 0.96))

    # Paws & Inner Legs (strictly on leg/paw parts, NOT on tail!)
    paw_w = np.clip((0.32 - AZ) / 0.16, 0.0, 1.0) * ((P == 2) | (P == 3))
    white_mask = np.maximum(white_mask, paw_w * 0.92)
    inner_leg_w = (P == 2) * np.clip((1.55 - AZ) / 0.35, 0.0, 1.0) * np.clip((- NY * np.sign(AY)) + 0.20, 0.0, 1.0)
    white_mask = np.maximum(white_mask, inner_leg_w * 0.78)

    # Subtle cream underside on tail
    tail_underside = (P == 6) * np.clip((-NZ) * 0.7, 0.0, 0.65)
    white_mask = np.where(P == 6, tail_underside, white_mask)
    white_mask = np.where(P == 5, 0.94, white_mask)

    coat_r = base_r * (1.0 - white_mask) + cream_white[0] * white_mask
    coat_g = base_g * (1.0 - white_mask) + cream_white[1] * white_mask
    coat_b = base_b * (1.0 - white_mask) + cream_white[2] * white_mask

    # 2. Authentic Branching Black Bengal Tiger Stripes
    stripe_mask = np.zeros((H, W), dtype=np.float32)

    warp = 0.24 * np.sin(3.2 * AZ + 1.9 * AX) + 0.11 * np.cos(7.5 * AZ - 3.2 * AX) + 0.06 * np.sin(15.0 * AX + 9.0 * np.abs(AY))
    phase_body = (AX * 15.5) + (AZ * 1.8) + warp * 4.5
    body_stripes = np.clip((np.cos(phase_body) - 0.58) / 0.24, 0.0, 1.0)
    body_zone = np.clip((AZ - (throat_belly_line - 0.10)) / 0.28, 0.0, 1.0) * np.clip((1.88 - AX) / 0.18, 0.0, 1.0) * (P == 1)
    stripe_mask = np.maximum(stripe_mask, body_stripes * body_zone * (1.0 - 0.65 * white_mask))

    # Leg Stripes
    phase_leg = (AZ * 18.5) + (AX * 4.5) + 0.35 * np.sin(9.0 * AX + 6.0 * AY)
    leg_stripes = np.clip((np.cos(phase_leg) - 0.62) / 0.22, 0.0, 1.0)
    leg_zone = np.clip((1.75 - AZ) / 0.25, 0.0, 1.0) * np.clip((AZ - 0.26) / 0.14, 0.0, 1.0) * (P == 2)
    stripe_mask = np.maximum(stripe_mask, leg_stripes * leg_zone * 0.88)

    # Forehead Crown Stripes & Cheek Stripes
    phase_face = (AX * 32.0) + (np.abs(AY) * 18.0) + (AZ * 6.0)
    face_stripes = np.clip((np.cos(phase_face) - 0.58) / 0.22, 0.0, 1.0)
    crown_or_cheek = ((AX < 2.22) & (np.abs(AY) > 0.035)) | (np.abs(AY) > 0.095)
    face_zone = np.clip((AX - 1.75) / 0.12, 0.0, 1.0) * np.clip((2.42 - AX) / 0.10, 0.0, 1.0) * np.clip((AZ - 3.05) / 0.15, 0.0, 1.0) * crown_or_cheek * (P == 1) * (1.0 - np.clip(eyepatch_w * 1.5, 0.0, 1.0))
    stripe_mask = np.maximum(stripe_mask, face_stripes * face_zone * 0.90)

    # Black Eyeliner Rim
    eye_rim = np.exp(-((AX - 2.24) / 0.07)**2 - ((np.abs(AY) - 0.19) / 0.05)**2 - ((AZ - 3.55) / 0.05)**2)
    stripe_mask = np.maximum(stripe_mask, np.clip(eye_rim * 1.4, 0.0, 0.95) * (P == 1))

    # Whisker Dots on White Whisker Pads
    whisker_dots = np.clip((np.cos(AX * 65.0) * np.cos(AZ * 65.0) - 0.72) / 0.18, 0.0, 1.0) * whisker_w * (AX > 2.38) * (AZ > 3.27) * (np.abs(AY) > 0.04)
    stripe_mask = np.maximum(stripe_mask, whisker_dots * 0.85)

    # Tail Rings & Solid Black Tip
    ts = uv_tail_s
    tail_rings = np.clip((np.cos(ts * 9.5 * 2.0 * math.pi) - 0.25) / 0.30, 0.0, 1.0)
    tail_tip = np.clip((ts - 0.82) / 0.08, 0.0, 1.0)
    tail_stripe = np.maximum(tail_rings, tail_tip) * np.clip((ts - 0.06) / 0.08, 0.0, 1.0)
    stripe_mask = np.where(P == 6, tail_stripe, stripe_mask)

    # Outer Ears: Jet Black with White Central Spot
    is_outer_ear = (P == 4)
    ear_spot = np.exp(-((AX - 1.83) / 0.08)**2 - ((AZ - 3.70) / 0.09)**2)
    ear_white_spot = np.clip(ear_spot * 1.6, 0.0, 1.0)
    coat_r = np.where(is_outer_ear, cream_white[0] * ear_white_spot + stripe_black[0] * (1.0 - ear_white_spot), coat_r)
    coat_g = np.where(is_outer_ear, cream_white[1] * ear_white_spot + stripe_black[1] * (1.0 - ear_white_spot), coat_g)
    coat_b = np.where(is_outer_ear, cream_white[2] * ear_white_spot + stripe_black[2] * (1.0 - ear_white_spot), coat_b)
    stripe_mask = np.where(is_outer_ear, 0.0, stripe_mask)

    final_r = coat_r * (1.0 - stripe_mask) + stripe_black[0] * stripe_mask
    final_g = coat_g * (1.0 - stripe_mask) + stripe_black[1] * stripe_mask
    final_b = coat_b * (1.0 - stripe_mask) + stripe_black[2] * stripe_mask

    # 3. Neat Inverted-Triangle Feline Pink Nose Pad, Philtrum, & Mouth Cleft!
    # Inverted triangle width: narrow at bottom (AZ=3.36), wider at top (AZ=3.45)
    tri_half_w = np.clip(0.015 + 0.048 * (AZ - 3.36) / 0.09, 0.012, 0.062)
    nose_tip = (P == 1) & (AX > 2.66) & (AZ > 3.36) & (AZ < 3.455) & (np.abs(AY) < tri_half_w)
    nose_rim = (P == 1) & (AX > 2.64) & (~nose_tip) & (AZ > 3.345) & (AZ < 3.468) & (np.abs(AY) < tri_half_w + 0.018)
    philtrum_mouth = (P == 1) & (AX > 2.50) & (AZ > 3.23) & (AZ <= 3.35) & ((np.abs(AY) < 0.014) | ((AZ < 3.265) & (np.abs(AY) < 0.085)))

    final_r = np.where(nose_tip, nose_pink[0], np.where(nose_rim | philtrum_mouth, 0.07, final_r))
    final_g = np.where(nose_tip, nose_pink[1], np.where(nose_rim | philtrum_mouth, 0.05, final_g))
    final_b = np.where(nose_tip, nose_pink[2], np.where(nose_rim | philtrum_mouth, 0.05, final_b))

    # 4. Multiply by Real Photographic Fur Hair-Strand Micro-Detail!
    shade = np.where(P == 6, np.clip(fur_detail, 0.82, 1.18), fur_detail * macro_ao)
    final_r = np.clip(final_r * shade, 0.0, 1.0)
    final_g = np.clip(final_g * shade, 0.0, 1.0)
    final_b = np.clip(final_b * shade, 0.0, 1.0)

    # 5. Preserve & Golden-Tint Photorealistic Eyes
    uu_norm, vv_norm = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    eye_uv_mask = (P == 7) | ((vv_norm > 0.76) & (vv_norm < 0.96) & (((uu_norm > 0.11) & (uu_norm < 0.25)) | ((uu_norm > 0.45) & (uu_norm < 0.58))))
    orig_r, orig_g, orig_b = orig_pixels[:, :, 0], orig_pixels[:, :, 1], orig_pixels[:, :, 2]
    final_r = np.where(eye_uv_mask, np.clip(orig_r * 1.45, 0.0, 1.0), final_r)
    final_g = np.where(eye_uv_mask, np.clip(orig_g * 1.15, 0.0, 1.0), final_g)
    final_b = np.where(eye_uv_mask, np.clip(orig_b * 0.45, 0.0, 1.0), final_b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = final_r
    out_pixels[:, :, 1] = final_g
    out_pixels[:, :, 2] = final_b
    out_pixels[:, :, 3] = 1.0

    tiger_img = bpy.data.images.new("TigerPBRTex", width=W, height=H, alpha=False)
    tiger_img.pixels[:] = out_pixels.ravel().tolist()
    tiger_tex_path = os.path.join(SCRATCH_DIR, "tiger_tex.png")
    tiger_img.filepath_raw = tiger_tex_path
    tiger_img.file_format = 'PNG'
    tiger_img.save()
    tiger_img.pack()

    mat = obj.data.materials[0]
    mat.name = "RoyalBengalTigerMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            node.image = tiger_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs:
                node.inputs['Roughness'].default_value = 0.78
            if 'Metallic' in node.inputs:
                node.inputs['Metallic'].default_value = 0.02

    bm.free()
    obj.name = "RoyalBengalTiger"
    bpy.ops.export_scene.gltf(filepath=OUT_TIGER_GLB, export_format='GLB')
    print(f"✓ Exported final Royal Bengal Tiger to {OUT_TIGER_GLB}")

if __name__ == "__main__":
    build_realistic_tiger()
