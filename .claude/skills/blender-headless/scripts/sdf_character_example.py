"""Pikachu body as a signed distance field -> marching cubes mesh (npz).
Units ~ metres-ish, height ~1.45 incl. ears. x right, -y = front, z up."""
import numpy as np, sys, json, time
from skimage.measure import marching_cubes

VOX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.003
OUT = sys.argv[1]
f32 = np.float32


def V(*a):
    return np.array(a, dtype=f32)


def nrm(v):
    v = np.asarray(v, f32); return v / np.linalg.norm(v)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def ellip(P, c, r, R=None):
    p = P - c
    if R is not None:
        p = p @ R.T  # world -> local
    k0 = np.linalg.norm(p / r, axis=-1)
    k1 = np.linalg.norm(p / (r * r), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-6)


def rcone(P, a, b, r1, r2):
    """round cone (iq)"""
    ba = b - a; l2 = ba @ ba; rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = P - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - y[..., None] * ba
    x2 = np.sum(xv * xv, -1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d1 = np.sqrt(x2 + z2) * il2 - r2
    d2 = np.sqrt(x2 + y2) * il2 - r1
    d3 = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1
    out = np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))
    return out


def rotz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], f32)


def frame(u, hint):
    u = nrm(u); v = nrm(np.cross(hint, u)); w = np.cross(u, v)
    return u, v, w


# ---------------- parameters (shared with shader via json) ----------------
EAR = []
for s in (-1, 1):
    base = V(0.135 * s, 0.03, 0.93)
    tip = V(0.37 * s, 0.10, 1.43)
    u = nrm(tip - base)
    # width axis lies roughly in the x-z plane, thickness ~ y
    v = nrm(np.cross(V(0, 1, 0), u)); w = np.cross(u, v)
    EAR.append(dict(base=base, tip=tip, u=u, v=v, w=w, L=float(np.linalg.norm(tip - base))))
EAR_T0 = 0.64  # black tip starts here (fraction of length)

CHEEK = [V(0.205 * s, -0.175, 0.705) for s in (-1, 1)]
TAIL_POLY = np.array([(0.15, 0.17), (0.31, 0.26), (0.245, 0.325), (0.44, 0.41), (0.355, 0.49),
                      (0.64, 0.66), (0.49, 0.93), (0.29, 0.75), (0.37, 0.68), (0.21, 0.58),
                      (0.28, 0.515), (0.13, 0.30)], f32)
MOUTH = dict(z0=0.703, a=0.013, w=0.034)


def poly_sdf2(py, pz, poly):
    d = np.full(py.shape, 1e9, f32); s = np.ones(py.shape, f32)
    n = len(poly)
    for i in range(n):
        vi = poly[i]; vj = poly[i - 1]
        ey, ez = vj - vi
        wy, wz = py - vi[0], pz - vi[1]
        t = np.clip((wy * ey + wz * ez) / (ey * ey + ez * ez), 0, 1)
        by, bz = wy - ey * t, wz - ez * t
        d = np.minimum(d, by * by + bz * bz)
        c1 = pz >= vi[1]; c2 = pz < vj[1]; c3 = ey * wz > ez * wy
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def finger_set(P, palm_c, palm_r, R, dirs, bases, length, r1, r2, kpalm):
    palm = ellip(P, palm_c, palm_r, R)
    d = palm
    for dvec, b in zip(dirs, bases):
        f = rcone(P, b, b + dvec * length, r1, r2)
        d = np.minimum(d, smin(palm, f, kpalm))
    return d


def hand(P, s):
    # s=-1 left hand (on -x side), fingers curl toward body centre (+x for left)
    wrist = V(0.138 * s, -0.232, 0.462)
    shoulder = V(0.19 * s, -0.05, 0.53)
    arm = rcone(P, shoulder, wrist, 0.058, 0.047)
    pc = V(0.114 * s, -0.264, 0.447)
    fwd = nrm(V(-0.55 * s, -0.55, -0.45))      # main finger direction
    up = nrm(np.cross(fwd, V(-s, 0, 0)))      # spread axis
    up = nrm(V(0, 0.25, 1.0) - fwd * (fwd @ V(0, 0.25, 1.0)))
    side = np.cross(fwd, up)
    dirs, bases = [], []
    for i, sp in enumerate((-1.5, -0.5, 0.5, 1.5)):
        b = pc + fwd * 0.026 + up * (sp * 0.0235) + side * 0.004 * (abs(sp) - 1.0)
        dv = nrm(fwd + up * sp * 0.32 - side * 0.12)
        dirs.append(dv); bases.append(b)
    # thumb: upward / inward
    tb = pc + up * 0.042 + fwd * 0.006
    dirs.append(nrm(up * 0.75 + fwd * 0.65)); bases.append(tb)
    R = np.stack([fwd, up, side])  # local axes rows
    h = finger_set(P, pc, V(0.046, 0.052, 0.034), R, dirs, bases, 0.024, 0.0128, 0.0118, 0.011)
    return smin(arm, h, 0.02)


