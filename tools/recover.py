"""Second OCR pass at independent scale to recover scan lines missed by the first detector."""
import os
os.environ['OMP_NUM_THREADS']='1'
import pathlib,json,concurrent.futures,re
import fitz
ROOT=pathlib.Path(__file__).resolve().parents[1];engine=None
sources=json.loads((ROOT/'tools/sources.json').read_text())
def init():
 global engine
 from rapidocr_onnxruntime import RapidOCR
 engine=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,text_score=.35,det_box_thresh=.3,det_thresh=.2)
def norm(t):return re.sub(r'\s+','',t)
def work(job):
 id,pn=job;cache=ROOT/'data/ocr'/f'{id}-{pn:03}.json';p=json.loads(cache.read_text())
 if p.get('recovered'):return id,p
 import numpy as np
 doc=fitz.open(ROOT/'input'/f'{id}.pdf');page=doc[pn-1];pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False);a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3);result,_=engine(a);lines=p['lines'];added=0
 for box,text,score in result or []:
  b=[min(x[0] for x in box)/2,min(x[1] for x in box)/2,max(x[0] for x in box)/2,max(x[1] for x in box)/2];cy=(b[1]+b[3])/2
  near=[(i,l) for i,l in enumerate(lines) if abs((l['b'][1]+l['b'][3])/2-cy)<min(b[3]-b[1],l['b'][3]-l['b'][1])*.6 and max(0,min(b[2],l['b'][2])-max(b[0],l['b'][0]))>min(b[2]-b[0],l['b'][2]-l['b'][0])*.6]
  candidate={'t':text,'b':b,'confidence':round(float(score),4),'secondPass':True}
  if not near:lines.append(candidate);added+=1
  else:
   i,l=max(near,key=lambda t:len(t[1]['t']))
   if (re.match(r'^\d{1,2}[.．、。，,:：]',text) and not re.match(r'^\d{1,2}[.．、。，,:：]',l['t'])) or (len(norm(text))>len(norm(l['t']))*1.35 and score>.65):lines[i]=candidate
 lines.sort(key=lambda l:(round(l['b'][1]/4),l['b'][0]));p.update(lines=lines,text='\n'.join(l['t'] for l in lines),recovered=True);cache.write_text(json.dumps(p,ensure_ascii=False,separators=(',',':')));print(id,pn,'recovered rows',added,flush=True);return id,p
if __name__=='__main__':
 (ROOT/'input').mkdir(exist_ok=True);jobs=[]
 for s in sources:
  dst=ROOT/'input'/f'{s["id"]}.pdf'
  if not dst.exists():
   with dst.open('wb') as f:
    for part in s['parts']:f.write((ROOT/part).read_bytes())
  jobs.extend((s['id'],n) for n in range(1,len(fitz.open(dst))+1))
 records={s['id']:[] for s in sources}
 with concurrent.futures.ProcessPoolExecutor(max_workers=4,initializer=init) as ex:
  for id,p in ex.map(work,jobs):records[id].append(p)
 for s in sources:(ROOT/'data'/f'{s["id"]}.json').write_text(json.dumps({'source':s,'pages':sorted(records[s['id']],key=lambda p:p['page'])},ensure_ascii=False,separators=(',',':')))
