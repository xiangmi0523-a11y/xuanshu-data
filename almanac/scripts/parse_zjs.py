import re,csv,sys,collections
T="小寒 大寒 立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至".split()
txt=open(sys.argv[1],encoding='utf-8').read()
lines=txt.split('\n')
year=None; out=[]; odd=[]
pat=re.compile('('+'|'.join(T)+r')(\d\))?\s*(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})')
for i,l in enumerate(lines):
    m=re.search(r'公元\s*(\d{4})\s*年',l)
    if m: year=int(m.group(1)); continue
    for mm in pat.finditer(l):
        out.append((year,mm.group(1),int(mm.group(3)),int(mm.group(4)),int(mm.group(5)),int(mm.group(6)),'Y' if mm.group(2) else '',i+1))
    # lines with a term name but not matched
    names=[t for t in T if t in l]
    if names and len(pat.findall(l))<len(names) and year: odd.append((year,i+1,l.strip()))
c=collections.Counter(y for y,*_ in out)
bad=[y for y in range(1900,2026) if c[y]!=24]
print('parsed',len(out),'years with !=24:',[(y,c[y]) for y in bad])
print('odd lines',len(odd))
for o in odd[:40]: print(o)
w=csv.writer(open(sys.argv[2],'w',encoding='utf-8',newline=''))
w.writerow(['year','term','month','day','hour','minute','footnote','txt_line'])
w.writerows(out)
