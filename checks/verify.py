#!/usr/bin/env python3
"""
玄枢数据仓库核对脚本 —— 本仓库唯一的"对不对"判据。

用法:
    python3 checks/verify.py            # 快速核对（几秒）
    python3 checks/verify.py --regen    # 另外用生成脚本重跑，比对哈希（需 skyfield，约 30 秒）

退出码 0 = 全部通过（PENDING 不算失败）；1 = 有失败项。
本脚本不与排盘引擎共用任何代码【B4-11】。
"""
import csv
import hashlib
import os
import subprocess
import sys
import tempfile
import tomllib
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
GANZHI = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]
TERMS = {
    0: "春分", 15: "清明", 30: "谷雨", 45: "立夏", 60: "小满", 75: "芒种",
    90: "夏至", 105: "小暑", 120: "大暑", 135: "立秋", 150: "处暑", 165: "白露",
    180: "秋分", 195: "寒露", 210: "霜降", 225: "立冬", 240: "小雪", 255: "大雪",
    270: "冬至", 285: "小寒", 300: "大寒", 315: "立春", 330: "雨水", 345: "惊蛰",
}

results = []  # (status, section, message)


def ok(sec, msg): results.append(("PASS", sec, msg))
def fail(sec, msg): results.append(("FAIL", sec, msg))
def pending(sec, msg): results.append(("PENDING", sec, msg))


