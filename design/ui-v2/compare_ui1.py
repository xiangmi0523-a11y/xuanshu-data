#!/usr/bin/env python3
"""UI-2 与 UI-1 设计源文件逐字比对。只读。用法：python3 design/ui-v2/compare_ui1.py [输出 md]"""
import difflib, hashlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A, B = os.path.join(ROOT, "design/ui-v1/source"), os.path.join(ROOT, "design/ui-v2/source")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
names = sorted(set(os.listdir(A)) | set(os.listdir(B)))
rows, diffs = [], []
for n in names:
    a, b = os.path.join(A, n), os.path.join(B, n)
    if not os.path.exists(a): rows.append((n, "—", sha(b)[:16], "UI-2 新增")); continue
    if not os.path.exists(b): rows.append((n, sha(a)[:16], "—", "UI-2 删除")); continue
    same = sha(a) == sha(b)
    rows.append((n, sha(a)[:16], sha(b)[:16], "逐字相同" if same else "有改动"))
    if not same:
        d = difflib.unified_diff(open(a, encoding="utf-8").read().splitlines(), open(b, encoding="utf-8").read().splitlines(),
                                 f"ui-v1/source/{n}", f"ui-v2/source/{n}", n=0, lineterm="")
        diffs.append((n, "\n".join(d)))
out = ["# UI-2 与 UI-1 设计源文件逐字比对", "",
       "由 `design/ui-v2/compare_ui1.py` 生成（只读）。UI-1 源文件为定稿 PDF 的渲染来源（design/ui-v1/source）。", "",
       "| 文件 | UI-1 sha256 前 16 位 | UI-2 sha256 前 16 位 | 结果 |", "|---|---|---|---|"]
out += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |" for r in rows]
c = {k: sum(1 for r in rows if r[3] == k) for k in ("逐字相同", "有改动", "UI-2 新增", "UI-2 删除")}
out += ["", f"合计：逐字相同 {c['逐字相同']}，有改动 {c['有改动']}，UI-2 新增 {c['UI-2 新增']}，UI-2 删除 {c['UI-2 删除']}。", "",
        "## 有改动文件的逐行差异（unified diff，无上下文行）", ""]
for n, d in diffs: out += [f"### {n}", "", "```diff", d, "```", ""]
text = "\n".join(out) + "\n"
if len(sys.argv) > 1: open(sys.argv[1], "w", encoding="utf-8").write(text)
else: sys.stdout.write(text)
