# UI-2 与 UI-1 设计源文件逐字比对

由 `design/ui-v2/compare_ui1.py` 生成（只读）。UI-1 源文件为定稿 PDF 的渲染来源（design/ui-v1/source）。

| 文件 | UI-1 sha256 前 16 位 | UI-2 sha256 前 16 位 | 结果 |
|---|---|---|---|
| About.dc.html | 756db44995156dc5 | 756db44995156dc5 | 逐字相同 |
| BaziInput.dc.html | 88678ea0e9de1235 | 88678ea0e9de1235 | 逐字相同 |
| BaziInputShichen.dc.html | 10ac3b049f567813 | 9bf4145b4288f932 | 有改动 |
| BaziInputUnknown.dc.html | 87afcc93cc2d943d | 87afcc93cc2d943d | 逐字相同 |
| DeleteProfile.dc.html | b2cc3475dadd3a0d | b2cc3475dadd3a0d | 逐字相同 |
| GujiSearch.dc.html | 7670adb4302ee6dd | 7670adb4302ee6dd | 逐字相同 |
| GujiText.dc.html | 19e9056a63c29242 | 19e9056a63c29242 | 逐字相同 |
| History.dc.html | 2b74e210db4b73c8 | 2b74e210db4b73c8 | 逐字相同 |
| Liuyao.dc.html | fa134db13b947092 | 771991a0b174d4e7 | 有改动 |
| LiuyaoSource.dc.html | — | 0c99e17bed08ec0b | UI-2 新增 |
| Main.dc.html | f46c9023f0064374 | 69bd1ee1d8211b0c | 有改动 |
| ResultAmbiguous.dc.html | 4cfa8d93a3937d3b | 4cfa8d93a3937d3b | 逐字相同 |
| ResultBlocked.dc.html | c6846743880b3178 | c6846743880b3178 | 逐字相同 |
| ResultDegraded.dc.html | 64dd6361637767d4 | 64dd6361637767d4 | 逐字相同 |
| ResultNormal.dc.html | 2c7994775a174e2a | 02eb992c2d68cfae | 有改动 |
| Settings.dc.html | fdc9e16e4287d79a | fdc9e16e4287d79a | 逐字相同 |
| States.dc.html | 46ec506a9c630370 | 46ec506a9c630370 | 逐字相同 |
| canvas.json | d5ca94c085f0b81e | 3c6b3c08ac0e254a | 有改动 |

合计：逐字相同 12，有改动 5，UI-2 新增 1，UI-2 删除 0。

## 有改动文件的逐行差异（unified diff，无上下文行）

### BaziInputShichen.dc.html

```diff
--- ui-v1/source/BaziInputShichen.dc.html
+++ ui-v2/source/BaziInputShichen.dc.html
@@ -18 +18 @@
-<div style="width: 390px; height: 1270px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
+<div style="width: 390px; height: 1385px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
@@ -82,0 +83 @@
+      <span style="font-size: 12px; line-height: 1.6; color: #6E2218; background: #F5E1DB; border-radius: 10px; padding: 8px 10px">只知时辰时，如出生地时区与北京时间（UTC+8）相差的不是 2 小时的整数倍（例如 1986–1991 年夏令时期间为 UTC+9），所选时辰换到北京时间后会横跨两个时辰，时柱无法唯一确定，排盘会被阻断。请改选“精确到分钟”，填写出生证明上的时间。</span>
@@ -101 +102 @@
-<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1270}}'>
+<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1385}}'>
```

### Liuyao.dc.html