def p(rel): return os.path.join(ROOT, rel)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(rel):
    with open(p(rel), encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


# ------------------------------------------------------------------ 1. 清单
def check_manifest(manifest):
    sec = "清单"
    listed = set()
    contract = open(p("contract/玄枢数据契约_v1.0.md"), encoding="utf-8").read()
    for e in manifest["file"]:
        rel = e["path"]
        listed.add(rel)
        if not os.path.exists(p(rel)):
            if e["status"] == "pending":
                pending(sec, f"{rel} 尚未放入仓库")
            else:
                fail(sec, f"{rel} 缺失（status={e['status']}）")
            continue
        if "sha256" not in e:
            fail(sec, f"{rel} 已在仓库但清单没登记 sha256")
            continue
        got = sha256(p(rel))
        if got != e["sha256"]:
            fail(sec, f"{rel} sha256 不符：清单 {e['sha256'][:12]}… 实际 {got[:12]}…")
            continue
        if "md5" in e and md5(p(rel)) != e["md5"]:
            fail(sec, f"{rel} md5 不符")
            continue
        if "bytes" in e and os.path.getsize(p(rel)) != e["bytes"]:
            fail(sec, f"{rel} 大小不符")
            continue
        if "rows" in e:
            n = len(read_csv(rel)) - 1
            if n != e["rows"]:
                fail(sec, f"{rel} 行数 {n}，清单 {e['rows']}")
                continue
        if e["status"] == "frozen":
            if e["sha256"] not in contract:
                fail("冻结", f"{rel} 已冻结，但契约正文没有载明定稿哈希 {e['sha256'][:12]}…")
            else:
                ok("冻结", f"{rel} 定稿哈希 {e['sha256'][:12]}… 与契约正文一致，文件未改动")
            continue
        ok(sec, f"{rel} 哈希一致")
    # 反向：仓库里的数据文件都得登记
    for top in ("ephemeris", "jieqi", "b4-data", "almanac", "contract"):
        for dirpath, _, files in os.walk(p(top)):
            for fn in files:
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
                if rel not in listed and not fn.startswith("."):
                    fail(sec, f"{rel} 在仓库里但没登记在 manifest.toml")


# ------------------------------------------------------------------ 2. 节气表
def load_jieqi():
    rows = read_csv("jieqi/jieqi_1900_2100_utc_skyfield.csv")
    return rows[0], rows[1:]


def check_jieqi(header, rows):
    sec = "节气表"
    want = ["year", "term", "ecliptic_longitude", "term_utc8_iso", "term_utc_iso"]
    if header != want:
        fail(sec, f"表头不符：{header}")
        return
    errs = []
    per_year = defaultdict(list)
    prev = None
    for r in rows:
        y, term, lon, t8, tu = r
        lon = int(lon)
        if TERMS.get(lon) != term:
            errs.append(f"{y} {term} 黄经 {lon} 对不上")
        d8 = datetime.fromisoformat(t8)
        du = datetime.fromisoformat(tu.replace("Z", "+00:00"))
        if d8 != du:
            errs.append(f"{y} {term} 北京时间与 UTC 不是同一时刻")
        if d8.utcoffset() != timedelta(hours=8):
            errs.append(f"{y} {term} 时区不是 +08:00")
        if d8.year != int(y):
            errs.append(f"{y} {term} 落在 {d8.year} 年")
        if prev and d8 <= prev:
            errs.append(f"{y} {term} 时间没有递增")
        prev = d8
        per_year[int(y)].append(term)
    years = sorted(per_year)
    if years != list(range(1900, 2101)):
        errs.append("年份不是 1900–2100 连续")
    bad = [y for y in years if len(per_year[y]) != 24 or len(set(per_year[y])) != 24]
    if bad:
        errs.append(f"每年不足/多于 24 个节气：{bad[:5]}")
    if errs:
        for e in errs[:10]:
            fail(sec, e)
    else:
        ok(sec, f"{len(rows)} 行结构正确：201 年×24 节气，时区一致，时间递增")


# ------------------------------------------------------------------ 3. 日柱
def load_day_pillars(rel):
    with open(p(rel), encoding="utf-8", newline="") as f:
        return {r["date"]: r["day_pillar"] for r in csv.DictReader(f)}


def check_day_pillars(rel, dp):
    sec = f"日柱 {rel}"
    errs = []
    d, end = date(1900, 1, 1), date(2100, 12, 31)
    anchor = date(1949, 10, 1)
    n = 0
    while d <= end:
        k = d.isoformat()
        want = GANZHI[(d - anchor).days % 60]
        if dp.get(k) != want:
            errs.append(f"{k} 为 {dp.get(k)}，按锚点推算应为 {want}")
        n += 1
        d += timedelta(days=1)
    if len(dp) != n:
        errs.append(f"共 {len(dp)} 天，应为 {n} 天")
    if errs:
        for e in errs[:10]:
            fail(sec, e)
    else:
        ok(sec, f"{n} 天连续，全部与 1949-10-01 甲子锚点推算一致")


def check_day_pillars_agree(a, b):
    sec = "日柱 正式 vs 复算"
    diff = [k for k in a if a.get(k) != b.get(k)]
    if diff or len(a) != len(b):
        fail(sec, f"{len(diff)} 天不同，首个 {diff[:3]}")
    else:
        ok(sec, f"两份逐日相同（{len(a)} 天）")


# ------------------------------------------------------------------ 4. 已定结论
def check_constants(c, jieqi_rows, dp):
    by_key = {(int(r[0]), r[1]): datetime.fromisoformat(r[3]) for r in jieqi_rows}

    sec = "金值"
    for g in c.get("golden_term", []):
        got = by_key.get((g["year"], g["term"]))
        want = datetime.fromisoformat(g["utc8"])
        (ok if got == want else fail)(sec, f"{g['year']} {g['term']} 表中 {got:%m-%d %H:%M:%S}，应为 {want:%m-%d %H:%M:%S}")
    if dp:
        for g in c.get("golden_day", []):
            got = dp.get(g["date"])
            (ok if got == g["pillar"] else fail)(sec, f"{g['date']} 日柱 {got}，应为 {g['pillar']}")

    sec = "叠加用例（规则 2）"
    sel = c["superposition_selector"]
    m = timedelta(minutes=sel["min_margin_minutes"])
    for case in c["superposition_case"]:
        t = by_key.get((case["decided_year"], case["term"]))
        want_t = datetime.fromisoformat(case["term_utc8"])
        if t != want_t:
            fail(sec, f"{case['id']} 交节 {t}，登记为 {want_t}")
            continue
        D = (t + timedelta(hours=1)).date() if t.hour == 23 else t.date()
        if D.isoformat() != case["fixed_utc8_date"]:
            fail(sec, f"{case['id']} D 应为 {D}，登记为 {case['fixed_utc8_date']}")
            continue
        if dp:
            cands = [dp[(D - timedelta(days=1)).isoformat()], dp[D.isoformat()]]
            if cands != case["day_candidates"]:
                fail(sec, f"{case['id']} 日柱候选 {cands}，登记为 {case['day_candidates']}")
                continue
        if not case["required"]:
            ok(sec, f"{case['id']}（可选）交节、D、日柱候选与登记一致")
            continue
        hits = []
        for (y, term), tt in sorted(by_key.items()):
            if term != case["term"] or y < sel["min_year"] or tt.hour != sel["term_hour"]:
                continue
            h23 = tt.replace(minute=0, second=0)
            if tt - h23 > m and h23 + timedelta(hours=1) - tt > m:
                hits.append(y)
        picked = hits[0] if hits else None
        (ok if picked == case["decided_year"] else fail)(
            sec, f"{case['term']} 按规则 2 筛得 {picked}（全部 {hits}），已定 {case['decided_year']}")

    sec = "年历舍入跨日"
    for e in c["almanac"]["rounding_cross_midnight"]:
        got = by_key.get((e["year"], e["term"]))
        want = datetime.fromisoformat(e["baseline_utc8"])
        (ok if got == want else fail)(sec, f"{e['year']} {e['term']} 基准表 {got}，登记 {want}")



# ------------------------------------------------------------------ 5. 年历比对【§13.5 / B4-15 / B4-17】
def check_almanac_terms(c, jieqi_rows):
    sec = "年历节气比对"
    rel = "almanac/zjs_terms_1900_2025_extracted.csv"
    if not os.path.exists(p(rel)):
        pending(sec, "紫金山日历抄取结果尚未放入")
        return
    alm = c["almanac"]
    y0, y1 = alm["almanac_years"]
    base = {(int(r[0]), r[1]): datetime.fromisoformat(r[3]).replace(tzinfo=None) for r in jieqi_rows}
    with open(p(rel), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    seen, over, nonexact, datediff = set(), [], set(), set()
    exact = 0
    for r in rows:
        key = (int(r["year"]), r["term"])
        seen.add(key)
        a = datetime(key[0], int(r["month"]), int(r["day"]), int(r["hour"]), int(r["minute"]))
        s = base[key]
        rnd = (s + timedelta(seconds=30)).replace(second=0, microsecond=0)
        if abs((a - s).total_seconds()) > alm["tolerance_seconds"]:
            over.append(f"{key[0]} {key[1]} 年历 {a:%m-%d %H:%M} 基准 {s:%m-%d %H:%M:%S}")
        if a == rnd:
            exact += 1
        else:
            nonexact.add(f"{key[0]} {key[1]}")
        if a.date() != s.date():
            datediff.add(f"{key[0]} {key[1]}")
    want = {(y, t) for (y, t) in base if y0 <= y <= y1}
    if seen != want:
        fail(sec, f"抄取条目与 {y0}–{y1} 基准不对应：缺 {len(want - seen)}，多 {len(seen - want)}")
    if over:
        for o in over[:10]:
            fail(sec, f"差异超过 1 分钟，需查影印本：{o}")
    else:
        ok(sec, f"{len(rows)} 条全部在 ±1 分钟内；{exact} 条与基准四舍五入到分完全相同，{len(nonexact)} 条差 1 分钟")
    cross = {f"{e['year']} {e['term']}" for e in alm["rounding_cross_midnight"]}
    extra = datediff - cross
    (ok if not extra else fail)(sec, "日期不同的条目都已登记为舍入跨日" if not extra else f"未登记的跨日条目：{sorted(extra)}")
    checked = set(alm["visual_checked"])
    flagged = nonexact | datediff
    if flagged == checked:
        ok(sec, f"需要对图的 {len(flagged)} 条与已对图清单完全一致")
    else:
        fail(sec, f"需对图未对：{sorted(flagged - checked)}；清单多出：{sorted(checked - flagged)}")


def check_almanac_days(dp):
    sec = "年历日干支比对"
    pdf = "almanac/紫金山天文台_1900-2025年日历.pdf"
    if not os.path.exists(p(pdf)):
        pending(sec, "紫金山日历 PDF 尚未放入")
        return
    if not dp:
        pending(sec, "日柱序列尚未放入")
        return
    import calendar, re, shutil
    if not shutil.which("pdftotext"):
        pending(sec, "本机没有 pdftotext，跳过（CI 会装）")
        return
    with tempfile.TemporaryDirectory() as td:
        txt = os.path.join(td, "zjs.txt")
        subprocess.run(["pdftotext", "-layout", p(pdf), txt], check=True)
        lines = open(txt, encoding="utf-8").read().split("\n")
    gz = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")
    year = months = None
    seen, bad, rowfail = Counter(), [], 0
    for line in lines:
        m = re.search(r"公元\s*(\d{4})\s*年", line)
        if m:
            year, months = int(m.group(1)), None
            continue
        mm = re.findall(r"(\d{1,2})\s*月", line)
        if len(mm) == 4 and "日" not in line and year:
            months = [int(x) for x in mm]
            continue
        m = re.match(r"\s*(\d{1,2})\s+\S", line)
        if m and months and year and not re.search(r"[时分]", line):
            d = int(m.group(1))
            if not 1 <= d <= 31:
                continue
            toks = gz.findall(line[m.end() - 1:])
            have = [mo for mo in months if d <= calendar.monthrange(year, mo)[1]]
            if len(toks) != len(have):
                rowfail += 1
                continue
            for mo, t in zip(have, toks):
                k = f"{year}-{mo:02d}-{d:02d}"
                seen[k] += 1
                if dp.get(k) != t:
                    bad.append(f"{k} 年历 {t} 序列 {dp.get(k)}")
    expect = (date(2025, 12, 31) - date(1900, 1, 1)).days + 1
    dup = sum(1 for v in seen.values() if v > 1)
    if bad or rowfail or len(seen) != expect or dup:
        fail(sec, f"覆盖 {len(seen)}/{expect} 天，不一致 {len(bad)}，行解析失败 {rowfail}，重复 {dup}；{bad[:3]}")
    else:
        ok(sec, f"1900–2025 共 {expect} 天逐日比对，年历与日柱序列全部一致")


def check_almanac_reparse():
    sec = "年历抄取复现"
    pdf = p("almanac/紫金山天文台_1900-2025年日历.pdf")
    script = p("almanac/scripts/parse_zjs.py")
    ext = p("almanac/zjs_terms_1900_2025_extracted.csv")
    import shutil
    if not (os.path.exists(pdf) and os.path.exists(script) and os.path.exists(ext)):
        pending(sec, "PDF、抄取脚本或抄取结果未齐")
        return
    if not shutil.which("pdftotext"):
        pending(sec, "本机没有 pdftotext，跳过（CI 会装）")
        return
    with tempfile.TemporaryDirectory() as td:
        txt, out = os.path.join(td, "zjs.txt"), os.path.join(td, "re.csv")
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
        subprocess.run([sys.executable, "-I", script, txt, out], check=True, capture_output=True)
        with open(out, encoding="utf-8", newline="") as f:
            again = {(r["year"], r["term"]): r for r in csv.DictReader(f)}
    with open(ext, encoding="utf-8", newline="") as f:
        stored = list(csv.DictReader(f))
    cols = ["month", "day", "hour", "minute", "footnote", "txt_line"]
    differ = {(r["year"], r["term"]) for r in stored
              if (r["year"], r["term"]) not in again or any(again[(r["year"], r["term"])][c] != r[c] for c in cols)}
    fixed = {(r["year"], r["term"]) for r in stored if r.get("note") == "parse_fixed_by_page_text"}
    if differ == fixed and len(again) == len(stored):
        ok(sec, f"从 PDF 重跑抄取脚本得 {len(again)} 条，与抄取结果一致；唯一不同的是已登记的手工更正行 {sorted(' '.join(k) for k in fixed)}")
    else:
        fail(sec, f"重跑结果与抄取 CSV 不符：未登记的差异 {sorted(differ - fixed)[:5]}，登记了却没差异 {sorted(fixed - differ)}")


def check_visual_readme(c):
    sec = "对图证据"
    rel = "almanac/visual_check_24/README.txt"
    if not os.path.exists(p(rel)):
        pending(sec, "对图 README 尚未放入")
        return
    import re
    txt = open(p(rel), encoding="utf-8").read()
    listed = {f"{y} {t}" for y, t in re.findall(r"#\d+\s*(\d{4})\s*(\S{2})\s*p\d+", txt)}
    want = set(c["almanac"]["visual_checked"])
    (ok if listed == want else fail)(sec, f"README 列出 {len(listed)} 条，与 constants.toml 清单{'一致' if listed == want else '不一致：' + str(sorted(listed ^ want))}")


def check_hko(jieqi_rows):
    sec = "香港天文台日期比对"
    rel = "jieqi/hko_dates_sample_12y.txt"
    if not os.path.exists(p(rel)):
        pending(sec, "抽样文件尚未放入")
        return
    trad = {"驚蟄": "惊蛰", "小滿": "小满", "穀雨": "谷雨", "處暑": "处暑", "芒種": "芒种"}
    base = {(int(r[0]), r[1]): datetime.fromisoformat(r[3]).strftime("%m-%d") for r in jieqi_rows}
    n, bad = 0, []
    for line in open(p(rel), encoding="utf-8"):
        if ":" not in line:
            continue
        y, rest = line.split(":", 1)
        for item in rest.split(","):
            name, md = item.split()
            name = trad.get(name, name)
            n += 1
            if base.get((int(y), name)) != md:
                bad.append(f"{y} {name} 天文台 {md} 基准 {base.get((int(y), name))}")
    if bad:
        for b in bad[:10]:
            fail(sec, b)
    else:
        ok(sec, f"{n} 个节气日期与基准表全部同日（日期级第二来源，DATE_LEVEL_DUAL）")

# ------------------------------------------------------------------ 6. 重跑
def check_regen(manifest):
    sec = "重跑复现"
    for e in manifest["file"]:
        cmd = e.get("regen_cmd")
        if not cmd or not os.path.exists(p(e["path"])):
            continue
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "out.csv")
            r = subprocess.run(cmd.format(out=out), shell=True, cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(sec, f"{e['path']} 生成脚本出错：{r.stderr.strip()[-200:]}")
                continue
            got = sha256(out)
            (ok if got == e["sha256"] else fail)(sec, f"{e['path']} 重跑哈希 {'一致' if got == e['sha256'] else '不符：' + got[:12]}")


def main():
    with open(p("manifest.toml"), "rb") as f:
        manifest = tomllib.load(f)
    with open(p("constants.toml"), "rb") as f:
        consts = tomllib.load(f)

    check_manifest(manifest)
    header, jrows = load_jieqi()
    check_jieqi(header, jrows)

    dp_formal = dp_recheck = None
    if os.path.exists(p("b4-data/day_pillars_1900_2100.csv")):
        dp_formal = load_day_pillars("b4-data/day_pillars_1900_2100.csv")
        check_day_pillars("b4-data/day_pillars_1900_2100.csv", dp_formal)
    if os.path.exists(p("b4-data/recheck/day_pillars_1900_2100.csv")):
        dp_recheck = load_day_pillars("b4-data/recheck/day_pillars_1900_2100.csv")
        check_day_pillars("b4-data/recheck/day_pillars_1900_2100.csv", dp_recheck)
    if dp_formal and dp_recheck:
        check_day_pillars_agree(dp_formal, dp_recheck)

    check_constants(consts, jrows, dp_formal or dp_recheck)

    check_almanac_terms(consts, jrows)
    check_almanac_days(dp_formal or dp_recheck)
    check_almanac_reparse()
    check_visual_readme(consts)
    check_hko(jrows)

    if "--regen" in sys.argv:
        check_regen(manifest)

    icon = {"PASS": "✅", "FAIL": "❌", "PENDING": "⏳"}
    for st, sec, msg in results:
        print(f"{icon[st]} [{sec}] {msg}")
    cnt = Counter(st for st, _, _ in results)
    print(f"\n通过 {cnt['PASS']}，失败 {cnt['FAIL']}，待补 {cnt['PENDING']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## 玄枢数据核对\n\n通过 {cnt['PASS']}，失败 {cnt['FAIL']}，待补 {cnt['PENDING']}\n\n")
            for st, sec, msg in results:
                if st != "PASS":
                    f.write(f"- {icon[st]} **{sec}**：{msg}\n")
    sys.exit(1 if cnt["FAIL"] else 0)


if __name__ == "__main__":
    main()
