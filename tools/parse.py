"""Pair the eight original question sections with annotated answers and printed quick keys."""
import pathlib,json,re,collections,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE='https://aokid666.github.io/zz-tuijie-exams-2027/';ID='tuijie8'
def dump(name,data):
 text=json.dumps(data,ensure_ascii=False,separators=(',',':'));(ROOT/'data'/name).write_text(text);(ROOT/'_site/data'/name).write_text(text)
def norm(t):return re.sub(r'\s+','',t)
def useful(l,p):
 t=l['t'].strip();return 20<l['b'][1]<p['height']-20 and not re.search(r'后续更新|夸克网盘|835784031|考研政治冲刺专项.*[册卷]|第[一二三四五六七八]套卷|参考答案速查|[一二三]、?[单双多]项选择|单项选择题|多项选择题',t)
def head(l,p):
 if l['b'][0]>p['width']*.26:return None
 m=re.match(r'^(\d{1,2})\s*[.．、。，,:：]\s*(.*)',l['t'])
 return (int(m[1]),m[2]) if m and 1<=int(m[1])<=38 else None
QSTART=[5,13,20,28,35,42,50,57];ASTART=[8,22,34,48,60,72,86,100]
subjects=['马克思主义基本原理','毛泽东思想和中国特色社会主义理论体系概论','习近平新时代中国特色社会主义思想概论','中国近现代史纲要','思想道德与法治']
def groups(pages,starts,answer=False):
 out=[]
 for s,start in enumerate(starts):
  end=starts[s+1] if s+1<len(starts) else len(pages);found={};cur=None;expected=1;quick={}
  for p in pages[start-1:end-1]:
   rows=[{**l,'p':p['page']} for l in p['lines'] if useful(l,p)]
   for l in rows:
    h=head(l,p)
    # The quick-answer rows have number+answer tokens, no question stem.
    entries=list(re.finditer(r'(\d{1,2})\s*[.．、。，,:：]\s*([ABCDabcd]{1,4})(?![A-Za-z])',l['t']))
    if answer and cur is None and entries:
     for m in entries:
      if 1<=int(m[1])<=33:quick[int(m[1])]=''.join(sorted(set(m[2].upper())))
     continue
    if h and h[0]==expected and len(h[1])>=3:
     if cur:found[cur[0]]=cur[1]
     cur=(h[0],[{**l,'rest':h[1]}]);expected+=1
    elif cur:cur[1].append(l)
  if cur:found[cur[0]]=cur[1]
  out.append((found,quick))
 return out

def refs(rows,pages,offset=0):
 out=[]
 for pn in dict.fromkeys(l['p'] for l in rows):
  ls=[l for l in rows if l['p']==pn];p=pages[pn-1];x=max(0,min(l['b'][0] for l in ls)-4);y=max(0,min(l['b'][1] for l in ls)-4);right=min(p['width'],max(l['b'][2] for l in ls)+4);bottom=min(p['height'],max(l['b'][3] for l in ls)+4);out.append({'page':pn+offset,'b':[x,y,right-x,bottom-y]})
 return out

def options(rows):
 stem=[rows[0]['rest']];opts={};anchors=[];unlabelled=[]
 for l in rows[1:]:
  t=l['t'];ms=list(re.finditer(r'(?<![A-Za-z])([ABCDabcd])[.．、。:：]\s*',t))
  if not ms:
   m=re.match(r'^([ABCDabcd])\s*(?=[\u4e00-\u9fff“《])',t)
   if m:ms=[m]
  if ms:
   before=t[:ms[0].start()].strip()
   if before:unlabelled.append({**l,'t':before})
   for i,m in enumerate(ms):
    k=m[1].upper();v=t[m.end():ms[i+1].start() if i+1<len(ms) else len(t)].strip()
    if k in opts:opts[k]+='〔重复选项标记〕'
    else:opts[k]=''
    opts[k]+=v;anchors.append((l['p'],l['b'][0]+(l['b'][2]-l['b'][0])*m.start()/max(1,len(t)),l['b'][1],k))
  else:unlabelled.append(l)
 for l in unlabelled:
  choices=[a for a in anchors if a[0]<=l['p'] and (a[0]<l['p'] or a[2]<=l['b'][1]+2)]
  if not choices:stem.append(l['t']);continue
  cols=sorted({round(a[1]/35)*35 for a in choices if a[0]==l['p']});same=[a for a in choices if a[0]==l['p'] and abs(a[1]-l['b'][0])<70]
  target=max(same or choices,key=lambda a:(a[0],a[2]));opts[target[3]]+=l['t']
 return '\n'.join(stem),opts

def answer(rows,quick,no):
 found=[]
 for i,l in enumerate(rows):
  t=norm(l['t']).replace('【','').replace('】','').replace('[','').replace(']','')
  if re.match(r'^(?:正确)?答案',t):
   m=re.match(r'^(?:正确)?答案[:：]?([ABCDabcd]{1,4})$',t)
   if m:found.append(m[1].upper())
   else:
    for r in rows[i+1:i+4]:
     if re.fullmatch('[ABCDabcd]{1,4}',norm(r['t'])):found.append(norm(r['t']).upper());break
 if found:return ''.join(sorted(set(found[0]))),found
 return quick.get(no,''),found