```diff
--- ui-v1/source/Liuyao.dc.html
+++ ui-v2/source/Liuyao.dc.html
@@ -17 +17 @@
-<div style="width: 390px; height: 1160px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
+<div style="width: 390px; height: 1678px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
@@ -71,6 +71,20 @@
-    <section style="display: flex; gap: 12px; align-items: flex-start; padding: 16px; border: 1.5px dashed #C9BBA6; border-radius: 18px">
-      <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4F5966" stroke-width="2" style="flex-shrink: 0; margin-top: 1px"><rect x="5" y="11" width="14" height="9" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg>
-      <span style="display: flex; flex-direction: column; gap: 4px">
-        <span style="font-size: 15px; font-weight: 700">装卦 · 暂不显示</span>
-        <span style="font-size: 13px; line-height: 1.65; color: #3F4955">八宫、纳甲、世应、六亲、六神的静态表正在核查。核实并经你确认后，逐项开放。</span>
-      </span>
+    <section aria-label="装卦" style="background: #FBF8F2; border: 1px solid #E4DACB; border-radius: 20px; padding: 16px; display: flex; flex-direction: column; gap: 8px">
+      <div style="display: flex; align-items: baseline; justify-content: space-between; gap: 8px">
+        <span style="font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 17px; letter-spacing: 1px">装卦 · 乾宫 本宫</span>
+        <span style="font-size: 12px; color: #4F5966">宫五行 金 · 以金为我</span>
+      </div>
+      <span style="align-self: flex-start; font-size: 11px; font-weight: 700; color: #3F4955; border: 1px solid #8C99A8; border-radius: 6px; padding: 0 6px">京房纳甲体系 · 后世术数，非《周易》原文</span>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; font-size: 11px; color: #5E6874; padding-top: 4px"><span>爻</span><span>六神</span><span>六亲</span><span>纳甲 · 五行</span><span>爻象</span><span>世应</span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">上</span><span style="font-size: 12px; color: #5E6874">朱雀</span><span style="font-size: 13px; font-weight: 700">父母</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">壬戌土</span><span></span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 10px; background: #2F4A68; color: #FBF8F2; font-size: 11px; font-weight: 700">世</span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">五</span><span style="font-size: 12px; color: #5E6874">青龙</span><span style="font-size: 13px; font-weight: 700">兄弟</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">壬申金</span><span></span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span></span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">四</span><span style="font-size: 12px; color: #5E6874">玄武</span><span style="font-size: 13px; font-weight: 700">官鬼</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">壬午火</span><span></span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span></span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">三</span><span style="font-size: 12px; color: #5E6874">白虎</span><span style="font-size: 13px; font-weight: 700">父母</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">甲辰土</span><span></span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 10px; background: #2F4A68; color: #FBF8F2; font-size: 11px; font-weight: 700">应</span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">二</span><span style="font-size: 12px; color: #5E6874">螣蛇</span><span style="font-size: 13px; font-weight: 700">妻财</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">甲寅木</span><span></span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span></span><span></span></div>
+      <div style="display: grid; grid-template-columns: 18px 34px 34px minmax(0, 1fr) 36px 20px 12px; gap: 6px; align-items: center; min-height: 30px; border-top: 1px solid #EFE7DA"><span style="font-size: 11px; color: #4F5966">初</span><span style="font-size: 12px; color: #5E6874">勾陈</span><span style="font-size: 13px; font-weight: 700">子孙</span><span style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14px; font-family: 'Noto Serif SC', serif; font-weight: 700; letter-spacing: 1px">甲子水</span><span style="font-size: 12px; color: #9A3B2A; white-space: nowrap">→ 父母 辛丑土</span></span><span style="display: block; height: 8px; border-radius: 2px; background: #1E2833"></span><span></span><span aria-label="动爻" style="width: 12px; height: 12px; border-radius: 6px; border: 2px solid #9A3B2A; box-sizing: border-box"></span></div>
+      <div style="display: flex; flex-direction: column; gap: 4px; padding: 10px 12px; margin-top: 4px; border-radius: 12px; background: #F3EEE6">
+        <span style="font-size: 12px; line-height: 1.6; color: #3F4955">变卦天风姤（乾宫一世）只列变爻的纳甲与六亲；六亲仍以本卦乾宫金论。</span>
+        <span style="font-size: 12px; line-height: 1.6; color: #3F4955">变卦不排六神：古籍卦例一致，四书无明文，属由例推定。</span>
+        <span style="font-size: 12px; line-height: 1.6; color: #3F4955">变卦不标世应：经古吴版扫描本卦例复核，已证实；四书无明文，规则由卦例归纳。</span>
+      </div>
+      <span style="font-size: 12px; line-height: 1.6; color: #5E6874">六神仅作辅助符号，不参与生克。旬空 辰巳（戊戌日，甲午旬）。断语与旺衰不在此显示。</span>
+      <a href="LiuyaoSource.dc.html" style="align-self: flex-start; display: inline-flex; align-items: center; gap: 4px; min-height: 44px; font-size: 13px">出处与证据<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2F4A68" stroke-width="2" stroke-linecap="round"><path d="M9 5l7 7-7 7"></path></svg></a>
@@ -86 +100 @@
-        <span style="font-size: 12px; line-height: 1.6; color: #3F4955">纳甲、六亲、世应，非《周易》原文；六神仅作辅助符号</span>
+        <span style="font-size: 12px; line-height: 1.6; color: #3F4955">八宫、纳甲、世应、六亲、六神、旬空：京房纳甲体系，非《周易》原文</span>
@@ -105 +119 @@
-<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1160}}'>
+<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1678}}'>
```

