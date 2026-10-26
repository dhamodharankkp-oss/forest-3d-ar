import bpy
import bmesh
import math
import os
import numpy as np

MODELS_DIR = r"D:\tecplore\assets\models"
DEER_GLB = os.path.join(MODELS_DIR, "deer.glb")
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

def prepare_base_mammal():
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

    return obj, bm, orig_pixels, W, H, vert_part, pos_groups, anat_coords, z_samples, leg_curves

def rasterize_uv_attributes(bm, W, H, vert_part, anat_coords):
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
        'ear_outer': 4, 'ear_inner': 5, 'tail': 6, 'eye': 7, 'tusk': 8
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

        p_info = vert_part.get(v0, ('body', 0))
        p_code = part_code_map.get(p_info[0], 1)
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

    return uv_ax, uv_ay, uv_az, uv_nx, uv_ny, uv_nz, uv_part, uv_tail_s

# =============================================================================
# 1. ROYAL BENGAL TIGER (tiger.glb)
# =============================================================================
def build_tiger():
    obj, bm, orig_pixels, W, H, vert_part, pos_groups, anat_coords, z_samples, leg_curves = prepare_base_mammal()

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
            orig_cx.append(mx); orig_cy.append(my); orig_rad.append(max(mr, 0.03))

        for v in tail_verts:
            s = max(0.0, min(1.0, (z_max - v.co.z) / (z_max - z_min + 1e-6)))
            ocx = float(np.interp(s, s_bins, orig_cx))
            ocy = float(np.interp(s, s_bins, orig_cy))
            orad = float(np.interp(s, s_bins, orig_rad))
            ux, uy = (v.co.x - ocx) / orad, (v.co.y - ocy) / orad
            unorm = math.hypot(ux, uy)
            if unorm > 1e-4:
                ux /= unorm; uy /= unorm
            tip_round = math.sqrt(max(0.04, 1.0 - max(0.0, (s - 0.88) / 0.12) ** 2))
            target_r = (0.115 * (1.0 - 0.25 * s)) * tip_round
            w_tail = smoothstep(0.0, 0.15, s)
            tx = -1.42 - 1.55 * (s ** 0.95)
            tz = 2.48 - 1.85 * math.sin(s * 0.72 * math.pi) + 0.30 * (s ** 2.4)
            s2 = min(1.0, s + 0.02)
            tx2 = -1.42 - 1.55 * (s2 ** 0.95)
            tz2 = 2.48 - 1.85 * math.sin(s2 * 0.72 * math.pi) + 0.30 * (s2 ** 2.4)
            tang_x, tang_z = tx2 - tx, tz2 - tz
            tlen = math.hypot(tang_x, tang_z) or 1.0
            nx_xz, nz_xz = -tang_z / tlen, tang_x / tlen
            v.co.x = v.co.x * (1.0 - w_tail) + (tx + ux * target_r * nx_xz) * w_tail
            v.co.y = v.co.y * (1.0 - w_tail) + (uy * target_r) * w_tail
            v.co.z = v.co.z * (1.0 - w_tail) + (tz + ux * target_r * nz_xz) * w_tail
            vert_part[v] = ('tail', s)

    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.20, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.55 * w_ear)
            y = yb + (y - yb) * (1.0 - 0.52 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.15 * w_ear) + 0.06 * w_ear

        w_head = smoothstep(1.70, 2.00, x) * smoothstep(2.75, 3.10, z)
        if w_head > 0.0:
            if x > 2.10:
                x = 2.10 + (x - 2.10) * (1.0 - 0.35 * w_head)
            w_crown = math.exp(-((x - 1.98) / 0.22) ** 2) * math.exp(-(y / 0.18) ** 2) * smoothstep(3.38, 3.52, z)
            z += 0.14 * w_crown * w_head
            w_eye_socket = math.exp(-((x - 2.18) / 0.14) ** 2) * math.exp(-((z - 3.54) / 0.12) ** 2)
            y *= (1.0 - 0.14 * w_eye_socket)
            x += 0.04 * w_eye_socket * (1.0 - smoothstep(0.10, 0.24, abs(y)))
            w_cheek_zone = (1.0 - smoothstep(3.36, 3.52, z)) * (1.0 - 0.55 * smoothstep(2.15, 2.48, x))
            y *= (1.0 + 0.34 * w_head * w_cheek_zone)
            w_ruff = math.exp(-((x - 1.98) / 0.15) ** 2) * math.exp(-((z - 3.22) / 0.18) ** 2) * smoothstep(0.08, 0.18, abs(y))
            y += math.copysign(0.12 * w_ruff, y)
            z -= 0.15 * w_head * smoothstep(2.05, 2.52, x)
            if z < 3.36:
                z -= 0.14 * w_head * smoothstep(1.95, 2.35, x) * smoothstep(3.36, 3.18, z)

        w_neck_rot = smoothstep(0.85, 1.55, x) * smoothstep(1.55, 2.15, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.10, 2.30
            ang1 = math.radians(-27.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1)
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)

        w_neck = smoothstep(1.05, 1.40, x) * (1.0 - smoothstep(1.90, 2.20, x)) * smoothstep(1.65, 2.05, z)
        if w_neck > 0.0:
            y *= (1.0 + 0.30 * w_neck)
            if z < 2.45:
                z -= 0.14 * w_neck * smoothstep(2.45, 1.85, z)

        if part in ('front_leg', 'rear_leg', 'paw') and z < 1.58:
            for idxs, cx_arr, cy_arr in leg_curves:
                if isl_idx in idxs:
                    cx = float(np.interp(z, z_samples, cx_arr))
                    cy = float(np.interp(z, z_samples, cy_arr))
                    dx, dy = x - cx, y - cy
                    w_leg = 1.0 - smoothstep(1.10, 1.55, z)
                    thick = 1.0 + 0.56 * w_leg
                    w_paw = 1.0 - smoothstep(0.02, 0.18, z)
                    x = cx + dx * (thick + 0.24 * w_paw) + 0.035 * w_paw
                    y = cy + dy * (thick + 0.20 * w_paw)
                    break

        x *= 1.10
        y *= 1.24
        w_chest = math.exp(-((x - 0.35) / 0.85) ** 2) * smoothstep(1.35, 1.85, z) * (1.0 - smoothstep(2.05, 2.45, z))
        z = (z - 0.12 * w_chest) * 0.82
        v.co.x, v.co.y, v.co.z = x, y, max(0.0, z)

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

    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.60, 1.40)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.82 + 0.25 * (lum_smooth / (lum_macro + 0.05)), 0.68, 1.14)

    AX, AY, AZ, NX, NY, NZ, P, ts = rasterize_uv_attributes(bm, W, H, vert_part, anat_coords)

    spine_dark_orange = np.array([0.82, 0.34, 0.04], dtype=np.float32)
    flank_orange      = np.array([0.93, 0.46, 0.09], dtype=np.float32)
    cream_white       = np.array([0.97, 0.95, 0.90], dtype=np.float32)
    stripe_black      = np.array([0.06, 0.04, 0.03], dtype=np.float32)
    nose_pink         = np.array([0.85, 0.43, 0.39], dtype=np.float32)

    dorsal_t = np.clip((AZ - 2.35) / 0.55, 0.0, 1.0) * np.clip(NZ, 0.0, 1.0)
    base_r = flank_orange[0] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[0] * (0.50 * dorsal_t)
    base_g = flank_orange[1] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[1] * (0.50 * dorsal_t)
    base_b = flank_orange[2] * (1.0 - 0.50 * dorsal_t) + spine_dark_orange[2] * (0.50 * dorsal_t)

    white_mask = np.zeros((H, W), dtype=np.float32)
    throat_belly_line = 1.92 + 1.25 * np.clip((AX - 1.15) / 0.95, 0.0, 1.0)
    belly_w = np.clip((throat_belly_line - AZ) / 0.22, 0.0, 1.0) * (P == 1)
    white_mask = np.maximum(white_mask, belly_w * 0.95)

    cheek_w = np.clip((AX - 1.75) / 0.18, 0.0, 1.0) * np.clip((2.42 - AX) / 0.12, 0.0, 1.0) * np.clip((np.abs(AY) - 0.11) / 0.08, 0.0, 1.0) * np.clip((3.44 - AZ) / 0.12, 0.0, 1.0)
    white_mask = np.maximum(white_mask, cheek_w * 0.95)

    whisker_w = np.clip((AX - 2.28) / 0.14, 0.0, 1.0) * np.clip((3.39 - AZ) / 0.06, 0.0, 1.0)
    white_mask = np.maximum(white_mask, whisker_w * 0.95)

    eyepatch_w = np.exp(-((AX - 2.22) / 0.11)**2 - ((np.abs(AY) - 0.17) / 0.07)**2 - ((AZ - 3.63) / 0.06)**2)
    white_mask = np.maximum(white_mask, np.clip(eyepatch_w * 1.5, 0.0, 0.96))

    paw_w = np.clip((0.32 - AZ) / 0.16, 0.0, 1.0) * ((P == 2) | (P == 3))
    white_mask = np.maximum(white_mask, paw_w * 0.92)
    inner_leg_w = (P == 2) * np.clip((1.55 - AZ) / 0.35, 0.0, 1.0) * np.clip((- NY * np.sign(AY)) + 0.20, 0.0, 1.0)
    white_mask = np.maximum(white_mask, inner_leg_w * 0.78)

    tail_underside = (P == 6) * np.clip((-NZ) * 0.7, 0.0, 0.65)
    white_mask = np.where(P == 6, tail_underside, white_mask)
    white_mask = np.where(P == 5, 0.94, white_mask)

    coat_r = base_r * (1.0 - white_mask) + cream_white[0] * white_mask
    coat_g = base_g * (1.0 - white_mask) + cream_white[1] * white_mask
    coat_b = base_b * (1.0 - white_mask) + cream_white[2] * white_mask

    stripe_mask = np.zeros((H, W), dtype=np.float32)
    warp = 0.24 * np.sin(3.2 * AZ + 1.9 * AX) + 0.11 * np.cos(7.5 * AZ - 3.2 * AX) + 0.06 * np.sin(15.0 * AX + 9.0 * np.abs(AY))
    phase_body = (AX * 15.5) + (AZ * 1.8) + warp * 4.5
    body_stripes = np.clip((np.cos(phase_body) - 0.58) / 0.24, 0.0, 1.0)
    body_zone = np.clip((AZ - (throat_belly_line - 0.10)) / 0.28, 0.0, 1.0) * np.clip((1.88 - AX) / 0.18, 0.0, 1.0) * (P == 1)
    stripe_mask = np.maximum(stripe_mask, body_stripes * body_zone * (1.0 - 0.65 * white_mask))

    phase_leg = (AZ * 18.5) + (AX * 4.5) + 0.35 * np.sin(9.0 * AX + 6.0 * AY)
    leg_stripes = np.clip((np.cos(phase_leg) - 0.62) / 0.22, 0.0, 1.0)
    leg_zone = np.clip((1.75 - AZ) / 0.25, 0.0, 1.0) * np.clip((AZ - 0.26) / 0.14, 0.0, 1.0) * (P == 2)
    stripe_mask = np.maximum(stripe_mask, leg_stripes * leg_zone * 0.88)

    phase_face = (AX * 32.0) + (np.abs(AY) * 18.0) + (AZ * 6.0)
    face_stripes = np.clip((np.cos(phase_face) - 0.58) / 0.22, 0.0, 1.0)
    crown_or_cheek = ((AX < 2.22) & (np.abs(AY) > 0.035)) | (np.abs(AY) > 0.095)
    face_zone = np.clip((AX - 1.75) / 0.12, 0.0, 1.0) * np.clip((2.42 - AX) / 0.10, 0.0, 1.0) * np.clip((AZ - 3.05) / 0.15, 0.0, 1.0) * crown_or_cheek * (P == 1) * (1.0 - np.clip(eyepatch_w * 1.5, 0.0, 1.0))
    stripe_mask = np.maximum(stripe_mask, face_stripes * face_zone * 0.90)

    eye_rim = np.exp(-((AX - 2.24) / 0.07)**2 - ((np.abs(AY) - 0.19) / 0.05)**2 - ((AZ - 3.55) / 0.05)**2)
    stripe_mask = np.maximum(stripe_mask, np.clip(eye_rim * 1.4, 0.0, 0.95) * (P == 1))

    whisker_dots = np.clip((np.cos(AX * 65.0) * np.cos(AZ * 65.0) - 0.72) / 0.18, 0.0, 1.0) * whisker_w * (AX > 2.38) * (AZ > 3.27) * (np.abs(AY) > 0.04)
    stripe_mask = np.maximum(stripe_mask, whisker_dots * 0.85)

    tail_rings = np.clip((np.cos(ts * 9.5 * 2.0 * math.pi) - 0.25) / 0.30, 0.0, 1.0)
    tail_tip = np.clip((ts - 0.82) / 0.08, 0.0, 1.0)
    tail_stripe = np.maximum(tail_rings, tail_tip) * np.clip((ts - 0.06) / 0.08, 0.0, 1.0)
    stripe_mask = np.where(P == 6, tail_stripe, stripe_mask)

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

    tri_half_w = np.clip(0.015 + 0.048 * (AZ - 3.36) / 0.09, 0.012, 0.062)
    nose_tip = (P == 1) & (AX > 2.66) & (AZ > 3.36) & (AZ < 3.455) & (np.abs(AY) < tri_half_w)
    nose_rim = (P == 1) & (AX > 2.64) & (~nose_tip) & (AZ > 3.345) & (AZ < 3.468) & (np.abs(AY) < tri_half_w + 0.018)
    philtrum_mouth = (P == 1) & (AX > 2.50) & (AZ > 3.23) & (AZ <= 3.35) & ((np.abs(AY) < 0.014) | ((AZ < 3.265) & (np.abs(AY) < 0.085)))

    final_r = np.where(nose_tip, nose_pink[0], np.where(nose_rim | philtrum_mouth, 0.07, final_r))
    final_g = np.where(nose_tip, nose_pink[1], np.where(nose_rim | philtrum_mouth, 0.05, final_g))
    final_b = np.where(nose_tip, nose_pink[2], np.where(nose_rim | philtrum_mouth, 0.05, final_b))

    shade = np.where(P == 6, np.clip(fur_detail, 0.82, 1.18), fur_detail * macro_ao)
    final_r = np.clip(final_r * shade, 0.0, 1.0)
    final_g = np.clip(final_g * shade, 0.0, 1.0)
    final_b = np.clip(final_b * shade, 0.0, 1.0)

    # Strictly use P == 7 for eye_uv_mask so there is ZERO bleed onto the rear flank!
    eye_uv_mask = (P == 7)
    orig_r, orig_g, orig_b = orig_pixels[:, :, 0], orig_pixels[:, :, 1], orig_pixels[:, :, 2]
    final_r = np.where(eye_uv_mask, np.clip(orig_r * 1.45, 0.0, 1.0), final_r)
    final_g = np.where(eye_uv_mask, np.clip(orig_g * 1.15, 0.0, 1.0), final_g)
    final_b = np.where(eye_uv_mask, np.clip(orig_b * 0.45, 0.0, 1.0), final_b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = final_r; out_pixels[:, :, 1] = final_g; out_pixels[:, :, 2] = final_b

    tiger_img = bpy.data.images.new("TigerPBRTex", width=W, height=H, alpha=False)
    tiger_img.pixels[:] = out_pixels.ravel().tolist()
    tiger_img.filepath_raw = os.path.join(SCRATCH_DIR, "tiger_tex.png")
    tiger_img.file_format = 'PNG'
    tiger_img.save(); tiger_img.pack()

    mat = obj.data.materials[0]
    mat.name = "RoyalBengalTigerMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE': node.image = tiger_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs: node.inputs['Roughness'].default_value = 0.78

    bm.free()
    obj.name = "RoyalBengalTiger"
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODELS_DIR, "tiger.glb"), export_format='GLB')
    print("✓ Exported tiger.glb")


