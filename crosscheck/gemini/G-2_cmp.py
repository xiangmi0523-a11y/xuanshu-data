#!/usr/bin/env python3
"""
G-2 比对：Gemini 交回与封存答案逐格比对，并对装卦分歧归因（认卦错误 vs 规则不同）。只读。
用法：python3 crosscheck/gemini/G-2_cmp.py crosscheck/gemini/G-2_Gemini结果_原文.txt crosscheck/gemini/G-2_答案_封存.json crosscheck/oracle/static_oracle.json
"""
import json, re, sys
A = json.load(open(sys.argv[2], encoding="utf-8"))
txt = open(sys.argv[1], encoding="utf-8").read()
POS = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
# ---- 装卦
blocks = re.split(r"\n(?=编号：Z\d\d)", txt.split("二、地支藏干")[0])
G = {}
for b in blocks:
    m = re.search(r"编号：(Z\d\d)", b)
    if not m: continue
    z = {"爻": [], "变爻": {}}
    for ln in b.splitlines():
        ln = ln.strip()
        if ln.startswith("本卦："): f = ln[3:].split("｜"); z.update(本卦=f[0], 宫=f[1], 宫内位置=f[2], 世=int(f[3]), 应=int(f[4]))
        elif re.match(r"^[初二三四五上]爻：", ln):
            f = ln[3:].split("｜"); z["爻"].append({"纳甲": f[0], "五行": f[1], "六亲": f[2], "六神": f[3], "动": "是" if f[4] == "动" else "否"})
        elif ln.startswith("变卦"):
            v = ln.split("：", 1)[1]; z["变卦"], z["变卦宫"] = (None, None) if v == "无" else v.split("｜")
        elif ln.startswith("变爻：") and "无" != ln[3:]:
            f = re.split(r"[｜：]", ln[3:]); z["变爻"][POS[f[0][0]]] = {"纳甲": f[1], "六亲": f[2]}
        elif ln.startswith("旬空："): z["旬空"] = ln[3:]
    G[m.group(1)] = z
rows, stat = [], {}
def c(cat, where, g, w):
    s = stat.setdefault(cat, [0, 0]); s[1] += 1
    if g == w: s[0] += 1
    else: rows.append(f"{where}：Gemini {g} ｜ 封存 {w}")
for a in A["装卦"]:
    k = a["编号"]; g = G[k]
    for f in ["本卦", "宫", "宫内位置", "世", "应"]: c("本卦五项", f"{k} {f}", g[f], a[f])
    for i in range(6):
        for f in ["纳甲", "五行", "六亲", "六神", "动"]: c(f"爻·{f}", f"{k} {i+1}爻{f}", g["爻"][i][f], a["爻"][i][f])
    c("旬空", f"{k} 旬空", g["旬空"], a["旬空"])
    c("变卦名宫", f"{k} 变卦", (g["变卦"], g["变卦宫"]), (a.get("变卦"), a.get("变卦宫")))
    want = {v["爻位"]: v for v in a.get("变爻", [])}
    c("变爻位置", f"{k} 动爻位", sorted(g["变爻"]), sorted(want))
    for p in sorted(set(g["变爻"]) & set(want)):
        for f in ["纳甲", "六亲"]: c(f"变爻·{f}", f"{k} 变爻{p}{f}", g["变爻"][p][f], want[p][f])
# ---- 藏干次序
cg = {l.split(",")[0]: l.split(",")[1:4] for l in re.search(r"地支,本气,中气,余气\n(.*?)\n\n", txt, re.S).group(1).splitlines()}
for r in A["藏干次序"]:
    for f, i in [("本气", 0), ("中气", 1), ("余气", 2)]: c(f"藏干·{f}", f"藏干 {r['地支']}{f}", cg[r["地支"]][i], r[f])
# ---- 八字
bz = [l.split(",") for l in txt.splitlines() if re.match(r"^B\d,", l)]
flat = [(ch["编号"], p) for ch in A["八字"] for p in ch["逐柱"]]
for (bid, p), l in zip(flat, bz):
    assert l[0] == bid and l[1] == p["柱"], (l, bid, p["柱"])
    c("八字·天干十神", f"{bid} {p['柱']} 天干十神", l[2], p["天干十神"])
    c("八字·藏干及十神(集合)", f"{bid} {p['柱']} 藏干十神", sorted(l[3].split("/")), sorted(h + s for h, s in p["藏干"]))
    c("八字·藏干次序", f"{bid} {p['柱']} 藏干次序", [x[0] for x in l[3].split("/")], [h for h, _ in p["藏干"]])
    c("八字·日主长生", f"{bid} {p['柱']} 长生", l[4], p["日主十二长生"])