### Main.dc.html

```diff
--- ui-v1/source/Main.dc.html
+++ ui-v2/source/Main.dc.html
@@ -67 +67 @@
-      <span style="display: flex; flex-direction: column; gap: 2px"><span style="font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 16px">六爻装卦</span><span style="font-size: 12px; color: #5E6874">起卦 · 卦象</span></span>
+      <span style="display: flex; flex-direction: column; gap: 2px"><span style="font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 16px">六爻装卦</span><span style="font-size: 12px; color: #5E6874">起卦 · 装卦</span></span>
```

### ResultNormal.dc.html

```diff
--- ui-v1/source/ResultNormal.dc.html
+++ ui-v2/source/ResultNormal.dc.html
@@ -17 +17 @@
-<div style="width: 390px; height: 1560px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
+<div style="width: 390px; height: 1789px; background: #F3EEE6; font-family: 'Noto Sans SC', sans-serif; color: #1E2833; display: flex; flex-direction: column; overflow: hidden">
@@ -53,0 +54 @@
+        <span style="margin-top: auto; font-size: 11px; color: #5E6874; border-top: 1px dashed #E4DACB; padding-top: 6px; align-self: stretch">胎</span>
@@ -60,0 +62 @@
+        <span style="margin-top: auto; font-size: 11px; color: #5E6874; border-top: 1px dashed #E4DACB; padding-top: 6px; align-self: stretch">长生</span>
@@ -67,0 +70 @@
+        <span style="margin-top: auto; font-size: 11px; color: #5E6874; border-top: 1px dashed #E4DACB; padding-top: 6px; align-self: stretch">帝旺</span>
@@ -74,0 +78 @@
+        <span style="margin-top: auto; font-size: 11px; color: #5E6874; border-top: 1px dashed #E4DACB; padding-top: 6px; align-self: stretch">养</span>
@@ -75,0 +80 @@
+          <p style="grid-column: 1 / -1; margin: 12px 6px 0; text-align: left; font-size: 11px; line-height: 1.7; color: #5E6874">藏干按本气、中气、余气列出，次序为<strong style="color: #3F4955">现代整理</strong>，《渊海子平》歌诀只给所藏之干。末行为日主壬在各支的十二长生，属术数传承层，旺衰不等于吉凶。</p>
@@ -81,0 +87 @@
+        <span style="color: #3F4955">时区依据</span><span>1990 年中国夏令时</span>
@@ -87,0 +94 @@
+      <p style="margin: 0; padding: 10px 12px; border-radius: 12px; background: #F3EEE6; font-size: 12px; line-height: 1.7; color: #3F4955">原始出生时间按照出生地当地民用时间记录，系统依据出生日期和出生地点对应的时区规则换算为北京时间（UTC+8），并统一按照北京时间进行排盘。原始出生时间予以保留。</p>
@@ -144 +151 @@
-<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1560}}'>
+<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":390,"height":1789}}'>
```

