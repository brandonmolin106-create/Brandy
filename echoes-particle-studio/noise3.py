"""Fast 3D gradient noise / fbm / curl for particle fields (numba)."""
import math

import numba as nb
import numpy as np

_perm = np.random.default_rng(1234).permutation(256).astype(np.int64)
PERM = np.concatenate([_perm, _perm]).astype(np.int64)
_g = np.random.default_rng(99).standard_normal((256, 3))
GRAD = (_g / np.linalg.norm(_g, axis=1, keepdims=True)).astype(np.float64)


@nb.njit(cache=True, fastmath=True, inline='always')
def _fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


@nb.njit(cache=True, fastmath=True)
def noise3(x, y, z, perm, grad):
    xi = int(math.floor(x))
    yi = int(math.floor(y))
    zi = int(math.floor(z))
    xf = x - xi
    yf = y - yi
    zf = z - zi
    xi &= 255
    yi &= 255
    zi &= 255
    u = _fade(xf)
    v = _fade(yf)
    w = _fade(zf)
    acc = 0.0
    for dz in range(2):
        wz = w if dz else 1.0 - w
        for dy in range(2):
            wy = v if dy else 1.0 - v
            for dx in range(2):
                wx = u if dx else 1.0 - u
                h = perm[perm[perm[xi + dx] + yi + dy] + zi + dz] & 255
                g0 = grad[h, 0]
                g1 = grad[h, 1]
                g2 = grad[h, 2]
                acc += wx * wy * wz * (g0 * (xf - dx) + g1 * (yf - dy) + g2 * (zf - dz))
    return acc


@nb.njit(parallel=True, cache=True, fastmath=True)
def fbm3(p, octaves, lac, gain, perm, grad):
    n = p.shape[0]
    out = np.empty(n, np.float32)
    for i in nb.prange(n):
        x = p[i, 0]
        y = p[i, 1]
        z = p[i, 2]
        a = 1.0
        s = 0.0
        norm = 0.0
        for o in range(octaves):
            s += a * noise3(x, y, z, perm, grad)
            norm += a
            x *= lac
            y *= lac
            z *= lac
            a *= gain
        out[i] = s / norm
    return out


@nb.njit(parallel=True, cache=True, fastmath=True)
def ridged3(p, octaves, lac, gain, perm, grad):
    n = p.shape[0]
    out = np.empty(n, np.float32)
    for i in nb.prange(n):
        x = p[i, 0]
        y = p[i, 1]
        z = p[i, 2]
        a = 1.0
        s = 0.0
        norm = 0.0
        prev = 1.0
        for o in range(octaves):
            r = 1.0 - abs(noise3(x, y, z, perm, grad) * 1.8)
            r = r * r * prev
            prev = r
            s += a * r
            norm += a
            x *= lac
            y *= lac
            z *= lac
            a *= gain
        out[i] = s / norm
    return out


@nb.njit(parallel=True, cache=True, fastmath=True)
def curl3(p, scale, t, perm, grad):
    """Divergence-free-ish velocity from three offset noise fields."""
    n = p.shape[0]
    out = np.empty((n, 3), np.float32)
    e = 0.05
    for i in nb.prange(n):
        x = p[i, 0] * scale
        y = p[i, 1] * scale
        z = p[i, 2] * scale + t
        # psi = (n1, n2, n3); curl = (dn3/dy - dn2/dz, dn1/dz - dn3/dx, dn2/dx - dn1/dy)
        n1_y = noise3(x, y + e, z, perm, grad) - noise3(x, y - e, z, perm, grad)
        n1_z = noise3(x, y, z + e, perm, grad) - noise3(x, y, z - e, perm, grad)
        n2_x = noise3(x + 31.4 + e, y, z, perm, grad) - noise3(x + 31.4 - e, y, z, perm, grad)
        n2_z = noise3(x + 31.4, y, z + e, perm, grad) - noise3(x + 31.4, y, z - e, perm, grad)
        n3_x = noise3(x + e, y + 57.2, z, perm, grad) - noise3(x - e, y + 57.2, z, perm, grad)
        n3_y = noise3(x, y + 57.2 + e, z, perm, grad) - noise3(x, y + 57.2 - e, z, perm, grad)
        inv = 1.0 / (2 * e)
        out[i, 0] = (n3_y - n2_z) * inv
        out[i, 1] = (n1_z - n3_x) * inv
        out[i, 2] = (n2_x - n1_y) * inv
    return out


def fbm(p, octaves=5, lac=2.0, gain=0.5):
    return fbm3(np.ascontiguousarray(p, np.float64), octaves, lac, gain, PERM, GRAD)


def ridged(p, octaves=6, lac=2.0, gain=0.55):
    return ridged3(np.ascontiguousarray(p, np.float64), octaves, lac, gain, PERM, GRAD)


def curl(p, scale=1.0, t=0.0):
    return curl3(np.ascontiguousarray(p, np.float64), scale, t, PERM, GRAD)
