#!/usr/bin/env python3
"""B4 day-pillar baseline generator (independent of the engine under test).

Generates the continuous 60-cycle day pillar sequence for 1900-01-01 .. 2100-12-31
(proleptic Gregorian civil dates, UTC+8, day rollover 00:00 per CFG-01).
Anchor: 1949-10-01 = 甲子 (contract P-D-04). Index = (date - 1949-10-01) mod 60.
Two independent counting methods are used and must agree on every row:
  A) Python date.toordinal() difference from the anchor
  B) Julian Day Number by the Fliegel-Van Flandern integer formula, (JDN - 11) mod 60
This script shares no code with the XUANSHU engine (none exists yet; contract B4-11).
"""
import csv, datetime, hashlib, sys

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ANCHOR = datetime.date(1949, 10, 1)

def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045

def ganzhi(i):
    return STEMS[i % 10] + BRANCHES[i % 12]

def main(out):
    d = datetime.date(1900, 1, 1)
    end = datetime.date(2100, 12, 31)
    one = datetime.timedelta(days=1)
    n = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "jdn", "cycle_index", "day_pillar"])
        while d <= end:
            ia = (d.toordinal() - ANCHOR.toordinal()) % 60
            j = jdn(d.year, d.month, d.day)
            ib = (j - 11) % 60
            if ia != ib:
                sys.exit(f"method mismatch at {d}: {ia} vs {ib}")
            w.writerow([d.isoformat(), j, ia, ganzhi(ia)])
            d += one
            n += 1
    assert ganzhi((ANCHOR.toordinal() - ANCHOR.toordinal()) % 60) == "甲子"
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print(f"rows={n} sha256={h}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "day_pillars_1900_2100.csv")