# =============================================================================
# 2. INDIAN WILD BOAR (boar.glb)
# =============================================================================
def build_boar():
    obj, bm, orig_pixels, W, H, vert_part, pos_groups, anat_coords, z_samples, leg_curves = prepare_base_mammal()

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

    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.21, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.35 * w_ear) + 0.05 * w_ear
            y = yb + (y - yb) * (1.0 - 0.35 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.15 * w_ear)

        w_head = smoothstep(1.65, 1.98, x) * smoothstep(2.70, 3.05, z)
        if w_head > 0.0:
            w_snout = smoothstep(2.10, 2.65, x)
            y *= (1.0 + w_head * (0.35 - 0.12 * w_snout))
            if z < 3.40:
                z -= 0.20 * w_head * (1.0 - 0.35 * w_snout)
            else:
                z -= 0.12 * w_head * w_snout
            if x > 2.66:
                x = 2.66 + (x - 2.66) * 0.25

        w_neck_rot = smoothstep(0.75, 1.50, x) * smoothstep(1.65, 2.15, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.05, 2.25
            ang1 = math.radians(-36.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1)
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)

        # Keep neck widening strictly above the shoulder-leg seam (z > 2.05) so there is ZERO shoulder flare!
        w_neck = smoothstep(0.85, 1.35, x) * (1.0 - smoothstep(1.85, 2.25, x)) * smoothstep(2.00, 2.35, z)
        if w_neck > 0.0:
            y *= (1.0 + 0.24 * w_neck)

        if part in ('front_leg', 'rear_leg', 'paw') and z < 1.58:
            for idxs, cx_arr, cy_arr in leg_curves:
                if isl_idx in idxs:
                    cx = float(np.interp(z, z_samples, cx_arr))
                    cy = float(np.interp(z, z_samples, cy_arr))
                    dx, dy = x - cx, y - cy
                    w_leg = 1.0 - smoothstep(1.10, 1.55, z)
                    thick = 1.0 + 0.50 * w_leg
                    x = cx + dx * thick
                    y = cy + dy * thick
                    break

        x *= 0.96
        y *= 1.34
        w_torso_top = smoothstep(2.15, 2.55, z) * smoothstep(-1.3, -0.8, x) * (1.0 - smoothstep(1.5, 2.0, x))
        shoulder_hump = math.exp(-((x - 0.78) / 0.55) ** 2) * 0.22 * w_torso_top
        dorsal_crest = math.exp(-(y / 0.10) ** 2) * 0.12 * w_torso_top * smoothstep(-0.6, 0.4, x)
        w_belly = math.exp(-((x - 0.15) / 0.95) ** 2) * smoothstep(1.35, 1.80, z) * (1.0 - smoothstep(2.05, 2.40, z))
        z = (z + shoulder_hump + dorsal_crest - 0.18 * w_belly) * 0.68
        v.co.x, v.co.y, v.co.z = x, y, max(0.0, z)

    for key, v_list in pos_groups.items():
        if len(v_list) > 1:
            mx = sum(v.co.x for v in v_list) / len(v_list)
            my = sum(v.co.y for v in v_list) / len(v_list)
            mz = sum(v.co.z for v in v_list) / len(v_list)
            for v in v_list:
                v.co.x, v.co.y, v.co.z = mx, my, mz

    # Prominent Upward-Curving Ivory Tusks protruding from lower jaw
    snout_verts = [v for v in bm.verts if anat_coords.get(v, (0,0,0))[0] > 2.55]
    sx = sum(v.co.x for v in snout_verts) / len(snout_verts)
    sz = sum(v.co.z for v in snout_verts) / len(snout_verts)

    uv_layer = bm.loops.layers.uv.active
    for side in (-1.0, 1.0):
        rings = []
        n_seg = 8
        for r_idx in range(6):
            t = r_idx / 5.0
            rad = 0.042 * (1.0 - 0.85 * t)
            rcx = sx - 0.12 + 0.14 * t
            rcy = side * (0.11 + 0.13 * t)
            rcz = sz - 0.05 + 0.26 * (t ** 1.25)
            ring_v = []
            for k in range(n_seg):
                ang = k * 2.0 * math.pi / n_seg
                vx = rcx + rad * math.cos(ang) * 0.7
                vy = rcy + rad * math.sin(ang) * 0.7
                vz = rcz + rad * math.cos(ang) * 0.4
                nv = bm.verts.new((vx, vy, vz))
                anat_coords[nv] = (3.0, side * 0.5, 3.0)
                vert_part[nv] = ('tusk', 99)
                ring_v.append(nv)
            rings.append(ring_v)
        for r_idx in range(5):
            r0, r1 = rings[r_idx], rings[r_idx + 1]
            for k in range(n_seg):
                k1 = (k + 1) % n_seg
                for tri in [(r0[k], r0[k1], r1[k1]), (r0[k], r1[k1], r1[k])]:
                    f = bm.faces.new(tri)
                    for loop in f.loops:
                        loop[uv_layer].uv = (0.94, 0.94)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.update()

    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.52, 1.48)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.80 + 0.28 * (lum_smooth / (lum_macro + 0.05)), 0.62, 1.15)

    AX, AY, AZ, NX, NY, NZ, P, ts = rasterize_uv_attributes(bm, W, H, vert_part, anat_coords)

    dark_boar   = np.array([0.20, 0.15, 0.11], dtype=np.float32)
    black_mane  = np.array([0.07, 0.05, 0.04], dtype=np.float32)
    grizzle_gry = np.array([0.50, 0.45, 0.38], dtype=np.float32)
    snout_pink  = np.array([0.58, 0.36, 0.32], dtype=np.float32)

    mane_zone = np.clip((AZ - 2.65) / 0.25, 0.0, 1.0) * np.exp(-(AY / 0.15) ** 2)
    sock_zone = np.clip((0.95 - AZ) / 0.35, 0.0, 1.0) * ((P == 2) | (P == 3))
    dark_mask = np.clip(mane_zone + sock_zone, 0.0, 1.0)

    grizzle_zone = np.clip((fur_detail - 1.04) * 3.2, 0.0, 1.0) * (1.0 - 0.7 * dark_mask)

    r = dark_boar[0] * (1.0 - dark_mask) + black_mane[0] * dark_mask
    g = dark_boar[1] * (1.0 - dark_mask) + black_mane[1] * dark_mask
    b = dark_boar[2] * (1.0 - dark_mask) + black_mane[2] * dark_mask

    r = r * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[0] * (0.55 * grizzle_zone)
    g = g * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[1] * (0.55 * grizzle_zone)
    b = b * (1.0 - 0.55 * grizzle_zone) + grizzle_gry[2] * (0.55 * grizzle_zone)

    disc_zone = (P == 1) & (AX > 2.60) & (AZ > 3.24) & (AZ < 3.49)
    nostril_zone = disc_zone & (AX > 2.64) & (np.abs(np.abs(AY) - 0.045) < 0.024) & (AZ > 3.33) & (AZ < 3.42)
    r = np.where(nostril_zone, 0.06, np.where(disc_zone, snout_pink[0], r))
    g = np.where(nostril_zone, 0.04, np.where(disc_zone, snout_pink[1], g))
    b = np.where(nostril_zone, 0.04, np.where(disc_zone, snout_pink[2], b))

    shade = np.clip(fur_detail * 1.15 - 0.15, 0.45, 1.50) * macro_ao
    r = np.clip(r * shade, 0.0, 1.0)
    g = np.clip(g * shade, 0.0, 1.0)
    b = np.clip(b * shade, 0.0, 1.0)

    # Ivory Tusks
    uu_norm, vv_norm = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    tusk_mask = (P == 8) | ((uu_norm > 0.88) & (vv_norm > 0.88))
    r = np.where(tusk_mask, 0.96, r)
    g = np.where(tusk_mask, 0.93, g)
    b = np.where(tusk_mask, 0.84, b)

    # Strictly use P == 7 for eye_uv_mask so there is ZERO orange triangle bleed on the rear flank!
    eye_uv_mask = (P == 7)
    r = np.where(eye_uv_mask, orig_pixels[:, :, 0] * 0.9, r)
    g = np.where(eye_uv_mask, orig_pixels[:, :, 1] * 0.8, g)
    b = np.where(eye_uv_mask, orig_pixels[:, :, 2] * 0.6, b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = r; out_pixels[:, :, 1] = g; out_pixels[:, :, 2] = b

    boar_img = bpy.data.images.new("BoarPBRTex", width=W, height=H, alpha=False)
    boar_img.pixels[:] = out_pixels.ravel().tolist()
    boar_img.filepath_raw = os.path.join(SCRATCH_DIR, "boar_tex.png")
    boar_img.file_format = 'PNG'
    boar_img.save(); boar_img.pack()

    mat = obj.data.materials[0]
    mat.name = "IndianWildBoarMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE': node.image = boar_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs: node.inputs['Roughness'].default_value = 0.88

    bm.free()
    obj.name = "IndianWildBoar"
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODELS_DIR, "boar.glb"), export_format='GLB')
    print("✓ Exported boar.glb")


