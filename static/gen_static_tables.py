#!/usr/bin/env python3
"""
从 Muse 查证交回文件生成六爻、八字静态表（【用户裁决 M1-R、M2-R】，契约附录 R-39.9、R-39.10）。

输入（只读，均已存档）：
  crosscheck/muse/M-1_Muse已填表.md   T1（卦名→宫位世应）、T2～T9
  crosscheck/muse/M-2_Muse已填表.pdf  T1′（爻象→卦名），用 pdftotext -layout 取文本
唯一的人工改值：T8 午支本气 ? → 丁（【用户裁决 M2-R】第 3 项）。
输出：static/*.csv（UTF-8，LF）。脚本自带一致性断言，任何一条不过即报错退出。
用法：python3 static/gen_static_tables.py [输出目录，默认 static]
"""
import csv, io, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "static")
M1 = os.path.join(ROOT, "crosscheck/muse/M-1_Muse已填表.md")
M2 = os.path.join(ROOT, "crosscheck/muse/M-2_Muse已填表.pdf")

def tables_from_md(text):
    out, cur = {}, None
    for ln in text.splitlines():
        m = re.match(r"^#\s*(T\d)\s*$", ln.strip())
        if m: cur = m.group(1); out[cur] = []; continue
        if cur and ln.startswith("```"):
            if out[cur]: cur = None
            continue
        if cur and ln.strip(): out[cur].append(ln)
    return {k: list(csv.reader(io.StringIO("\n".join(v))))[1:] for k, v in out.items()}

m1_text = open(M1, encoding="utf-8").read()
T = tables_from_md(m1_text)

# ---- T1′：爻象 → 上卦、下卦、卦名（M-2 PDF；版式断行时上卦、下卦、卦名在上一行）
pdf = subprocess.run(["pdftotext", "-layout", M2, "-"], capture_output=True, text=True, check=True).stdout.splitlines()
k1 = {}
for i, l in enumerate(pdf):
    m = re.search(r"(K\d\d),([01]{6}),(.*)", l)
    if not m: continue
    k, bits, rest = m.groups(); f = [x.strip() for x in rest.split(",")]
    if f[0] and f[2]: up, lo, name = f[0], f[1], f[2]
    else:
        mm = re.match(r"(\S)\s+(\S)\s+([^,]+),", pdf[i - 1].strip()); up, lo, name = mm.groups()
    k1[bits] = (lo, up, name)
assert len(k1) == 64, f"T1′ 应 64 行，得 {len(k1)}"

# ---- T1（M-1）：卦名 → 宫、宫内位置、世、应
pal = {r[4]: (r[5], r[6], r[7], r[8]) for r in T["T1"]}
assert len(pal) == 64

TRI = {"乾":"111","兑":"110","离":"101","震":"100","巽":"011","坎":"010","艮":"001","坤":"000"}  # 初→三（M-2 所填，下方断言核对）
IMG = {"乾":"天","坤":"地","震":"雷","巽":"风","坎":"水","离":"火","艮":"山","兑":"泽"}
POS = ["本宫","一世","二世","三世","四世","五世","游魂","归魂"]
SHI = {"本宫":6,"一世":1,"二世":2,"三世":3,"四世":4,"五世":5,"游魂":4,"归魂":3}   # P-B-03
hexa = []
for bits, (lo, up, name) in sorted(k1.items(), key=lambda kv: kv[0]):
    assert TRI[lo] == bits[:3] and TRI[up] == bits[3:], f"{bits} 上下卦与爻象不符"
    assert name.startswith(f"{up}为") if up == lo else name.startswith(IMG[up] + IMG[lo]), f"{bits} 卦名不是上卦之象 + 下卦之象：{name}"
    p, pos, shi, ying = pal[name]
    assert pos in POS and int(shi) == SHI[pos] and int(ying) == (int(shi) + 2) % 6 + 1, f"{name} 世应与 P-B-03 不符"
    hexa.append([bits, lo, up, name, p, pos, shi, ying])
for p in TRI:
    rows = [h for h in hexa if h[4] == p]
    assert len(rows) == 8 and sorted(h[5] for h in rows) == sorted(POS), f"{p} 宫不是八卦各一位"
    assert [h for h in rows if h[5] == "本宫"][0][0] == TRI[p] * 2, f"{p} 宫本宫卦不是纯卦"

# ---- 卦宫五行（M-1 T4 来源块所引《卜筮正宗》卷一原句）
m = re.search(r"乾属金，坎属水，艮属土，震、巽属木，离属火，坤属土，兑属金", m1_text)
assert m, "未找到《卜筮正宗》八宫所属原句"
palace_wx = [["乾","金"],["兑","金"],["离","火"],["震","木"],["巽","木"],["坎","水"],["艮","土"],["坤","土"]]

# ---- 其余各表
LINE = {"内卦·初爻":1,"内卦·二爻":2,"内卦·三爻":3,"外卦·四爻":4,"外卦·五爻":5,"外卦·上爻":6}
najia = [[r[1], LINE[r[2]], r[3]] for r in T["T2"]]
branch_wx = [[r[1], r[2]] for r in T["T3"]]
liuqin = [[r[1], r[2], r[3]] for r in T["T4"]]
liushen = [[r[1]] + r[2:8] for r in T["T5"]]
xunkong = [[r[1], r[2], r[3], r[4]] for r in T["T6"]]
shishen = [[r[1], r[2], r[3]] for r in T["T7"]]
canggan = []
for r in T["T8"]:
    zhi, ben, zhong, yu = r[1], r[2], r[3], r[4]
    if zhi == "午" and ben == "?": ben = "丁"   # 【用户裁决 M2-R】第 3 项
    canggan.append([zhi, ben, zhong, yu])
assert all(c[1] != "?" for c in canggan)
changsheng = [[r[2]] + r[3:15] for r in T["T9"]]

for name, n in [("T2", 48), ("T3", 12), ("T4", 25), ("T5", 10), ("T6", 60), ("T7", 100), ("T8", 12), ("T9", 10)]:
    assert len(T[name]) == n, f"{name} 行数 {len(T[name])} ≠ {n}"

def write(fn, header, rows):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(header); w.writerows(rows)

os.makedirs(OUT, exist_ok=True)
write("liuyao_hexagrams.csv", ["bits_bottom_up","lower","upper","name","palace","palace_position","shi","ying"], hexa)
write("liuyao_palace_wuxing.csv", ["palace","wuxing"], palace_wx)
write("liuyao_najia.csv", ["trigram","line","stem_branch"], najia)
write("branch_wuxing.csv", ["branch","wuxing"], branch_wx)
write("liuyao_liuqin.csv", ["self_wuxing","line_wuxing","liuqin"], liuqin)
write("liuyao_liushen.csv", ["day_stem","line1","line2","line3","line4","line5","line6"], liushen)
write("xunkong.csv", ["ganzhi","xun_head","void1","void2"], xunkong)
write("bazi_shishen.csv", ["day_stem","other_stem","shishen"], shishen)
write("bazi_canggan.csv", ["branch","benqi","zhongqi","yuqi"], canggan)
write("bazi_changsheng.csv", ["stem","changsheng","muyu","guandai","linguan","diwang","shuai","bing","si","mu","jue","tai","yang"], changsheng)
print("已生成 10 个静态表到", OUT)
