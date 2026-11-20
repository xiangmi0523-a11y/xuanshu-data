#!/usr/bin/env python3
"""
玄枢 B1 基准数据 —— 1900–2100 均时差（EoT）逐日表（Skyfield 版，独立生成脚本）

本脚本只用于生成基准数据，不与排盘引擎共用任何代码【B4-11】。

用法:
    pip install skyfield==1.55        # MIT 许可
    python3 eot/gen_eot_skyfield.py ephemeris/de440s.bsp out.csv

定义与方法【用户裁决 B1-1】
--------------------------
* 均时差 EoT = 视太阳时 − 平太阳时（正值：日晷走在钟表前面）。
* 视太阳时取格林尼治：视恒星时（GAST）− 太阳视赤经（真赤道、真春分点 of date）+ 12h；
  平太阳时取 UT1。EoT 与观测者经度无关，经度项另行计算。
* 太阳视位置：Skyfield `earth.at(t).observe(sun).apparent()`，星历 JPL DE440s。
* 采样：每日 UT1 00:00，1900-01-01 至 2101-01-01（含首尾，便于 2100-12-31 当日插值），
  共 73415 行。时间尺度用 Skyfield 1.55 内置 ΔT。
* 输出单位秒，保留 3 位小数（内部精度；App 显示到分钟，不输出秒）。
* 使用方式：引擎按出生时刻（UTC，与 UT1 相差 < 0.9 s，可忽略）在相邻两日样本间线性插值。
  1900–2100 全段逐日线性插值与直接计算之差最大约 0.11 s。
"""
import csv
import hashlib
import os
import sys

from skyfield import api

EXPECTED_MD5 = "3917ee56769db332790c751e2168843d"
EXPECTED_SIZE = 32726016


def verify(path):
    size = os.path.getsize(path)
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if size != EXPECTED_SIZE or h.hexdigest() != EXPECTED_MD5:
        sys.exit(f"星历校验失败: size={size} md5={h.hexdigest()}")


def main():
    bsp, out = sys.argv[1], sys.argv[2]
    verify(bsp)
    ts = api.load.timescale(builtin=True)
    eph = api.load_file(bsp)
    earth, sun = eph["earth"], eph["sun"]
    import numpy as np
    from datetime import date, timedelta
    d0 = date(1900, 1, 1)
    n = (date(2101, 1, 1) - d0).days + 1
    days = np.arange(n)
    t = ts.ut1(1900, 1, 1 + days, 0, 0, 0)
    ra, _, _ = earth.at(t).observe(sun).apparent().radec(epoch="date")
    ast = (t.gast - ra.hours + 12.0) % 24.0          # 格林尼治视太阳时（小时）
    mst = (t.ut1 - 0.5) % 1.0 * 24.0                  # 平太阳时 = UT1（小时）
    eot = ((ast - mst + 12.0) % 24.0 - 12.0) * 3600.0  # 秒
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "sample_ut1_iso", "eot_seconds"])
        for i in range(n):
            d = d0 + timedelta(days=int(i))
            w.writerow([d.isoformat(), f"{d.isoformat()}T00:00:00Z", f"{eot[i]:.3f}"])
    print(f"写出 {n} 行 → {out}")


if __name__ == "__main__":
    main()