def foot(P, s):
    ang = 0.22 * s
    Rz = rotz(ang)
    c = V(0.125 * s, -0.06, 0.04)
    R = Rz.T  # world->local
    base = ellip(P, c, V(0.08, 0.108, 0.046), R)
    fwd = Rz @ V(0, -1, 0); side = Rz @ V(1, 0, 0)
    d = base
    for sp in (-1, 0, 1):
        b = c + fwd * 0.055 + side * (sp * 0.047) + V(0, 0, -0.008)
        t = b + fwd * 0.052 + side * sp * 0.008
        toe = rcone(P, b, t, 0.0215, 0.0205)
        d = np.minimum(d, smin(base, toe, 0.02))
    return d


def ear(P, e):
    p = P - e['base']
    pu = p @ e['u']; pv = p @ e['v']; pw = p @ e['w']
    q = e['base'] + e['u'] * pu[..., None] + e['v'] * pv[..., None] + e['w'] * (pw / 0.5)[..., None]
    L = e['L']; b = e['base']; u = e['u']
    m = b + u * (0.45 * L)
    d = smin(rcone(q, b - u * 0.05, m, 0.07, 0.092), rcone(q, m, b + u * (0.94 * L), 0.092, 0.016), 0.05) * 0.5
    # groove line at the black tip boundary
    t = pu / L
    d = d + 0.0042 * np.exp(-((t - EAR_T0) / 0.0085) ** 2)
    return d


def sdf(P):
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    # body
    body = ellip(P, V(0, 0.02, 0.29), V(0.255, 0.225, 0.27))
    body = smin(body, ellip(P, V(0, 0.01, 0.47), V(0.205, 0.185, 0.17)), 0.08)
    for s in (-1, 1):
        body = smin(body, ellip(P, V(0.14 * s, -0.005, 0.15), V(0.105, 0.115, 0.11)), 0.05)
    # head
    head = ellip(P, V(0, 0.0, 0.775), V(0.292, 0.255, 0.245))
    for s in (-1, 1):
        head = smin(head, ellip(P, V(0.165 * s, -0.07, 0.69), V(0.135, 0.15, 0.115)), 0.06)
        # raised cheek pads
        head = smin(head, ellip(P, CHEEK[(s + 1) // 2] + V(0, 0.012, 0), V(0.058, 0.03, 0.058)), 0.035)
    head = smin(head, ellip(P, V(0, -0.15, 0.715), V(0.12, 0.11, 0.085)), 0.08)
    d = smin(body, head, 0.1)
    for e in EAR:
        d = smin(d, ear(P, e), 0.035)
    for s in (-1, 1):
        d = smin(d, foot(P, s), 0.035)
    # hands: blend only at the shoulder region
    for s in (-1, 1):
        d = smin(d, hand(P, s), 0.018)
    # tail
    tp = poly_sdf2(y, z, TAIL_POLY)
    th = np.maximum(np.abs(x) - 0.026, 0)
    tail = np.sqrt(np.maximum(tp, 0) ** 2 + th ** 2) + np.minimum(np.maximum(tp, np.abs(x) - 0.026), 0) - 0.012
    d = smin(d, tail, 0.03)
    # flat sole
    d = smax(d, -z, 0.006)
    # mouth groove (omega), front of face only
    ax = np.abs(x)
    w = MOUTH['w']
    zc = MOUTH['z0'] - MOUTH['a'] * np.sin(np.pi * np.clip(ax / w, 0, 1))
    # curl the ends upward slightly beyond w
    zc = np.where(ax > w, MOUTH['z0'] + (ax - w) * 0.5, zc)
    dm = np.where(ax < w + 0.012, np.abs(z - zc), 1.0)
    front = 1 / (1 + np.exp((y + 0.16) / 0.01))
    d = d + 0.0065 * np.exp(-(dm / 0.0042) ** 2) * front
    # nose dimple-free; nostril handled as separate object
    return d


def main():
    lo = V(-0.52, -0.40, -0.02); hi = V(0.52, 0.68, 1.50)
    n = np.ceil((hi - lo) / VOX).astype(int) + 1
    print('grid', n, n.prod() / 1e6, 'M', flush=True)
    xs = lo[0] + np.arange(n[0], dtype=f32) * VOX
    ys = lo[1] + np.arange(n[1], dtype=f32) * VOX
    zs = lo[2] + np.arange(n[2], dtype=f32) * VOX
    vol = np.empty((n[0], n[1], n[2]), f32)
    t0 = time.time()
    CH = 24
    for i in range(0, n[2], CH):
        zz = zs[i:i + CH]
        X, Y, Z = np.meshgrid(xs, ys, zz, indexing='ij')
        P = np.stack([X, Y, Z], -1)
        vol[:, :, i:i + CH] = sdf(P)
        print(f'{i}/{n[2]} {time.time()-t0:.0f}s', flush=True)
    verts, faces, normals, _ = marching_cubes(vol, 0.0, spacing=(VOX, VOX, VOX))
    verts += lo
    print('verts', len(verts), 'faces', len(faces))
    params = dict(ears=[{k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in e.items()} for e in EAR],
                  ear_t0=EAR_T0, cheeks=[c.tolist() for c in CHEEK], mouth=MOUTH,
                  tail_poly=TAIL_POLY.tolist())
    np.savez_compressed(OUT, verts=verts.astype(f32), faces=faces.astype(np.int32))
    json.dump(params, open(OUT.replace('.npz', '.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
