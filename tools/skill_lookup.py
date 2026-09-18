"""Deterministic read-only lookup over canonical Keyence skill_data."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'skill_data'
FILES={'command':D/'operations/command_reference.yaml','signal':D/'operations/io_signal_reference.yaml','operation':D/'operations/ljs8000_contextual_ui_io_save.yaml','head':D/'hardware/head_specifications.yaml','workflow':D/'workflows/operational_workflows.yaml','communication':D/'communication/communication_matrix.yaml','dataflow':D/'communication/data_flow_reference.yaml','measurement':D/'measurement/measurement_tools.yaml','correction':D/'measurement/corrections.yaml','acquisition':D/'measurement/acquisition.yaml','preprocessing':D/'measurement/preprocessing.yaml','guidance':D/'measurement/contextual_3d_guidance.yaml','diagnostic':D/'diagnostics/measurement_troubleshooting_playbooks.yaml','intent':D/'routing/measurement_routing.yaml','scenario':D/'routing/skill_scenarios.yaml'}
KEYS={'command':['command','command_id'],'signal':['signal','signal_name','signal_id'],'operation':['operation_id','official_name','aliases'],'head':['model','head_id'],'workflow':['workflow_id','title'],'communication':['method','method_id','name'],'dataflow':['flow_id','purpose','aliases'],'measurement':['tool_id','official_name','aliases'],'correction':['correction_id','official_name','aliases'],'acquisition':['setting_id','setting','aliases'],'preprocessing':['setting_id','official_name','aliases'],'guidance':['guidance_id','official_name','aliases'],'diagnostic':['playbook_id','title','symptoms'],'intent':['intent'],'scenario':['question','scenario_id']}
def records(path):
 d=json.loads(path.read_text(encoding='utf8'))
 for k in ('commands','signals','records','tools','heads','workflows','routes','scenarios','methods','relationships','playbooks','settings','flows'):
  if isinstance(d.get(k),list): return d[k]
 return []
def searchable_text(value):
 skip={'source_evidence','direct_evidence','supporting_evidence','evidence','source_sha256','evidence_excerpt_hash','chunk_id','section_id','document_id','block_id','table_id','page'}
 if isinstance(value,dict): return ' '.join(searchable_text(v) for k,v in value.items() if k not in skip)
 if isinstance(value,list): return ' '.join(searchable_text(v) for v in value)
 return str(value)
def main():
 p=argparse.ArgumentParser();p.add_argument('kind',choices=FILES);p.add_argument('query');p.add_argument('--controller');p.add_argument('--mode');p.add_argument('--json',action='store_true');a=p.parse_args()
 found=[]
 for x in records(FILES[a.kind]):
  text=searchable_text(x).lower()
  if a.query.lower() in text:
   applicability=x.get('applicability',{})
   fam=applicability.get('controller_family') or applicability.get('controllers') or x.get('family') or x.get('controller_family') or x.get('controller_applicability')
   mode=applicability.get('mode') or x.get('mode')
   if a.controller and fam and ((isinstance(fam,list) and a.controller not in fam) or (not isinstance(fam,list) and fam!=a.controller)): continue
   if a.controller and not fam and x.get('contextual_scope')!='FAMILY_NOT_ESTABLISHED': continue
   if a.mode and mode and mode not in (a.mode,'CONTEXT_REQUIRED','2D_OR_3D_CONTEXT_REQUIRED'): continue
   found.append({'canonical_file':str(FILES[a.kind].relative_to(R)),'record':x,'applicability':{'controller_family':fam,'mode':mode},'knowledge_status':x.get('knowledge_status'),'evidence':x.get('source_evidence') or x.get('direct_evidence') or []})
 out={'kind':a.kind,'query':a.query,'matches':found,'unresolved':not bool(found)}
 print(json.dumps(out,ensure_ascii=False,indent=2) if a.json else '\n'.join(f"{i+1}. {m['canonical_file']} :: {m['record'].get('command') or m['record'].get('model') or m['record'].get('official_name') or m['record'].get('workflow_id') or m['record'].get('intent')}" for i,m in enumerate(found)) or 'No canonical match.')
if __name__=='__main__':main()



