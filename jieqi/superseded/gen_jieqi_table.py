#!/usr/bin/env python3
"""
玄枢 B4 回归基准数据 —— 1900–2100 二十四节气交节时刻表（独立生成脚本）

本脚本只用于生成基准数据，不与排盘引擎共用任何代码。

用法:
    python3 gen_jieqi_table.py de440s.bsp out.csv

方法
----
* 星历: JPL DE440s (SPK type 2)，脚本先校验 MD5 / 大小，不符即退出。
  SPK 由本脚本直接读取（Chebyshev 求值），未使用 Skyfield / jplephem。
* 时间: 求根在 TT 上进行；查星历时 TDB = TT + 0.001657 s·sin g + 0.000014 s·sin 2g。
* 视位置（与 Skyfield `earth.at(t).observe(sun).apparent()` 相同的步骤）:
    - 地心观测者，光行时迭代（太阳取 t − τ 时刻的质心位置）
    - 相对论性周年光行差（NOVAS / Skyfield 同一公式，地球质心速度取自星历）
    - 太阳对自身光线的引力偏折为 0，不计
* 坐标: GCRS → 真黄道/真春分点 (of date)
    - 岁差: IAU 2006 Fukushima–Williams 角 γ̄, φ̄, ψ̄（已含 ICRS 帧偏差）
    - 章动: IAU 1980 章动序列（63 项，Meeus《天文算法》表 22.A），仅取 Δψ
    - 视黄经 λ = atan2(R1(φ̄)·R3(γ̄)·p) + ψ̄ + Δψ
  （Skyfield 用 IAU 2000A 章动；与 IAU 1980 的差在 0.01–0.03″ 量级，约 ≤1 秒时间）
* 交节: λ = 0°, 15°, …, 345°（0° 春分，315° 立春），割线/牛顿迭代至 |Δλ| < 1e-9°。
* 世界时: UT1 = TT − ΔT；北京时间 = UT1 + 8 h；四舍五入到整秒。
  term_utc_iso 一列即这个 UT1 时刻（1972 年后与 UTC 相差 < 0.9 s）。
* ΔT 模型（因无法安装 Skyfield，未使用其内置 ΔT）:
    - 1900.0–2005.0: Espenak & Meeus (2006, NASA) 分段多项式
    - 2005.0–2026.0: 实测年值（IERS，取年初值）三次样条
    - 2026.0–2050.0: 三次 Hermite 过渡，从 2026 实测值/斜率接到 Espenak–Meeus 2050 值/斜率
    - 2050.0–2100.x: Espenak & Meeus (2006) 2050–2150 公式
  2026 年以后全部是外推值。
"""
import csv
import hashlib
import math
import os
import struct
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

EXPECTED_MD5 = "3917ee56769db332790c751e2168843d"
EXPECTED_SIZE = 32726016

J2000 = 2451545.0
AU_KM = 149597870.7
C_KMS = 299792.458
C_AUDAY = C_KMS * 86400.0 / AU_KM
AS2R = math.pi / (180.0 * 3600.0)

TERMS = {
    0: "春分", 15: "清明", 30: "谷雨", 45: "立夏", 60: "小满", 75: "芒种",
    90: "夏至", 105: "小暑", 120: "大暑", 135: "立秋", 150: "处暑", 165: "白露",
    180: "秋分", 195: "寒露", 210: "霜降", 225: "立冬", 240: "小雪", 255: "大雪",
    270: "冬至", 285: "小寒", 300: "大寒", 315: "立春", 330: "雨水", 345: "惊蛰",
}


# ---------------------------------------------------------------- 校验
def verify(path):
    size = os.path.getsize(path)
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    md5 = h.hexdigest()
    if size != EXPECTED_SIZE or md5 != EXPECTED_MD5:
        sys.exit(f"星历校验失败: size={size} md5={md5}")
    return md5, size


