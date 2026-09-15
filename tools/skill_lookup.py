"""Deterministic read-only lookup over canonical Keyence skill_data."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'skill_data'
FILES={'command':D/'operations/command_reference.yaml','signal':D/'operations/io_signal_reference.yaml','head':D/'hardware/head_specifications.yaml','workflow':D/'workflows/operational_workflows.yaml','communication':D/'communication/communication_matrix.yaml','measurement':D/'measurement/measurement_tools.yaml','correction':D/'measurement/corrections.yaml','intent':D/'routing/measurement_routing.yaml','scenario':D/'routing/skill_scenarios.yaml'}
KEYS={'command':['command','command_id'],'signal':['signal','signal_name','signal_id'],'head':['model','head_id'],'workflow':['workflow_id','title'],'communication':['method','method_id','name'],'measurement':['tool_id','official_name'],'correction':['correction_id','official_name'],'intent':['intent'],'scenario':['question','scenario_id']}
def records(path):
 d=json.loads(path.read_text(encoding='utf8'))
 for k in ('commands','signals','records','tools','heads','workflows','routes','scenarios','methods','relationships'):
  if isinstance(d.get(k),list): return d[k]
 return []
def main():
 p=argparse.ArgumentParser();p.add_argument('kind',choices=FILES);p.add_argument('query');p.add_argument('--controller');p.add_argument('--mode');p.add_argument('--json',action='store_true');a=p.parse_args()
 found=[]
 for x in records(FILES[a.kind]):
  text=' '.join(str(x.get(k,'')) for k in KEYS[a.kind]).lower()
  if a.query.lower() in text:
   applicability=x.get('applicability',{})
   fam=applicability.get('controller_family') or applicability.get('controllers') or x.get('family') or x.get('controller_family') or x.get('controller_applicability')
   mode=applicability.get('mode') or x.get('mode')
   if a.controller and (not fam or (isinstance(fam,list) and a.controller not in fam) or (not isinstance(fam,list) and fam!=a.controller)): continue
   if a.mode and mode and mode not in (a.mode,'CONTEXT_REQUIRED','2D_OR_3D_CONTEXT_REQUIRED'): continue
   found.append({'canonical_file':str(FILES[a.kind].relative_to(R)),'record':x,'applicability':{'controller_family':fam,'mode':mode},'knowledge_status':x.get('knowledge_status'),'evidence':x.get('source_evidence') or x.get('direct_evidence') or []})
 out={'kind':a.kind,'query':a.query,'matches':found,'unresolved':not bool(found)}
 print(json.dumps(out,ensure_ascii=False,indent=2) if a.json else '\n'.join(f"{i+1}. {m['canonical_file']} :: {m['record'].get('command') or m['record'].get('model') or m['record'].get('official_name') or m['record'].get('workflow_id') or m['record'].get('intent')}" for i,m in enumerate(found)) or 'No canonical match.')
if __name__=='__main__':main()



