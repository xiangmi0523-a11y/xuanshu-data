import re,csv,calendar,datetime as dt,collections
lines=open('alm/zjs.txt',encoding='utf-8').read().split('\n')
DP={r['date']:r['day_pillar'] for r in csv.DictReader(open('/mnt/project-files/xuanshu/b4-data/day_pillars_1900_2100.csv',encoding='utf-8'))}
gz=re.compile(r'[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]')
year=None; months=None; checked=0; bad=[]; rowsbad=[]
seen=collections.Counter()
for i,l in enumerate(lines):
    m=re.search(r'公元\s*(\d{4})\s*年',l)
    if m: year=int(m.group(1)); months=None; continue
    mm=re.findall(r'(\d{1,2})\s*月',l)
    if len(mm)==4 and '日' not in l and year:
        months=[int(x) for x in mm]; continue
    m=re.match(r'\s*(\d{1,2})\s+\S',l)
    if m and months and year and not re.search(r'[时分]',l):
        d=int(m.group(1))
        if not 1<=d<=31: continue
        toks=gz.findall(l[m.end()-1:])
        have=[mo for mo in months if d<=calendar.monthrange(year,mo)[1]]
        if len(toks)!=len(have):
            rowsbad.append((year,months,d,toks,l.strip())); continue
        for mo,t in zip(have,toks):
            k=f'{year}-{mo:02d}-{d:02d}'; checked+=1; seen[k]+=1
            if DP[k]!=t: bad.append((k,t,DP[k],i+1))
print('checked',checked,'mismatch',len(bad),'row-parse failures',len(rowsbad))
exp=sum(366 if calendar.isleap(y) else 365 for y in range(1900,2026))
print('expected days',exp,'unique covered',len(seen),'dupes',sum(1 for v in seen.values() if v>1))
for b in bad[:30]: print('MISMATCH',b)
for r in rowsbad[:30]: print('ROWFAIL',r)
