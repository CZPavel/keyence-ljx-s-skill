"""Targeted read-only text lookup for the retained raw corpus."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; S=R/'corpus/keyence_skill_v1/skill_ready'
def main():
 p=argparse.ArgumentParser();p.add_argument('--query',required=True);p.add_argument('--document');p.add_argument('--page',type=int);p.add_argument('--tables',action='store_true');p.add_argument('--limit',type=int,default=10);p.add_argument('--json',action='store_true');a=p.parse_args(); path=S/('tables.jsonl' if a.tables else 'retrieval_chunks.jsonl'); out=[]
 if not path.exists():
  p.error('Local raw corpus is unavailable. Supply legally obtained sources locally; this public repository does not redistribute manuals.')
 for line in path.open(encoding='utf8'):
  x=json.loads(line); text=json.dumps(x,ensure_ascii=False).lower()
  if a.query.lower() not in text: continue
  if a.document and a.document.lower() not in str(x.get('document_id','')).lower(): continue
  if a.page is not None and a.page not in (x.get('page'),x.get('source_unit')): continue
  out.append(x)
  if len(out)>=a.limit: break
 result={'query':a.query,'source':path.name,'matches':out}
 print(json.dumps(result,ensure_ascii=False,indent=2) if a.json else '\n'.join(f"{x.get('document_id')} {x.get('source_locator','')} {x.get('chunk_id',x.get('table_id'))}" for x in out))
if __name__=='__main__':main()