### canvas.json

```diff
--- ui-v1/source/canvas.json
+++ ui-v2/source/canvas.json
@@ -21 +21 @@
-  "title": "玄枢 · 方案一 东方雅致 · 关键页面",
+  "title": "玄枢 · 方案一 东方雅致 · UI-2",
@@ -59 +59 @@
-      "h": 1560,
+      "h": 1789,
@@ -89,3 +89,3 @@
-      "y": 3700,
-      "w": 390,
-      "h": 1160,
+      "y": 3900,
+      "w": 390,
+      "h": 1678,
@@ -97 +97 @@
-      "y": 3700,
+      "y": 3900,
@@ -105 +105 @@
-      "y": 3700,
+      "y": 3900,
@@ -113 +113 @@
-      "y": 3700,
+      "y": 3900,
@@ -121 +121 @@
-      "y": 3700,
+      "y": 3900,
@@ -129 +129 @@
-      "y": 5540,
+      "y": 6140,
@@ -139 +139 @@
-      "h": 1270,
+      "h": 1385,
@@ -148,0 +149,8 @@
+      "radius": 44
+    },
+    "LiuyaoSource.dc.html": {
+      "x": 2350,
+      "y": 3900,
+      "w": 390,
+      "h": 1378,
+      "title": "08b 六爻 · 出处与证据",
@@ -163,0 +172 @@
+    "LiuyaoSource.dc.html",
@@ -189 +198 @@
-      "y": 3440,
+      "y": 3640,
@@ -197 +206 @@
-      "y": 5280,
+      "y": 5880,
@@ -209 +218 @@
-      "text": "设计说明（方案一 · 东方雅致 · 修订 1）\n\n· 命例四柱、真太阳时、交节时刻由引擎 E1 用冻结表实算；十神、藏干、神煞按通行表。\n· 大运、装卦（纳甲、世应、六亲、六神）在规则验收和静态表核实前不显示。\n· 版本名、底本名一律不虚构；未核实前显示“待核实”。\n· 正式 / 非正式是每条结果的状态；首页只放“研究模式”提示条，“正式”只在标明“状态示例”的区域出现。"
+      "text": "设计说明（方案一 · 东方雅致 · UI-2）\n\n· 在 UI-1 定稿基础上只改与新裁决相关的页面，视觉方向不变。\n· 装卦开放（M1-R、M2-R 准入，E2-A 第 1 项已验收）：08 页显示八宫、世应、纳甲、六亲、六神、旬空；数值由引擎实算。\n· 变卦不显示六神与世应（M3-R、R-39.12）；08b 出处详情写依据与特殊标注（H13、H19、H31）。\n· 03 页补“统一按北京时间排盘”说明（PD-1）、日主十二长生，藏干标“现代整理”。\n· 02b 补“时区差不是 2 小时整数倍时阻断”提示（E1-1）。"
@@ -217 +226 @@
-      "text": "三处冲突：按 ChatGPT 建议执行，待用户确认\n\n1. 原“取用义项”改为“分析义项”。\n2. 人元司令、《滴天髓》版本：等 Muse 核查，界面只留“版本待核实”空状态。\n3. 首页不放全局“正式”；历史页的正式记录移入“状态示例”区。"
+      "text": "UI-2 依据\n\n1. M3-R：变卦不排六神、不标世应；藏干次序为现代整理。\n2. R-39.12：变卦不标世应证据升为已证实。\n3. E2-A1-C：H13 写“原文作‘六位居世’（两刊本同）；世五应二依安世应诀推定”；H19、H31 写应爻证据尚待补强。\n4. PD-1：结果页统一按北京时间排盘说明。\n5. E1-1：只知时辰跨两个时辰即阻断。\n\n未改：人元司令、《滴天髓》仍未选版本、不显示；大运仍暂不显示。"
```

