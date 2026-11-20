#!/usr/bin/env python3
"""
玄枢 B4 回归基准数据 —— 1900–2100 二十四节气交节时刻表（Skyfield 版，独立生成脚本）

本脚本只用于生成基准数据，不与排盘引擎共用任何代码。

用法:
    pip install skyfield            # MIT 许可
    python3 gen_jieqi_skyfield.py de440s.bsp out.csv

方法
----
* 星历: JPL DE440s，先校验 MD5 / 大小，不符即退出。
* 计算: Skyfield `earth.at(t).observe(sun).apparent()`，取真黄道/真春分点 (of date)
  视黄经（skyfield.framelib.ecliptic_frame），用 find_discrete 求 λ 跨过 15° 整数倍的时刻。
* 时间口径（玄枢决定：钟表时间 UTC，与出生时间同口径）:
    - 1972-01-01 之前: UT1（Skyfield 内置 ΔT），因当时民用时间以地球自转为准
    - 1972-01-01 起: UTC（Skyfield 内置闰秒表）；表末之后不再有闰秒，即 UTC = TT − 69.184 s
  北京时间 = UTC + 8 h；四舍五入到整秒。term_utc_iso 列在 1972 年前即 UT1。
"""
import csv
import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone

from skyfield import api
from skyfield.framelib import ecliptic_frame
from skyfield.searchlib import find_discrete

EXPECTED_MD5 = "3917ee56769db332790c751e2168843d"
EXPECTED_SIZE = 32726016

TERMS = {
    0: "春分", 15: "清明", 30: "谷雨", 45: "立夏", 60: "小满", 75: "芒种",
    90: "夏至", 105: "小暑", 120: "大暑", 135: "立秋", 150: "处暑", 165: "白露",
    180: "秋分", 195: "寒露", 210: "霜降", 225: "立冬", 240: "小雪", 255: "大雪",
    270: "冬至", 285: "小寒", 300: "大寒", 315: "立春", 330: "雨水", 345: "惊蛰",
}
UTC_START = datetime(1972, 1, 1, tzinfo=timezone.utc)
CST = timezone(timedelta(hours=8))


def verify(path):
    size = os.path.getsize(path)
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if size != EXPECTED_SIZE or h.hexdigest() != EXPECTED_MD5:
        sys.exit(f"星历校验失败: size={size} md5={h.hexdigest()}")


def civil_utc(t):
    """Skyfield Time → 民用 UTC datetime（未取整）。1972 前用 UT1。"""
    utc = t.utc_datetime()
    if utc >= UTC_START:
        return utc
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=t.ut1 - 2451545.0)


def main():
    bsp, out = sys.argv[1], sys.argv[2]
    verify(bsp)
    ts = api.load.timescale(builtin=True)
    eph = api.load_file(bsp)
    earth, sun = eph["earth"], eph["sun"]

    def term_index(t):
        lat, lon, _ = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)
        return (lon.degrees // 15).astype(int) % 24

    term_index.step_days = 5.0

    t0 = ts.utc(1899, 12, 1)
    t1 = ts.utc(2101, 1, 31)
    times, idx = find_discrete(t0, t1, term_index, epsilon=1e-4 / 86400)

    # 交节点附近浮点抖动会让 find_discrete 报出微秒级的"来回翻转"，只保留每个节气第一次正向跨越
    by_year = {}
    state = None
    for t, i in zip(times, idx):
        i = int(i)
        if state is not None and i != (state + 1) % 24:
            continue
        state = i
        lon = i * 15
        ut = civil_utc(t)
        ut = (ut + timedelta(microseconds=500000)).replace(microsecond=0)
        bj = ut.astimezone(CST)
        if 1900 <= bj.year <= 2100:
            by_year.setdefault(bj.year, []).append((ut, lon, bj))

    rows = []
    for year in range(1900, 2101):
        recs = sorted(by_year[year])
        if len(recs) != 24 or len({r[1] for r in recs}) != 24:
            sys.exit(f"{year} 年节气数异常: {len(recs)}")
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