print("| 类别 | 一致 / 总数 |\n|---|---|")
for k, (o, n) in stat.items(): print(f"| {k} | {o} / {n} |")
print("\n不一致明细："); print("\n".join(rows))

# ---- 分歧归因
O = json.load(open(sys.argv[3], encoding="utf-8"))
byname = {h["name"]: (b, h) for b, h in O["hexagrams"].items()}
INNER = {"甲": "乾", "乙": "坤", "庚": "震", "辛": "巽", "戊": "坎", "己": "离", "丙": "艮", "丁": "兑"}
OUTER = {"壬": "乾", "癸": "坤", "庚": "震", "辛": "巽", "戊": "坎", "己": "离", "丙": "艮", "丁": "兑"}
EL = "木火土金水"
def lq(me, x): return ["兄弟", "子孙", "妻财", "官鬼", "父母"][(EL.index(x) - EL.index(me)) % 5]
print("| 例 | 爻值 | 应为（由爻值） | Gemini 卦名 | Gemini 纳甲所示上/下卦 | 卦名与其纳甲是否同一卦 | 宫位世应按其卦名是否合我方表 | 六亲按其所称宫五行是否自洽 | 动爻 |")
print("|---|---|---|---|---|---|---|---|---|")
for a in A["装卦"]:
    k, y = a["编号"], a["爻值"]; g = G[k]
    lo = INNER[g["爻"][0]["纳甲"][0]]; up = OUTER[g["爻"][3]["纳甲"][0]]
    b, h = byname[g["本卦"]]
    same = (h["lower"], h["upper"]) == (lo, up)
    rule = (h["palace"], h["palace_position"], h["shi"], h["ying"]) == (g["宫"], g["宫内位置"], g["世"], g["应"])
    me = O["palace_wuxing"][g["宫"]]
    selfc = all(l["六亲"] == lq(me, l["五行"]) for l in g["爻"])
    mv_y = [i + 1 for i, v in enumerate(y) if v in "69"]; mv_g = [i + 1 for i, l in enumerate(g["爻"]) if l["动"] == "是"]
    print(f"| {k} | {' '.join(y)} | {a['本卦']} | {g['本卦']} | 上{up} 下{lo} | {'是' if same else '否（卦名=上' + h['upper'] + '下' + h['lower'] + '）'} | {'合' if rule else '不合'} | {'自洽' if selfc else '不自洽'} | {'对' if mv_y == mv_g else '错：应' + str(mv_y) + ' 填' + str(mv_g)} |")

print("\n按 Gemini 自己所用的上下卦（由其纳甲判定）核其六爻纳甲、五行；按其所称变卦核变爻纳甲：")
tot = ok = 0; bad = []
for a in A["装卦"]:
    k = a["编号"]; g = G[k]
    lo = INNER[g["爻"][0]["纳甲"][0]]; up = OUTER[g["爻"][3]["纳甲"][0]]
    hb = next(h for h in O["hexagrams"].values() if (h["lower"], h["upper"]) == (lo, up))
    for i, l in enumerate(g["爻"]):
        for f, w in [("纳甲", hb["najia"][i]), ("五行", hb["wuxing"][i])]:
            tot += 1; ok += l[f] == w
            if l[f] != w: bad.append(f"{k} {i+1}爻{f} {l[f]}≠{w}")
    if g["变卦"]:
        bb, hv = byname[g["变卦"]]
        for p, v in g["变爻"].items():
            tot += 1; ok += v["纳甲"] == hv["najia"][p - 1]
            if v["纳甲"] != hv["najia"][p - 1]: bad.append(f"{k} 变爻{p} {v['纳甲']}≠{hv['najia'][p-1]}（按其所称变卦 {g['变卦']}）")
print(f"一致 {ok} / {tot}"); print("\n".join(bad))