# =============================================================================
# 3. INDIAN GIANT FLYING SQUIRREL (squirrel.glb)
# =============================================================================
def build_squirrel():
    obj, bm, orig_pixels, W, H, vert_part, pos_groups, anat_coords, z_samples, leg_curves = prepare_base_mammal()

    # Magnificent Fluffy Plumed Squirrel Tail arching gracefully behind and above the back
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
            orig_cx.append(mx); orig_cy.append(my); orig_rad.append(max(mr, 0.03))

        for v in tail_verts:
            s = max(0.0, min(1.0, (z_max - v.co.z) / (z_max - z_min + 1e-6)))
            ocx = float(np.interp(s, s_bins, orig_cx))
            ocy = float(np.interp(s, s_bins, orig_cy))
            orad = float(np.interp(s, s_bins, orig_rad))
            ux, uy = (v.co.x - ocx) / orad, (v.co.y - ocy) / orad
            unorm = math.hypot(ux, uy)
            if unorm > 1e-4:
                ux /= unorm; uy /= unorm

            plume_env = math.sin(max(0.08, min(0.95, s)) * math.pi) ** 0.52
            target_r = 0.34 * plume_env
            w_tail = smoothstep(0.0, 0.14, s)

            tx = -1.35 - 1.75 * (s ** 0.85)
            tz = 2.48 + 0.72 * math.sin(s * 0.85 * math.pi)
            v.co.x = v.co.x * (1.0 - w_tail) + (tx + ux * target_r * 0.45) * w_tail
            v.co.y = v.co.y * (1.0 - w_tail) + (uy * target_r * 1.15) * w_tail
            v.co.z = v.co.z * (1.0 - w_tail) + (tz + ux * target_r * 0.90) * w_tail
            vert_part[v] = ('tail', s)

    for v in bm.verts:
        part, isl_idx = vert_part.get(v, ('body', 0))
        x, y, z = v.co.x, v.co.y, v.co.z

        w_ear = smoothstep(0.21, 0.27, abs(y)) * smoothstep(3.48, 3.56, z) * smoothstep(1.45, 1.65, x) * (1.0 - smoothstep(1.98, 2.12, x))
        if w_ear > 0.0:
            yb = math.copysign(0.20, y)
            xb, zb = 1.82, 3.54
            x = xb + (x - xb) * (1.0 + 0.45 * w_ear)
            y = yb + (y - yb) * (1.0 - 0.55 * w_ear)
            z = zb + (z - zb) * (1.0 - 0.32 * w_ear)

        w_head = smoothstep(1.68, 2.00, x) * smoothstep(2.75, 3.10, z)
        if w_head > 0.0:
            if x > 2.02:
                x = 2.02 + (x - 2.02) * (1.0 - 0.48 * w_head)
            y *= (1.0 + 0.25 * w_head)
            z -= 0.14 * w_head * smoothstep(2.00, 2.45, x)

        w_neck_rot = smoothstep(0.75, 1.50, x) * smoothstep(1.60, 2.15, z)
        if w_neck_rot > 0.0:
            xs, zs = 1.05, 2.25
            ang1 = math.radians(-30.0) * w_neck_rot
            dx, dz = x - xs, z - zs
            x = xs + dx * math.cos(ang1) - dz * math.sin(ang1) - 0.18 * w_neck_rot
            z = zs + dx * math.sin(ang1) + dz * math.cos(ang1)

        # Smooth aerodynamic Patagium gliding membrane along the mid-flank (z in [1.95, 2.45])
        w_patagium = math.exp(-((x - (-0.05)) / 0.72) ** 2) * math.exp(-((z - 2.18) / 0.22) ** 2) * smoothstep(0.22, 0.38, abs(y))
        if w_patagium > 0.0:
            y += math.copysign(0.28 * w_patagium, y)

        if part in ('front_leg', 'rear_leg', 'paw') and z < 1.58:
            for idxs, cx_arr, cy_arr in leg_curves:
                if isl_idx in idxs:
                    cx = float(np.interp(z, z_samples, cx_arr))
                    cy = float(np.interp(z, z_samples, cy_arr))
                    dx, dy = x - cx, y - cy
                    w_leg = 1.0 - smoothstep(1.10, 1.55, z)
                    thick = 1.0 + 0.45 * w_leg
                    x = cx + dx * thick
                    y = cy + dy * thick
                    break

        w_arch = math.exp(-((x - (-0.15)) / 0.85) ** 2) * smoothstep(2.10, 2.55, z)
        z += 0.18 * w_arch

        # Smoothly scale Z height without folding!
        y *= 1.24
        z *= 0.62
        v.co.x, v.co.y, v.co.z = x, y, max(0.0, z)

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

    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=8)
    fur_detail = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.55, 1.45)
    lum_macro = box_blur_2d(lum, r=28)
    macro_ao = np.clip(0.80 + 0.28 * (lum_smooth / (lum_macro + 0.05)), 0.65, 1.15)

    AX, AY, AZ, NX, NY, NZ, P, ts = rasterize_uv_attributes(bm, W, H, vert_part, anat_coords)

    maroon_back  = np.array([0.46, 0.13, 0.08], dtype=np.float32)
    russet_flank = np.array([0.68, 0.25, 0.12], dtype=np.float32)
    cream_belly  = np.array([0.94, 0.86, 0.74], dtype=np.float32)
    dark_tip     = np.array([0.14, 0.06, 0.05], dtype=np.float32)

    dorsal_t = np.clip((AZ - 2.15) / 0.55, 0.0, 1.0)
    r = russet_flank[0] * (1.0 - dorsal_t) + maroon_back[0] * dorsal_t
    g = russet_flank[1] * (1.0 - dorsal_t) + maroon_back[1] * dorsal_t
    b = russet_flank[2] * (1.0 - dorsal_t) + maroon_back[2] * dorsal_t

    throat_line = 1.95 + 1.25 * np.clip((AX - 1.15) / 0.95, 0.0, 1.0)
    belly_w = np.clip((throat_line - AZ) / 0.24, 0.0, 1.0) * (P == 1)
    r = r * (1.0 - belly_w) + cream_belly[0] * belly_w
    g = g * (1.0 - belly_w) + cream_belly[1] * belly_w
    b = b * (1.0 - belly_w) + cream_belly[2] * belly_w

    dark_zone = np.clip((0.55 - AZ) / 0.25, 0.0, 1.0) * ((P == 2) | (P == 3))
    dark_zone = np.where(P == 4, 0.85, dark_zone)
    dark_zone = np.where(P == 6, np.clip((ts - 0.35) / 0.45, 0.15, 0.92), dark_zone)
    r = r * (1.0 - dark_zone) + dark_tip[0] * dark_zone
    g = g * (1.0 - dark_zone) + dark_tip[1] * dark_zone
    b = b * (1.0 - dark_zone) + dark_tip[2] * dark_zone

    nose_tip = (P == 1) & (AX > 2.63) & (np.abs(AY) < 0.07) & (AZ > 3.33) & (AZ < 3.46)
    r = np.where(nose_tip, 0.86, r)
    g = np.where(nose_tip, 0.48, g)
    b = np.where(nose_tip, 0.46, b)

    shade = np.where(P == 6, np.clip(fur_detail, 0.78, 1.22), fur_detail * macro_ao)
    r = np.clip(r * shade, 0.0, 1.0)
    g = np.clip(g * shade, 0.0, 1.0)
    b = np.clip(b * shade, 0.0, 1.0)

    # Strictly use P == 7 for eye_uv_mask
    eye_uv_mask = (P == 7)
    r = np.where(eye_uv_mask, orig_pixels[:, :, 0] * 0.35, r)
    g = np.where(eye_uv_mask, orig_pixels[:, :, 1] * 0.25, g)
    b = np.where(eye_uv_mask, orig_pixels[:, :, 2] * 0.25, b)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = r; out_pixels[:, :, 1] = g; out_pixels[:, :, 2] = b

    sq_img = bpy.data.images.new("SquirrelPBRTex", width=W, height=H, alpha=False)
    sq_img.pixels[:] = out_pixels.ravel().tolist()
    sq_img.filepath_raw = os.path.join(SCRATCH_DIR, "squirrel_tex.png")
    sq_img.file_format = 'PNG'
    sq_img.save(); sq_img.pack()

    mat = obj.data.materials[0]
    mat.name = "GiantFlyingSquirrelMat"
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE': node.image = sq_img
        elif node.type == 'BSDF_PRINCIPLED':
            if 'Roughness' in node.inputs: node.inputs['Roughness'].default_value = 0.76

    bm.free()
    obj.name = "IndianGiantFlyingSquirrel"
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODELS_DIR, "squirrel.glb"), export_format='GLB')
    print("✓ Exported squirrel.glb")


