import csv,datetime as dt,collections
S={}
for r in csv.DictReader(open('/mnt/project-files/xuanshu/jieqi/jieqi_1900_2100_utc_skyfield.csv',encoding='utf-8')):
    S[(int(r['year']),r['term'])]=dt.datetime.fromisoformat(r['term_utc8_iso']).replace(tzinfo=None)
A=list(csv.DictReader(open('/mnt/project-files/xuanshu/almanac/zjs_terms_1900_2025_extracted.csv',encoding='utf-8')))
c=collections.Counter(); big=[]; dated=[]; trunc_ok=0; round_ok=0
for r in A:
    y=int(r['year']); t=r['term']
    a=dt.datetime(y,int(r['month']),int(r['day']),int(r['hour']),int(r['minute']))
    s=S[(y,t)]
    d=(a-s).total_seconds()   # seconds
    rnd=(s+dt.timedelta(seconds=30)).replace(second=0)
    trn=s.replace(second=0)
    if a==rnd: round_ok+=1
    if a==trn: trunc_ok+=1
    c[round((a-rnd).total_seconds()/60)]+=1
    if a!=rnd: big.append((y,t,a.strftime('%m-%d %H:%M'),s.strftime('%m-%d %H:%M:%S'),round((a-rnd).total_seconds()/60),r['footnote'],r['txt_line']))
    if a.date()!=s.date(): dated.append((y,t,a,s))
print('n',len(A),'equal to rounded Skyfield',round_ok,'equal to truncated',trunc_ok)
print('diff hist (min, vs rounded)',sorted(c.items()))
print('date differs',len(dated)); [print(x) for x in dated]
print('nonzero list',len(big))
for b in big: print(b)
