#!/usr/bin/env python3
"""
独立正确性基准（L3）生成脚本 —— E2-A 第 1 项全系统审查（2026-11-21）。

用途：为十张静态表与两种计算（六爻装卦、八字查表）生成**全覆盖**的独立期望值，
供 checks/verify.py::check_static_oracle（数据仓库 CI）与引擎 test/oracle.test.ts（引擎 CI）逐格比对。

独立性（与被测对象分开的依据）：
- **不读** static/*.csv，**不读** Muse 已填表，不调用引擎。
- 规则推算全部来自 crosscheck/gemini/G-1_对照推算_ref.py（G-1 时按通行规则机械推算：八宫由本宫纯卦逐爻变出、
  纳甲按歌诀、六亲按五行生克、六神按起首轮转、十神按五行生克 × 阴阳同异、十二长生按起点 + 顺逆）。
  与 Muse 的古籍查证是不同方法、不同链条。
- 八宫五行用八卦五行（本文件 PALACE_WUXING，八卦取象通说）。
- 藏干只给“所藏之干的集合”，文本从 crosscheck/muse/M-2_Muse交回报告.pdf 所录《渊海子平评注》
  〈又地支藏遁歌〉原文（来源 B，行 1364）用 pdftotext 抽取，不手抄。本气、中气、余气的**次序**没有独立来源，不在基准内。
- 动变按 P-B-08：老阴 6、老阳 9 为动爻，翻转得变卦。

用法：python3 crosscheck/oracle/gen_oracle.py [输出文件，默认 crosscheck/oracle/static_oracle.json]
"""
import hashlib, itertools, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(ROOT, "crosscheck/gemini/G-1_对照推算_ref.py")
M2 = os.path.join(ROOT, "crosscheck/muse/M-2_Muse交回报告.pdf")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "crosscheck/oracle/static_oracle.json")

ref = {}
exec(open(REF, encoding="utf-8").read(), ref)
S, B, TRI, PAL, NAJIA, BEL, GODS, GSTART, CS, STATES = (ref[k] for k in
    ["S", "B", "TRI", "PAL", "NAJIA", "BEL", "GODS", "GSTART", "CS", "STATES"])
fullname, liuqin, shishen = ref["fullname"], ref["liuqin"], ref["shishen"]

PALACE_WUXING = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
JIAZI = [S[i % 10] + B[i % 12] for i in range(60)]

# ---- 藏干歌诀：从 M-2 交回报告 PDF 抽取原文
txt = re.sub(r"\s+", "", subprocess.run(["pdftotext", M2, "-"], capture_output=True, text=True, check=True).stdout)
m = re.search(r"子宫癸水在其中，(?:[^，。]{6,7}，){10}[^，。]{6,7}。", txt)
assert m, "M-2 报告中未找到〈又地支藏遁歌〉全文"
song = m.group(0)
clauses = song.rstrip("。").split("，")
assert len(clauses) == 12 and [c[0] for c in clauses] == list(B), "歌诀应按子至亥十二句"
canggan_sets = {c[0]: sorted({x for x in c[1:] if x in S}, key=S.index) for c in clauses}

# ---- 六十四卦（含每爻纳甲与五行）
hexagrams = {}
for bits in ("".join(t) for t in itertools.product("01", repeat=6)):
    lo, up = TRI[bits[:3]], TRI[bits[3:]]
    palace, pos, shi, ying = PAL[bits]
    najia = [NAJIA[lo if i < 3 else up][i] for i in range(6)]
    hexagrams[bits] = {"lower": lo, "upper": up, "name": fullname(up, lo), "palace": palace, "palace_position": pos,
                       "shi": shi, "ying": ying, "najia": najia, "wuxing": [BEL[g[1]] for g in najia]}
assert len(hexagrams) == 64 and len({h["name"] for h in hexagrams.values()}) == 64

# ---- 各卦在各宫五行为“我”时的六亲（装卦：本卦与变卦都以本卦宫五行为我，P-B-04）
liuqin_by_self = {me: {b: [liuqin(me, w) for w in h["wuxing"]] for b, h in hexagrams.items()} for me in "木火土金水"}

# ---- 起卦：4096 种爻值 → 本卦、变卦、动爻（P-B-08）
yao = {}
for vals in itertools.product((6, 7, 8, 9), repeat=6):
    ben = "".join("1" if v in (7, 9) else "0" for v in vals)
    moving = [i + 1 for i, v in enumerate(vals) if v in (6, 9)]
    bian = "".join(("0" if ben[i] == "1" else "1") if (i + 1) in moving else ben[i] for i in range(6)) if moving else None
    yao["".join(map(str, vals))] = [ben, bian, moving]

def xun(gz):
    i = JIAZI.index(gz); h = i - i % 10
    return [JIAZI[h], B[(h + 10) % 12], B[(h + 11) % 12]]

oracle = {
    "meta": {
        "purpose": "E2-A 第 1 项独立正确性基准（L3）；不读 static/*.csv、不读 Muse 已填表、不调用引擎",
        "ref": "crosscheck/gemini/G-1_对照推算_ref.py",
        "ref_sha256": hashlib.sha256(open(REF, "rb").read()).hexdigest(),
        "canggan_song_source": "crosscheck/muse/M-2_Muse交回报告.pdf 来源 B《渊海子平评注》卷一〈又地支藏遁歌〉（行 1364）",
        "canggan_song": song,
        "not_covered": ["藏干本气、中气、余气的次序（R-39.9 现代整理层，无独立来源）"],
    },
    "hexagrams": hexagrams,
    "palace_wuxing": PALACE_WUXING,
    "najia": NAJIA,
    "branch_wuxing": {b: BEL[b] for b in B},
    "liuqin": {f"{a}|{b}": liuqin(a, b) for a in "木火土金水" for b in "木火土金水"},
    "liushen": {s: [GODS[(GSTART[s] + k) % 6] for k in range(6)] for s in S},
    "xunkong": {gz: xun(gz) for gz in JIAZI},
    "shishen": {f"{d}|{o}": shishen(d, o) for d in S for o in S},
    "canggan_sets": canggan_sets,
    "changsheng": {s: [B[(B.index(CS[s][0]) + CS[s][1] * k) % 12] for k in range(12)] for s in S},
    "changsheng_states": STATES,
    "liuqin_by_self": liuqin_by_self,
    "yao": yao,
}
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(oracle, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    f.write("\n")
print("已生成独立基准", OUT)
