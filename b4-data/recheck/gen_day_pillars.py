#!/usr/bin/env python3
"""
玄枢 B4 回归基准数据 —— 1900-01-01 至 2100-12-31 逐日日柱（六十甲子）序列（独立生成脚本）

本脚本只用于生成基准数据，不与排盘引擎共用任何代码（【用户裁决 B4-11】）。

用法:
    python3 gen_day_pillars.py out.csv

规则（契约 §13.5 / CFG-01 / P-D-04）:
* 按公历日期编号，UTC+8 民用日、00:00 换日；
* 锚点 1949-10-01 = 甲子（序 0）；
* 每一天用两种互不依赖的方法各算一次，全部一致才输出:
    方法 A: Python date 序数差  (d.toordinal() − anchor.toordinal()) mod 60
    方法 B: 儒略日数整数公式（Fliegel–Van Flandern）  (JDN(d) − JDN(anchor)) mod 60
输出列: date, day_pillar, sexagenary_index（0 = 甲子 … 59 = 癸亥）
"""
import csv
import sys
from datetime import date, timedelta

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
GANZHI = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]
ANCHOR = date(1949, 10, 1)
START, END = date(1900, 1, 1), date(2100, 12, 31)


def jdn(y, m, d):
    """公历日期 → 儒略日数（整数公式，不经过 datetime）。"""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def main():
    out = sys.argv[1]
    assert GANZHI[0] == "甲子" and GANZHI[59] == "癸亥" and len(set(GANZHI)) == 60
    assert jdn(2000, 1, 1) == 2451545
    anchor_jdn = jdn(ANCHOR.year, ANCHOR.month, ANCHOR.day)
    rows = []
    d = START
    while d <= END:
        a = (d.toordinal() - ANCHOR.toordinal()) % 60
        b = (jdn(d.year, d.month, d.day) - anchor_jdn) % 60
        if a != b:
            sys.exit(f"两种方法不一致: {d} {a} {b}")
        rows.append([d.isoformat(), GANZHI[a], a])
        d += timedelta(days=1)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "day_pillar", "sexagenary_index"])
        w.writerows(rows)
    print(f"写出 {len(rows)} 行 → {out}")


if __name__ == "__main__":
    main()