def main():
 qd=json.loads((ROOT/'data/tuijie8-question.json').read_text());ad=json.loads((ROOT/'data/tuijie8-answer.json').read_text());qp,ap=qd['pages'],ad['pages'];qgs=groups(qp,QSTART);ags=groups(ap,ASTART,True);qs=[];errors=[];comparison=[]
 for si,((qg,_),(ag,quick)) in enumerate(zip(qgs,ags),1):
  print(si,'question',list(qg),'analysis',list(ag),'quick',quick,flush=True)
  if set(qg)!=set(range(1,34)):errors.append(f'set {si}: question numbers {list(qg)}')
  if set(ag)!=set(range(1,34)):errors.append(f'set {si}: explanation numbers {list(ag)}')
  for n in sorted(set(qg)&set(ag)):
   stem,opts=options(qg[n]);key,found=answer(ag[n],quick,n)
   if set(opts)!=set('ABCD') or any(not v or '〔重复' in v for v in opts.values()):errors.append(f'{si}-{n}: malformed options {opts}')
   if not key or (n<=16 and len(key)!=1) or (17<=n<=33 and len(key)<2):errors.append(f'{si}-{n}: invalid key {key}')
   if n in quick and found:
    comparison.append([si,n,key,quick[n]])
    if key!=quick[n]:errors.append(f'{si}-{n}: quick key disagrees {key}/{quick[n]}')
   subject=subjects[si-1] if si<=5 else subjects[0 if n<=4 or 17<=n<=21 else 1 if n<=6 or n==22 else 2 if n<=10 or 23<=n<=26 else 3 if n<=14 or 27<=n<=29 else 4] if n<=31 else '时事政治'
   text='\n'.join([ag[n][0]['rest']]+[l['t'] for l in ag[n][1:]])
   qs.append({'id':f'pr-{ID}-choice-{si}-{n:02}','bookId':ID,'type':'choice','source':'p','moduleIdx':12,'module':subject,'chapter':f'第{si}套','chapterTitle':f'第{si}套','section':'单项选择题' if n<=16 else '多项选择题','no':n,'originalNo':n,'examSet':si,'stem':stem,'options':opts,'multi':n>=17,'answer':key,'qRefs':refs(qg[n],qp),'keyRefs':refs(ag[n],ap,len(qp)),'analysis':[{'k':'原书批注与解析','t':text}],'kPages':[],'sPages':[],'mRefs':[],'aPages':[],'aCrops':[],'extractionNote':'扫描原文识别，保留原始题面与批注；个别疑难字请对照原图。'})
 report={'questions':len(qs),'sets':[len(g[0]) for g in qgs],'answerSets':[len(g[0]) for g in ags],'quickKeyCounts':[len(g[1]) for g in ags],'compared':len(comparison),'errors':errors};dump('parse-report.json',report);dump('draft-questions.json',qs)
 if errors:print(json.dumps(report,ensure_ascii=False),flush=True);raise RuntimeError('Unresolved source mismatch; website import blocked')
 pages=qp+ap;pageurls=[BASE+f'img/{id}/{p["page"]:03}.{p["ext"]}' for id,ps in [('tuijie8-question',qp),('tuijie8-answer',ap)] for p in ps];pdfs=[{'firstPage':1,'lastPage':len(qp),'url':BASE+'pdf/tuijie8-question.pdf'},{'firstPage':len(qp)+1,'lastPage':len(pages),'url':BASE+'pdf/tuijie8-answer.pdf'}]
 book={'id':ID,'title':'腿姐八套卷','kind':'mock','count':len(qs),'counts':dict(collections.Counter(q['type'] for q in qs)),'pages':len(pages),'pageSizes':[{'width':p['width'],'height':p['height']} for p in pages],'pageUrls':pageurls,'sourceBase':BASE,'url':pdfs[0]['url'],'pdfParts':pdfs,'sha256':hashlib.sha256(''.join(s['source']['sha256'] for s in [qd,ad]).encode()).hexdigest(),'chapters':[{'key':q['module']+' · '+q['chapter'],'title':q['module']+' · '+q['chapter'],'firstPage':q['qRefs'][0]['page'],'count':sum(x['module']==q['module'] and x['chapter']==q['chapter'] for x in qs)} for i,q in enumerate(qs) if not any(x['module']==q['module'] and x['chapter']==q['chapter'] for x in qs[:i])],'readSections':[{'title':'解析册 · 第'+str(i+1)+'套','firstPage':n+len(qp)} for i,n in enumerate(ASTART)]}
 dump('book.json',book);dump(ID+'.json',{'bookId':ID,'questions':qs,'pages':[{'page':i+1,'width':p['width'],'height':p['height'],'text':p['text']} for i,p in enumerate(pages)]})
if __name__=='__main__':
 import hashlib
 try:main()
 except Exception:
  import traceback
  (ROOT/'data/parser-error.txt').write_text(traceback.format_exc())
  raise