# ---------------------------------------------------------------- SPK 读取
class SPK:
    def __init__(self, path):
        data = open(path, "rb").read()
        if data[:8] != b"DAF/SPK ":
            sys.exit("不是 SPK 文件")
        nd, ni = struct.unpack("<ii", data[8:16])
        fward = struct.unpack("<i", data[76:80])[0]
        self.arr = np.frombuffer(data, dtype="<f8")
        self.segs = {}
        rec = fward
        ss = nd + (ni + 1) // 2
        while rec:
            off = (rec - 1) * 1024
            nxt, _, nsum = struct.unpack("<ddd", data[off:off + 24])
            for i in range(int(nsum)):
                o = off + 24 + i * ss * 8
                dc = struct.unpack("<%dd" % nd, data[o:o + nd * 8])
                ic = struct.unpack("<%di" % ni, data[o + nd * 8:o + nd * 8 + ni * 4])
                if ic[3] != 2:
                    sys.exit("只支持 SPK type 2")
                start, end = ic[4], ic[5]
                init, intlen, rsize, n = self.arr[end - 4:end]
                self.segs[(ic[0], ic[1])] = (dc[0], dc[1], start, init, intlen, int(rsize), int(n))
            rec = int(nxt)

    def pv(self, target, center, et):
        """位置 km、速度 km/s（ICRF），et = TDB 秒（自 J2000）。"""
        e0, e1, start, init, intlen, rsize, n = self.segs[(target, center)]
        if not (e0 <= et <= e1):
            raise ValueError("超出星历范围")
        idx = min(int((et - init) // intlen), n - 1)
        r = self.arr[start - 1 + idx * rsize:start - 1 + (idx + 1) * rsize]
        mid, rad = r[0], r[1]
        nc = (rsize - 2) // 3
        x = (et - mid) / rad
        T = np.empty(nc)
        D = np.empty(nc)
        T[0], D[0] = 1.0, 0.0
        T[1], D[1] = x, 1.0
        for k in range(2, nc):
            T[k] = 2 * x * T[k - 1] - T[k - 2]
            D[k] = 2 * T[k - 1] + 2 * x * D[k - 1] - D[k - 2]
        c = r[2:].reshape(3, nc)
        return c @ T, (c @ D) / rad


# ---------------------------------------------------------------- 章动 IAU 1980
# D, M, M', F, Ω, ψ(0.0001″), ψ·T, ε(0.0001″), ε·T
NUT = [
    (0, 0, 0, 0, 1, -171996, -174.2, 92025, 8.9), (-2, 0, 0, 2, 2, -13187, -1.6, 5736, -3.1),
    (0, 0, 0, 2, 2, -2274, -0.2, 977, -0.5), (0, 0, 0, 0, 2, 2062, 0.2, -895, 0.5),
    (0, 1, 0, 0, 0, 1426, -3.4, 54, -0.1), (0, 0, 1, 0, 0, 712, 0.1, -7, 0),
    (-2, 1, 0, 2, 2, -517, 1.2, 224, -0.6), (0, 0, 0, 2, 1, -386, -0.4, 200, 0),
    (0, 0, 1, 2, 2, -301, 0, 129, -0.1), (-2, -1, 0, 2, 2, 217, -0.5, -95, 0.3),
    (-2, 0, 1, 0, 0, -158, 0, 0, 0), (-2, 0, 0, 2, 1, 129, 0.1, -70, 0),
    (0, 0, -1, 2, 2, 123, 0, -53, 0), (2, 0, 0, 0, 0, 63, 0, 0, 0),
    (0, 0, 1, 0, 1, 63, 0.1, -33, 0), (2, 0, -1, 2, 2, -59, 0, 26, 0),
    (0, 0, -1, 0, 1, -58, -0.1, 32, 0), (0, 0, 1, 2, 1, -51, 0, 27, 0),
    (-2, 0, 2, 0, 0, 48, 0, 0, 0), (0, 0, -2, 2, 1, 46, 0, -24, 0),
    (2, 0, 0, 2, 2, -38, 0, 16, 0), (0, 0, 2, 2, 2, -31, 0, 13, 0),
    (0, 0, 2, 0, 0, 29, 0, 0, 0), (-2, 0, 1, 2, 2, 29, 0, -12, 0),
    (0, 0, 0, 2, 0, 26, 0, 0, 0), (-2, 0, 0, 2, 0, -22, 0, 0, 0),
    (0, 0, -1, 2, 1, 21, 0, -10, 0), (0, 2, 0, 0, 0, 17, -0.1, 0, 0),
    (2, 0, -1, 0, 1, 16, 0, -8, 0), (-2, 2, 0, 2, 2, -16, 0.1, 7, 0),
    (0, 1, 0, 0, 1, -15, 0, 9, 0), (-2, 0, 1, 0, 1, -13, 0, 7, 0),
    (0, -1, 0, 0, 1, -12, 0, 6, 0), (0, 0, 2, -2, 0, 11, 0, 0, 0),
    (2, 0, -1, 2, 1, -10, 0, 5, 0), (2, 0, 1, 2, 2, -8, 0, 3, 0),
    (0, 1, 0, 2, 2, 7, 0, -3, 0), (-2, 1, 1, 0, 0, -7, 0, 0, 0),
    (0, -1, 0, 2, 2, -7, 0, 3, 0), (2, 0, 0, 2, 1, -7, 0, 3, 0),
    (2, 0, 1, 0, 0, 6, 0, 0, 0), (-2, 0, 2, 2, 2, 6, 0, -3, 0),
    (-2, 0, 1, 2, 1, 6, 0, -3, 0), (2, 0, -2, 0, 1, -6, 0, 3, 0),
    (2, 0, 0, 0, 1, -6, 0, 3, 0), (0, -1, 1, 0, 0, 5, 0, 0, 0),
    (-2, -1, 0, 2, 1, -5, 0, 3, 0), (-2, 0, 0, 0, 1, -5, 0, 3, 0),
    (0, 0, 2, 2, 1, -5, 0, 3, 0), (-2, 0, 2, 0, 1, 4, 0, 0, 0),
    (-2, 1, 0, 2, 1, 4, 0, 0, 0), (0, 0, 1, -2, 0, 4, 0, 0, 0),
    (-1, 0, 1, 0, 0, -4, 0, 0, 0), (-2, 1, 0, 0, 0, -4, 0, 0, 0),
    (1, 0, 0, 0, 0, -4, 0, 0, 0), (0, 0, 1, 2, 0, 3, 0, 0, 0),
    (0, 0, -2, 2, 2, -3, 0, 0, 0), (-1, -1, 1, 0, 0, -3, 0, 0, 0),
    (0, 1, 1, 0, 0, -3, 0, 0, 0), (0, -1, 1, 2, 2, -3, 0, 0, 0),
    (2, -1, -1, 2, 2, -3, 0, 0, 0), (0, 0, 3, 2, 2, -3, 0, 0, 0),
    (2, -1, 0, 2, 2, -3, 0, 0, 0),
]
_NUT_ARG = np.array([r[:5] for r in NUT], dtype=float)
_NUT_PS = np.array([r[5] for r in NUT], dtype=float)
_NUT_PT = np.array([r[6] for r in NUT], dtype=float)
_NUT_ES = np.array([r[7] for r in NUT], dtype=float)
_NUT_ET = np.array([r[8] for r in NUT], dtype=float)


def nutation_1980(T):
    """返回 (Δψ, Δε)，单位角秒。T: TT 儒略世纪。"""
    D = 297.85036 + 445267.111480 * T - 0.0019142 * T**2 + T**3 / 189474
    M = 357.52772 + 35999.050340 * T - 0.0001603 * T**2 - T**3 / 300000
    Mp = 134.96298 + 477198.867398 * T + 0.0086972 * T**2 + T**3 / 56250
    F = 93.27191 + 483202.017538 * T - 0.0036825 * T**2 + T**3 / 327270
    Om = 125.04452 - 1934.136261 * T + 0.0020708 * T**2 + T**3 / 450000
    arg = np.radians(_NUT_ARG @ np.array([D, M, Mp, F, Om]))
    dpsi = np.sum((_NUT_PS + _NUT_PT * T) * np.sin(arg)) * 1e-4
    deps = np.sum((_NUT_ES + _NUT_ET * T) * np.cos(arg)) * 1e-4
    return dpsi, deps


# ---------------------------------------------------------------- 岁差 IAU 2006 (F-W)
def fw_angles(T):
    gamb = (-0.052928 + (10.556378 + (0.4932044 + (-0.00031238 + (-0.000002788 + 0.0000000260 * T) * T) * T) * T) * T)
    phib = (84381.412819 + (-46.811016 + (0.0511268 + (0.00053289 + (-0.000000440 - 0.0000000176 * T) * T) * T) * T) * T)
    psib = (-0.041775 + (5038.481484 + (1.5584175 + (-0.00018522 + (-0.000026452 - 0.0000000148 * T) * T) * T) * T) * T)
    return gamb * AS2R, phib * AS2R, psib * AS2R


# ---------------------------------------------------------------- 太阳视黄经
class Sun:
    def __init__(self, spk):
        self.spk = spk

    def apparent_lon(self, jd_tt):
        """真黄道/真春分点视黄经（度），jd_tt 为 TT 儒略日。"""
        g = math.radians(357.53 + 0.98560028 * (jd_tt - J2000))
        et = (jd_tt - J2000) * 86400.0 + 0.001657 * math.sin(g) + 0.000014 * math.sin(2 * g)
        spk = self.spk
        emb_p, emb_v = spk.pv(3, 0, et)
        e_p, e_v = spk.pv(399, 3, et)
        earth_p, earth_v = emb_p + e_p, emb_v + e_v
        lt = 0.0
        for _ in range(10):
            s_p, _ = spk.pv(10, 0, et - lt)
            p = s_p - earth_p
            new_lt = np.linalg.norm(p) / C_KMS
            if abs(new_lt - lt) < 1e-12:
                lt = new_lt
                break
            lt = new_lt
        s_p, _ = spk.pv(10, 0, et - lt)
        p = (s_p - earth_p) / AU_KM                     # AU
        v = earth_v * 86400.0 / AU_KM                   # AU/day
        # 相对论光行差（NOVAS aberration / Skyfield add_aberration）
        tlight = lt / 86400.0
        p1mag = tlight * C_AUDAY
        vemag = np.linalg.norm(v)
        beta = vemag / C_AUDAY
        cosd = np.dot(p, v) / (p1mag * vemag)
        gammai = math.sqrt(1.0 - beta * beta)
        pp = beta * cosd
        q = (1.0 + pp / (1.0 + gammai)) * tlight
        p = (gammai * p + q * v) / (1.0 + pp)
        # GCRS → 真黄道 of date
        T = (jd_tt - J2000) / 36525.0
        gamb, phib, psib = fw_angles(T)
        cg, sg = math.cos(gamb), math.sin(gamb)
        x1 = cg * p[0] + sg * p[1]
        y1 = -sg * p[0] + cg * p[1]
        z1 = p[2]
        cp, sp = math.cos(phib), math.sin(phib)
        y2 = cp * y1 + sp * z1
        lon = math.atan2(y2, x1)
        dpsi, _ = nutation_1980(T)
        lon += psib + dpsi * AS2R
        return math.degrees(lon) % 360.0


# ---------------------------------------------------------------- ΔT
DT_OBS = {  # 年初实测 ΔT（秒）
    2005: 64.69, 2006: 64.85, 2007: 65.15, 2008: 65.46, 2009: 65.78, 2010: 66.07,
    2011: 66.32, 2012: 66.60, 2013: 66.91, 2014: 67.28, 2015: 67.64, 2016: 68.10,
    2017: 68.59, 2018: 68.97, 2019: 69.22, 2020: 69.36, 2021: 69.36, 2022: 69.29,
    2023: 69.20, 2024: 69.18, 2025: 69.14, 2026: 69.10,
}


def _em(y):
    """Espenak & Meeus (2006) 多项式，仅用于 1900–2005 与 2050 以后。"""
    if y < 1920:
        t = y - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t**2 + 0.0061966 * t**3 - 0.000197 * t**4
    if y < 1941:
        t = y - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t**2 + 0.0020936 * t**3
    if y < 1961:
        t = y - 1950
        return 29.07 + 0.407 * t - t**2 / 233 + t**3 / 2547
    if y < 1986:
        t = y - 1975
        return 45.45 + 1.067 * t - t**2 / 260 - t**3 / 718
    if y < 2005:
        t = y - 2000
        return 63.86 + 0.3345 * t - 0.060374 * t**2 + 0.0017275 * t**3 + 0.000651814 * t**4 + 0.00002373599 * t**5
    u = (y - 1820) / 100
    return -20 + 32 * u * u - 0.5628 * (2150 - y)


def _build_obs_spline():
    from scipy.interpolate import CubicSpline
    ys = np.array(sorted(DT_OBS), dtype=float)
    return CubicSpline(ys, np.array([DT_OBS[int(y)] for y in ys]), bc_type="natural")


_OBS = _build_obs_spline()
_Y0, _Y1 = 2026.0, 2050.0
_V0, _D0 = float(_OBS(_Y0)), float(_OBS(_Y0, 1))
_V1 = _em(_Y1)
_D1 = (_em(_Y1 + 1e-3) - _em(_Y1 - 1e-3)) / 2e-3


def delta_t(y):
    if y < 2005.0:
        return _em(y)
    if y <= _Y0:
        return float(_OBS(y))
    if y < _Y1:
        h = _Y1 - _Y0
        s = (y - _Y0) / h
        h00 = 2 * s**3 - 3 * s**2 + 1
        h10 = s**3 - 2 * s**2 + s
        h01 = -2 * s**3 + 3 * s**2
        h11 = s**3 - s**2
        return h00 * _V0 + h10 * h * _D0 + h01 * _V1 + h11 * h * _D1
    return _em(y)


# ---------------------------------------------------------------- 求交节
def march_equinox_guess(year):
    return 2451623.80984 + 365.242374 * (year - 2000)


def solve(sun, target, jd0):
    jd = jd0
    rate = 360.0 / 365.2422
    for _ in range(50):
        lam = sun.apparent_lon(jd)
        d = (target - lam + 180.0) % 360.0 - 180.0
        if abs(d) < 1e-9:
            return jd
        lam2 = sun.apparent_lon(jd + 1e-3)
        r = ((lam2 - lam + 180.0) % 360.0 - 180.0) / 1e-3
        if r > 0.5:
            rate = r
        jd += d / rate
    raise RuntimeError("不收敛")


def jd_to_dt(jd):
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=jd - J2000)


def main():
    bsp, out = sys.argv[1], sys.argv[2]
    verify(bsp)
    sun = Sun(SPK(bsp))
    rows = []
    for year in range(1900, 2101):
        eq = march_equinox_guess(year)
        recs = []
        for lon in range(0, 360, 15):
            guess = eq + (lon / 360.0) * 365.2422 if lon < 285 else eq - ((360 - lon) / 360.0) * 365.2422
            jd_tt = solve(sun, float(lon), guess)
            yfrac = 2000.0 + (jd_tt - 2451544.5) / 365.2425
            dt = delta_t(yfrac)
            ut = jd_to_dt(jd_tt) - timedelta(seconds=dt)
            ut = (ut + timedelta(microseconds=500000)).replace(microsecond=0)  # 四舍五入到秒
            bj = ut.astimezone(timezone(timedelta(hours=8)))
            if bj.year != year:
                raise RuntimeError(f"{year} {TERMS[lon]} 落在 {bj.year} 年")
            recs.append((ut, lon, bj))
        recs.sort()
        assert len(recs) == 24
        for ut, lon, bj in recs:
            rows.append([year, TERMS[lon], lon, bj.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                         ut.strftime("%Y-%m-%dT%H:%M:%SZ")])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["year", "term", "ecliptic_longitude", "term_utc8_iso", "term_utc_iso"])
        w.writerows(rows)
    print(f"写出 {len(rows)} 行 → {out}")


if __name__ == "__main__":
    main()
