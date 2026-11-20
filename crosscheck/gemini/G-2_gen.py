#!/usr/bin/env python3
"""
G-2 盲核对任务生成（E2-A 第 1 项全系统审查，2026-11-21）。
输出：G-2_任务书与空白表.md（交 Gemini，不含答案）、G-2_答案_封存.json（不外发；sha256 记入审查报告作为封存凭据）。
答案来源：crosscheck/oracle/static_oracle.json（独立基准，已在 CI 与 static/*.csv 逐格一致）；藏干三列次序取 static/bazi_canggan.csv（整理层，正是要盲核的对象）。
抽样：random.Random(20261121)，另强制覆盖戊日、己日、静卦、六爻全动、跨宫变卦。
"""
import csv, hashlib, json, os, random
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
O = json.load(open(os.path.join(ROOT, "crosscheck/oracle/static_oracle.json"), encoding="utf-8"))
S, B = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
JIAZI = [S[i % 10] + B[i % 12] for i in range(60)]
rng = random.Random(20261121)

cases = [("777777", "戊午"), ("696969", "己卯")]                          # 静卦戊日；六爻全动己日
while len(cases) < 12:
    y = "".join(rng.choice("6789") for _ in range(6)); d = rng.choice(JIAZI)
    if (y, d) not in cases: cases.append((y, d))
def zg(y, d):
    ben, bian, mv = O["yao"][y]; h = O["hexagrams"][ben]; me = O["palace_wuxing"][h["palace"]]
    lines = [{"纳甲": h["najia"][i], "五行": h["wuxing"][i], "六亲": O["liuqin_by_self"][me][ben][i], "六神": O["liushen"][d[0]][i], "动": "是" if i + 1 in mv else "否"} for i in range(6)]
    out = {"本卦": h["name"], "宫": h["palace"], "宫内位置": h["palace_position"], "世": h["shi"], "应": h["ying"], "爻": lines, "旬空": O["xunkong"][d][1] + O["xunkong"][d][2]}
    if bian:
        g = O["hexagrams"][bian]
        out.update({"变卦": g["name"], "变卦宫": g["palace"], "变爻": [{"爻位": i, "纳甲": g["najia"][i - 1], "六亲": O["liuqin_by_self"][me][bian][i - 1]} for i in mv]})
    return out
answers = {"装卦": [{"编号": f"Z{k + 1:02d}", "爻值": y, "日辰": d, **zg(y, d)} for k, (y, d) in enumerate(cases)]}
assert any(O["yao"][y][1] and O["hexagrams"][O["yao"][y][0]]["palace"] != O["hexagrams"][O["yao"][y][1]]["palace"] for y, _ in cases), "须含跨宫变卦"
cg = {r["branch"]: [r["benqi"], r["zhongqi"], r["yuqi"]] for r in csv.DictReader(open(os.path.join(ROOT, "static/bazi_canggan.csv"), encoding="utf-8"))}
answers["藏干次序"] = [{"地支": b, "本气": cg[b][0], "中气": cg[b][1], "余气": cg[b][2]} for b in B]
charts = [["庚午", "甲申", "壬子", "丁未"], ["癸卯", "乙卯", "己酉", "甲子"], ["戊辰", "辛酉", "乙亥", "丙戌"]]
def bz(p):
    d = p[2][0]
    return [{"柱": x, "天干十神": "日主" if i == 2 else O["shishen"][f"{d}|{x[0]}"],
             "藏干": [[h, O["shishen"][f"{d}|{h}"]] for h in cg[x[1]] if h],
             "日主十二长生": O["changsheng_states"][O["changsheng"][d].index(x[1])]} for i, x in enumerate(p)]
answers["八字"] = [{"编号": f"B{k + 1}", "四柱": p, "逐柱": bz(p)} for k, p in enumerate(charts)]

ans_path = os.path.join(ROOT, "crosscheck/gemini/G-2_答案_封存.json")
with open(ans_path, "w", encoding="utf-8", newline="\n") as f: json.dump(answers, f, ensure_ascii=False, indent=1); f.write("\n")

L = ["# 盲核对任务 G-2：六爻装卦与八字查表（第三方独立推算）", "",
"## 说明", "",
"- 请**完全独立**推算，不要使用任何在线排盘工具或程序的输出；按你掌握的古籍规则逐项推算。",
"- 规则口径：京房八宫纳甲体系；六亲以**本卦所属宫的五行**为“我”，变卦各爻的六亲**仍以本卦宫五行为我**；六神按占日日干起，自初爻排到上爻；旬空按占日日辰所在之旬。",
"- 爻值写法：从初爻（最下）到上爻（最上）六个数字，6 老阴（动）、7 少阳、8 少阴、9 老阳（动）。动爻阴阳翻转得变卦。",
"- 八字部分：十神以日干为“我”；藏干按《渊海子平》，三列按**通行整理次序**写本气、中气、余气（没有的留空）；十二长生按阳干顺行、阴干逆行、戊从丙、己从丁。",
"- 不确定的格子填 `?`，不要猜；每一部分末尾写一句你依据的规则或书名。", "",
"## 一、装卦（12 例）", "",
"每例按下列格式填写（爻从初爻到上爻各一行）：", "",
"```", "编号：", "本卦：卦名｜宫｜宫内位置（本宫/一世…五世/游魂/归魂）｜世爻｜应爻",
"初爻：纳甲干支｜五行｜六亲｜六神｜动否", "（二爻至上爻同上）", "变卦（无动爻写“无”）：卦名｜宫", "变爻：爻位｜纳甲干支｜六亲（依本卦宫）", "旬空：两支", "```", "",
"| 编号 | 爻值（初→上） | 占日日辰 |", "|---|---|---|"]
L += [f"| Z{k + 1:02d} | {' '.join(y)} | {d} |" for k, (y, d) in enumerate(cases)]
L += ["", "## 二、地支藏干三列次序（按《渊海子平》，通行整理次序）", "", "```csv", "地支,本气,中气,余气"] + [f"{b},,," for b in B] + ["```", "",
"## 三、八字查表（3 例）", "", "每柱填：天干十神（日柱写“日主”）｜藏干（本气、中气、余气）及各自十神｜日主在该柱地支的十二长生。", ""]
L += [f"- B{k + 1}：年 {p[0]}　月 {p[1]}　日 {p[2]}　时 {p[3]}" for k, p in enumerate(charts)]
L += ["", "```csv", "编号,柱,天干十神,藏干及十神（如 丁正财/己正官）,日主十二长生"] + [f"B{k + 1},{x},,," for k, p in enumerate(charts) for x in p] + ["```", ""]
open(os.path.join(ROOT, "crosscheck/gemini/G-2_任务书与空白表.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("答案封存 sha256：", hashlib.sha256(open(ans_path, "rb").read()).hexdigest())
print("抽样：", cases)