# =============================================================================
# 4. PHOTOREALISTIC INDIAN PEACOCK (peacock.glb)
# =============================================================================
def build_peacock():
    # First load photographic fiber micro-detail from deer_texture.jpg for realistic feather barbules
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=DEER_GLB)
    orig_img = bpy.data.images.get("Image_0")
    W, H = 1024, 1024
    orig_pixels = np.array(orig_img.pixels[:], dtype=np.float32).reshape((H, W, 4))
    lum = 0.299 * orig_pixels[:, :, 0] + 0.587 * orig_pixels[:, :, 1] + 0.114 * orig_pixels[:, :, 2]
    lum_smooth = box_blur_2d(lum, r=6)
    feather_micro = np.clip((lum + 0.03) / (lum_smooth + 0.03), 0.65, 1.35)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh = bpy.data.meshes.new("IndianPeacockMesh")
    obj = bpy.data.objects.new("IndianPeacock", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    def add_lofted_tube(spine_pts, radii_x, radii_y, u_range, v_range, n_seg=24, cap_ends=True):
        rings = []
        n_rings = len(spine_pts)
        for i in range(n_rings):
            px, py, pz = spine_pts[i]
            rx, ry = radii_x[i], radii_y[i]
            # Compute tangent along spine
            i0 = max(0, i - 1)
            i1 = min(n_rings - 1, i + 1)
            tx = spine_pts[i1][0] - spine_pts[i0][0]
            ty = spine_pts[i1][1] - spine_pts[i0][1]
            tz = spine_pts[i1][2] - spine_pts[i0][2]
            tlen = math.sqrt(tx*tx + ty*ty + tz*tz) or 1.0
            tx /= tlen; ty /= tlen; tz /= tlen
            # Frame in XZ plane (since Y=0 is symmetry plane for body/neck)
            nx, nz = -tz, tx
            nlen = math.hypot(nx, nz) or 1.0
            nx /= nlen; nz /= nlen

            v_coord = v_range[0] + (i / max(1, n_rings - 1)) * (v_range[1] - v_range[0])
            ring = []
            for k in range(n_seg):
                ang = (k / n_seg) * 2.0 * math.pi
                ca, sa = math.cos(ang), math.sin(ang)
                vx = px + ca * rx * nx
                vy = py + sa * ry
                vz = pz + ca * rx * nz
                vert = bm.verts.new((vx, vy, vz))
                u_coord = u_range[0] + (abs(k - n_seg/2) / (n_seg/2)) * (u_range[1] - u_range[0])
                ring.append((vert, u_coord, v_coord))
            rings.append(ring)

        for i in range(n_rings - 1):
            r0, r1 = rings[i], rings[i + 1]
            for k in range(n_seg):
                k1 = (k + 1) % n_seg
                for (va, ua, va_uv), (vb, ub, vb_uv), (vc, uc, vc_uv) in [
                    (r0[k], r0[k1], r1[k1]),
                    (r0[k], r1[k1], r1[k])
                ]:
                    f = bm.faces.new((va, vb, vc))
                    f.loops[0][uv_layer].uv = (ua, va_uv)
                    f.loops[1][uv_layer].uv = (ub, vb_uv)
                    f.loops[2][uv_layer].uv = (uc, vc_uv)

    # 1. Continuous Sculpted Avian Body -> S-Curved Neck -> Head -> Hooked Beak Tip!
    # Spine points (x, y, z) from tail-base (-0.95, 0, 1.05) through breast (0.35, 0, 1.15),
    # S-curved slender neck up to head (0.72, 0, 2.38), and beak tip (1.12, 0, 2.32)
    avian_spine = [
        (-1.05, 0.0, 1.02), # Tail uropygium tip
        (-0.85, 0.0, 1.08), # Lower back
        (-0.50, 0.0, 1.16), # Mid back / rump
        (-0.10, 0.0, 1.18), # Plump torso center
        ( 0.25, 0.0, 1.16), # Deep keeled breast
        ( 0.48, 0.0, 1.26), # Base of neck
        ( 0.56, 0.0, 1.48), # Lower S-curve of neck
        ( 0.52, 0.0, 1.74), # Mid neck (curving slightly back)
        ( 0.48, 0.0, 2.00), # Upper neck
        ( 0.54, 0.0, 2.22), # Throat / skull base
        ( 0.66, 0.0, 2.35), # Avian skull & eyes
        ( 0.82, 0.0, 2.36), # Fore-skull / lore
        ( 0.96, 0.0, 2.33), # Upper beak base
        ( 1.14, 0.0, 2.27), # Sharp hooked beak tip
    ]
    avian_rx = [0.04, 0.18, 0.34, 0.44, 0.42, 0.26, 0.16, 0.13, 0.12, 0.13, 0.17, 0.13, 0.055, 0.008]
    avian_ry = [0.05, 0.22, 0.36, 0.42, 0.38, 0.24, 0.15, 0.12, 0.11, 0.12, 0.16, 0.11, 0.045, 0.006]
    # UV Region [0.02..0.48, 0.02..0.98]: V=0 is rump, V=0.45 is breast, V=0.75 is neck, V=0.85 is head, V=0.95 is beak
    add_lofted_tube(avian_spine, avian_rx, avian_ry, (0.02, 0.28), (0.02, 0.98), n_seg=28)

    # 2. Sculpted Folded Barred Wings hugging left and right flanks
    for side in (-1.0, 1.0):
        wing_spine = [
            ( 0.22, side * 0.34, 1.24),
            (-0.08, side * 0.41, 1.22),
            (-0.42, side * 0.36, 1.16),
            (-0.78, side * 0.24, 1.08),
            (-1.08, side * 0.14, 1.00),
        ]
        w_rx = [0.10, 0.24, 0.26, 0.18, 0.03]
        w_ry = [0.04, 0.10, 0.09, 0.06, 0.015]
        add_lofted_tube(wing_spine, w_rx, w_ry, (0.30, 0.48), (0.10, 0.48), n_seg=16)

    # 3. Royal Peacock Fan Crest (Aigrette of 9 upright pins crowned with iridescent fan pennants)
    for c_idx in range(9):
        frac = (c_idx / 8.0) - 0.5
        ang_x = frac * 0.55
        bx = 0.64 - frac * 0.10
        bz = 2.48
        tx = bx - math.sin(ang_x) * 0.24
        tz = bz + math.cos(ang_x) * 0.26
        # Slender stem + teardrop pennant at top
        c_spine = [
            (bx, 0.0, bz),
            ((bx+tx)*0.5, 0.0, (bz+tz)*0.5),
            (tx - math.sin(ang_x)*0.05, 0.0, tz - 0.04),
            (tx, 0.0, tz),
            (tx + math.sin(ang_x)*0.03, 0.0, tz + 0.04),
        ]
        c_rx = [0.006, 0.005, 0.032, 0.042, 0.008]
        c_ry = [0.006, 0.005, 0.012, 0.015, 0.005]
        add_lofted_tube(c_spine, c_rx, c_ry, (0.05, 0.25), (0.72, 0.78), n_seg=10)

    # 4. Anatomical Avian Legs (Feathered Tibia + Scaly Tarsus + 4 Talons resting at Z=0)
    for side in (-1.0, 1.0):
        lx = -0.08
        ly = side * 0.20
        leg_spine = [
            (lx,        ly, 0.92), # Feathered thigh top
            (lx - 0.06, ly, 0.62), # Ankle / hock joint
            (lx - 0.02, ly, 0.28), # Scaly tarsus shaft
            (lx + 0.01, ly, 0.04), # Foot base
        ]
        l_rx = [0.11, 0.055, 0.032, 0.035]
        l_ry = [0.09, 0.050, 0.030, 0.035]
        add_lofted_tube(leg_spine, l_rx, l_ry, (0.32, 0.46), (0.55, 0.85), n_seg=12)

        # 3 front toes + 1 hind spur
        for t_ang, t_len in [(-0.42, 0.22), (0.0, 0.26), (0.42, 0.22), (math.pi, 0.14)]:
            dx = math.cos(t_ang) * t_len
            dy = math.sin(t_ang) * t_len
            toe_spine = [
                (lx + 0.01, ly, 0.035),
                (lx + 0.01 + dx*0.6, ly + dy*0.6, 0.022),
                (lx + 0.01 + dx,     ly + dy,     0.005),
            ]
            add_lofted_tube(toe_spine, [0.022, 0.016, 0.004], [0.022, 0.016, 0.004], (0.35, 0.45), (0.80, 0.88), n_seg=8)

    # 5. Magnificent Multi-Layered Cascading & Arching Peacock Train with 33 Iridescent Ocelli Plumes!
    # Every plume is mapped to UV [0.52..0.98, 0.02..0.98] where a complete photorealistic peacock feather
    # with emerald barbules and a glowing concentric gold/turquoise/indigo Eye-Spot (Ocellus) at V=0.82 is baked!
    plume_configs = []
    # 4 cascading tiers of feathers fanning out in width and length
    for tier, (n_plumes, length, arch_h, spread_w, z_end) in enumerate([
        ( 5, 1.15, 0.22, 0.45, 0.72),
        ( 7, 1.75, 0.28, 0.78, 0.48),
        ( 9, 2.35, 0.32, 1.15, 0.24),
        (11, 2.95, 0.35, 1.55, 0.05),
    ]):
        for p in range(n_plumes):
            frac = (p / max(1, n_plumes - 1)) - 0.5 # -0.5 to +0.5
            plume_configs.append((frac, length, arch_h, spread_w, z_end, tier * 0.025))

    for frac, length, arch_h, spread_w, z_end, z_offset in plume_configs:
        n_pts = 10
        for i in range(n_pts - 1):
            t0 = i / (n_pts - 1)
            t1 = (i + 1) / (n_pts - 1)

            def plume_pt(t):
                px = -0.82 - length * t
                py = frac * spread_w * (0.25 + 0.75 * (t ** 0.85))
                # Graceful upward arch near rump then sweeping cascade to the ground
                pz = 1.06 * (1.0 - t) + z_end * t + arch_h * math.sin(t * math.pi) + z_offset - 0.12 * (frac ** 2)
                # Feather vane width: widens into a lush oval paddle near the Ocellus (t=0.75..0.92)
                w = 0.05 + 0.13 * math.sin(max(0.05, min(0.98, t ** 0.75)) * math.pi)
                return px, py, max(0.02, pz), w

            x0, y0, z0, w0 = plume_pt(t0)
            x1, y1, z1, w1 = plume_pt(t1)
            # Tilt vane slightly with lateral fan angle
            tilt = frac * 0.35
            dy0, dz0 = w0 * math.cos(tilt), w0 * math.sin(tilt)
            dy1, dz1 = w1 * math.cos(tilt), w1 * math.sin(tilt)

            # Create double-sided (top + bottom slightly cambered) feather ribbon quad
            v_bl = bm.verts.new((x0, y0 - dy0, z0 - dz0))
            v_bc = bm.verts.new((x0, y0,       z0 + 0.018))
            v_br = bm.verts.new((x0, y0 + dy0, z0 + dz0))
            v_tl = bm.verts.new((x1, y1 - dy1, z1 - dz1))
            v_tc = bm.verts.new((x1, y1,       z1 + 0.018))
            v_tr = bm.verts.new((x1, y1 + dy1, z1 + dz1))

            uv_v0 = 0.04 + 0.92 * t0
            uv_v1 = 0.04 + 0.92 * t1
            u_l, u_c, u_r = 0.54, 0.75, 0.96

            for va, ua, va_v, vb, ub, vb_v, vc, uc, vc_v in [
                (v_bl, u_l, uv_v0, v_bc, u_c, uv_v0, v_tc, u_c, uv_v1),
                (v_bl, u_l, uv_v0, v_tc, u_c, uv_v1, v_tl, u_l, uv_v1),
                (v_bc, u_c, uv_v0, v_br, u_r, uv_v0, v_tr, u_r, uv_v1),
                (v_bc, u_c, uv_v0, v_tr, u_r, uv_v1, v_tc, u_c, uv_v1),
            ]:
                f = bm.faces.new((va, vb, vc))
                f.loops[0][uv_layer].uv = (ua, va_v)
                f.loops[1][uv_layer].uv = (ub, vb_v)
                f.loops[2][uv_layer].uv = (uc, vc_v)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    # =========================================================================
    # Bake 1024x1024 Photorealistic Indian Peacock Texture Atlas
    # =========================================================================
    print("Baking 1024x1024 Photorealistic Indian Peacock Iridescent Plumage & Ocelli Texture...")
    uu, vv = np.meshgrid(np.linspace(0, 1, W, dtype=np.float32), np.linspace(0, 1, H, dtype=np.float32))

    r = np.zeros((H, W), dtype=np.float32)
    g = np.zeros((H, W), dtype=np.float32)
    b = np.zeros((H, W), dtype=np.float32)

    # REGION 1: U in [0.0..0.30] -> Body, Breast, S-Neck, Head, Eyes, & Beak (parameterized by V in [0..1])
    # V=0.0..0.35: Emerald-gold metallic back & rump scale feathers
    # V=0.35..0.88: Iridescent Royal Cobalt-Sapphire Blue Breast, Neck, & Head
    # V=0.88..1.00: Horn-grey Beak
    w_sapphire = np.clip((vv - 0.30) / 0.12, 0.0, 1.0) * (1.0 - np.clip((vv - 0.87) / 0.04, 0.0, 1.0))
    w_beak     = np.clip((vv - 0.87) / 0.04, 0.0, 1.0)

    # Iridescent feather-scale shimmer along neck/breast
    scale_pat = 0.5 + 0.5 * np.sin(uu * 180.0) * np.sin(vv * 160.0)
    r_body = 0.06 * (1.0 - w_sapphire) + (0.02 + 0.04 * scale_pat) * w_sapphire
    g_body = 0.52 * (1.0 - w_sapphire) + (0.18 + 0.24 * scale_pat) * w_sapphire
    b_body = 0.24 * (1.0 - w_sapphire) + (0.68 + 0.26 * scale_pat) * w_sapphire

    r_body = r_body * (1.0 - w_beak) + 0.62 * w_beak
    g_body = g_body * (1.0 - w_beak) + 0.58 * w_beak
    b_body = b_body * (1.0 - w_beak) + 0.50 * w_beak

    # Glossy dark avian eye & iconic white facial lore patch at V ~ 0.80, U ~ 0.14
    eye_dist = np.hypot((uu - 0.15) / 0.035, (vv - 0.80) / 0.025)
    white_patch = np.exp(-(((uu - 0.15) / 0.045)**2 + ((vv - 0.77) / 0.018)**2))
    r_body = np.where(eye_dist < 0.75, 0.04, np.where(white_patch > 0.45, 0.95, r_body))
    g_body = np.where(eye_dist < 0.75, 0.03, np.where(white_patch > 0.45, 0.95, g_body))
    b_body = np.where(eye_dist < 0.75, 0.03, np.where(white_patch > 0.45, 0.95, b_body))

    # REGION 2: U in [0.30..0.50] -> Folded Wings (V=0.0..0.52) & Scaly Legs (V=0.52..1.0)
    # Barred buff-and-espresso scapular wing pattern + chestnut flight feathers
    bar_wave = 0.5 + 0.5 * np.cos(vv * 190.0 + uu * 40.0)
    r_wing = 0.22 + 0.58 * bar_wave
    g_wing = 0.16 + 0.48 * bar_wave
    b_wing = 0.11 + 0.36 * bar_wave
    w_leg_uv = np.clip((vv - 0.52) / 0.05, 0.0, 1.0)
    r_wing = r_wing * (1.0 - w_leg_uv) + 0.46 * w_leg_uv
    g_wing = g_wing * (1.0 - w_leg_uv) + 0.42 * w_leg_uv
    b_wing = b_wing * (1.0 - w_leg_uv) + 0.36 * w_leg_uv

    # REGION 3: U in [0.50..1.00] -> Individual Peacock Train Feather Vane & Concentric Eye-Spot (Ocellus)!
    # Center of feather shaft (rachis) is at U = 0.75; Ocellus center is at (U = 0.75, V = 0.80)
    du = (uu - 0.75) / 0.18
    dv = (vv - 0.80) / 0.12
    # Diagonal feather barbule striations radiating outward from the central shaft
    barbule = 0.5 + 0.5 * np.sin((np.abs(du) * 140.0 - vv * 95.0))
    # Emerald-jade & golden-bronze iridescent feather vane
    r_plume = 0.05 + 0.16 * barbule
    g_plume = 0.48 + 0.32 * barbule
    b_plume = 0.22 + 0.18 * barbule

    # Concentric Ocellus (Peacock Eye-Spot) rings around (du=0, dv=0):
    oc_r = np.hypot(du * 1.15, dv)
    # 1. Innermost deep midnight-indigo / royal-purple pupil (oc_r < 0.28)
    w_pupil = 1.0 - np.clip((oc_r - 0.22) / 0.07, 0.0, 1.0)
    # 2. Glowing electric turquoise-cyan heart ring (0.22 < oc_r < 0.46)
    w_cyan  = np.clip((oc_r - 0.20) / 0.07, 0.0, 1.0) * (1.0 - np.clip((oc_r - 0.42) / 0.08, 0.0, 1.0))
    # 3. Broad burnished copper-gold iris ring (0.42 < oc_r < 0.78)
    w_gold  = np.clip((oc_r - 0.40) / 0.08, 0.0, 1.0) * (1.0 - np.clip((oc_r - 0.74) / 0.09, 0.0, 1.0))
    # 4. Outer iridescent violet-blue halo (0.74 < oc_r < 0.95)
    w_halo  = np.clip((oc_r - 0.72) / 0.08, 0.0, 1.0) * (1.0 - np.clip((oc_r - 0.92) / 0.08, 0.0, 1.0))

    r_plume = r_plume * (1.0 - w_halo) + 0.18 * w_halo
    g_plume = g_plume * (1.0 - w_halo) + 0.25 * w_halo
    b_plume = b_plume * (1.0 - w_halo) + 0.78 * w_halo

    r_plume = r_plume * (1.0 - w_gold) + (0.88 + 0.10 * barbule) * w_gold
    g_plume = g_plume * (1.0 - w_gold) + (0.58 + 0.12 * barbule) * w_gold
    b_plume = b_plume * (1.0 - w_gold) + 0.08 * w_gold

    r_plume = r_plume * (1.0 - w_cyan) + 0.02 * w_cyan
    g_plume = g_plume * (1.0 - w_cyan) + 0.85 * w_cyan
    b_plume = b_plume * (1.0 - w_cyan) + 0.92 * w_cyan

    r_plume = r_plume * (1.0 - w_pupil) + 0.05 * w_pupil
    g_plume = g_plume * (1.0 - w_pupil) + 0.04 * w_pupil
    b_plume = b_plume * (1.0 - w_pupil) + 0.28 * w_pupil

    # Combine the 3 UV regions and multiply by photographic feather-fiber micro-detail!
    r = np.where(uu < 0.30, r_body, np.where(uu < 0.50, r_wing, r_plume))
    g = np.where(uu < 0.30, g_body, np.where(uu < 0.50, g_wing, g_plume))
    b = np.where(uu < 0.30, b_body, np.where(uu < 0.50, b_wing, b_plume))

    r = np.clip(r * feather_micro, 0.0, 1.0)
    g = np.clip(g * feather_micro, 0.0, 1.0)
    b = np.clip(b * feather_micro, 0.0, 1.0)

    out_pixels = np.ones((H, W, 4), dtype=np.float32)
    out_pixels[:, :, 0] = r; out_pixels[:, :, 1] = g; out_pixels[:, :, 2] = b

    pk_img = bpy.data.images.new("PeacockPBRTex", width=W, height=H, alpha=False)
    pk_img.pixels[:] = out_pixels.ravel().tolist()
    pk_img.filepath_raw = os.path.join(SCRATCH_DIR, "peacock_tex.png")
    pk_img.file_format = 'PNG'
    pk_img.save(); pk_img.pack()

    mat = bpy.data.materials.new(name="IndianPeacockMat")
    mat.use_nodes = True
    mat.use_backface_culling = False
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_node.image = pk_img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])
    if 'Roughness' in bsdf.inputs:
        bsdf.inputs['Roughness'].default_value = 0.42
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = 0.28
    mesh.materials.append(mat)

    bm.free()
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODELS_DIR, "peacock.glb"), export_format='GLB')
    print("✓ Exported peacock.glb")

if __name__ == "__main__":
    build_tiger()
    build_boar()
    build_squirrel()
    build_peacock()
    print("✓ All 4 photorealistic species models built and exported!")
