"""Evidence-first deltas relative to the LJ-X8000 operational baseline."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'skill_data';C=R/'corpus/keyence_skill_v1/skill_ready/retrieval_chunks.jsonl'
LS='KEYENCE-837C7E2323DA'; XA='KEYENCE-17574BD15720'
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
 rows=[json.loads(x) for x in C.open(encoding='utf8')]
 def e(doc,needle):
  x=next(x for x in rows if x['source_reference']['document_id']==doc and needle.lower() in x['text'].lower());return {'evidence_quality':'DIRECT','document_id':doc,'source_sha256':x['source_sha256'],'page':x['source_unit'],'section_id':x['section_id'],'chunk_id':x['chunk_id'],'evidence_excerpt_hash':x['text_sha256']}
 ls_t1=e(LS,'When the T1 command');ls_port=e(LS,'default port number');ls_pfr=e(LS,'profile data faster');xa_ext=e(XA,'External trigger');xa_cont=e(XA,'Continuous trigger');xa_enc=e(XA,'Encoder trigger');xa_pass=e(XA,'TRG_PASS')
 cmds=json.loads((O/'operations/command_reference.yaml').read_text(encoding='utf8'))['commands']; signals=json.loads((O/'operations/io_signal_reference.yaml').read_text(encoding='utf8'))['signals']; workflows=json.loads((O/'workflows/operational_workflows.yaml').read_text(encoding='utf8'))['workflows']
 def comp(rel='NOT_VERIFIED',ev=None,diff=None,ref=None):return {'relation':rel,'canonical_ref':ref,'differences':diff or [],'evidence':[ev] if ev else []}
 cd=[]
 for x in cmds:
  c=x['command']; ls=comp();xa=comp()
  if c=='T1':ls=comp('SAME',ls_t1,ref='command:T1')
  if c in {'PFR','PFRF'}:ls=comp('SAME',ls_pfr,ref='command:'+c)
  cd.append({'record_id':'command:'+c,'baseline_family':'LJ-X8000','comparison':{'LJ-S8000':ls,'LJ-X8000A':xa}})
 sd=[]
 for x in signals:
  n=x['signal_name'];ls=comp();xa=comp()
  sd.append({'record_id':'signal:'+n,'baseline_family':'LJ-X8000','comparison':{'LJ-S8000':ls,'LJ-X8000A':xa}})
 sd.append({'record_id':'signal:TRG_PASS','baseline_family':'LJ-X8000','comparison':{'LJ-S8000':comp(),'LJ-X8000A':comp('FAMILY_SPECIFIC',xa_pass,['Trigger-pass output is documented for LJ-X8000A.'],'signal:TRG_PASS')}})
 trigger=[]
 for method in ['external','software','continuous','encoder','multiple']:
  l=comp();a=comp()
  if method=='continuous':a=comp('DIFFERENT',xa_cont,['LJ-X8000A source documents continuous trigger configuration.'])
  if method=='external':a=comp('DIFFERENT',xa_ext,['LJ-X8000A source documents external trigger configuration.'])
  if method=='encoder':a=comp('DIFFERENT',xa_enc,['LJ-X8000A source documents encoder trigger configuration.'])
  trigger.append({'record_id':'trigger:'+method,'baseline_family':'LJ-X8000','comparison':{'LJ-S8000':l,'LJ-X8000A':a}})
 communication=[{'record_id':'communication:ethernet-nonprocedural','baseline_family':'LJ-X8000','comparison':{'LJ-S8000':comp('SAME',ls_port,['Common LJ-S8000/LJ-X8000 quick-start documents default port 8500.'],'communication:ethernet-nonprocedural'),'LJ-X8000A':comp()}}, {'record_id':'communication:fieldbus','baseline_family':'LJ-X8000','comparison':{'LJ-S8000':comp(),'LJ-X8000A':comp()}}]
 program=[{'record_id':'program:select-read-save','baseline_family':'LJ-X8000','comparison':{'LJ-S8000':comp(),'LJ-X8000A':comp()}}]
 wf=[]
 for x in workflows:
  wid=x['workflow_id'];l=comp();a=comp()
  if wid in {'ljx8000-pc-first-connection','ljx8000-software-trigger','ljx8000-read-latest-profile','ljx8000-fast-profile-read'}:l=comp('REUSABLE_WITH_VARIANT',ls_t1 if 'trigger' in wid else ls_port,['Shared manual provides only scoped common evidence; verify remaining bindings.'])
  if wid in {'ljx8000-external-trigger','ljx8000-software-trigger'}:a=comp('REUSABLE_WITH_VARIANT',xa_ext,['LJ-X8000A trigger configuration differs in documented tooling.'])
  wf.append({'record_id':'workflow:'+wid,'baseline_family':'LJ-X8000','comparison':{'LJ-S8000':l,'LJ-X8000A':a}})
 delta={'schema_version':1,'baseline_family':'LJ-X8000','command_deltas':cd,'signal_deltas':sd,'trigger_deltas':trigger,'communication_deltas':communication,'program_deltas':program,'workflow_deltas':wf};put(O/'hardware/controller_family_matrix.yaml',{'families':{'LJ-X8000':{'baseline':True},'LJ-S8000':{'operating_modes':'NOT_VERIFIED','communication_nonprocedural':'CONDITIONAL','trigger_methods':'NOT_VERIFIED','profile_output':'CONDITIONAL'},'LJ-X8000A':{'operating_modes':'CONDITIONAL','communication_nonprocedural':'NOT_VERIFIED','trigger_methods':'SUPPORTED','profile_output':'NOT_VERIFIED'}},'source_policy':'Cells other than LJ-X8000 baseline require family-specific evidence.'});put(O/'hardware/family_delta.yaml',delta)
 index=[]
 for group in [cd,sd,trigger,communication,program,wf]:
  for x in group:index.append({'record_id':x['record_id'],'LJ-X8000':'baseline','LJ-S8000':x['comparison']['LJ-S8000']['relation'],'LJ-X8000A':x['comparison']['LJ-X8000A']['relation']})
 put(O/'routing/family_delta_index.json',index)
 routes=json.loads((O/'routing/routing_map.yaml').read_text(encoding='utf8'));routes['family_applicability_policy']={'require_controller_family_before_controller_dependent_workflow':True,'unknown_controller':'infer explicit model; otherwise ask one targeted controller-family question; do not default to LJ-X8000'};put(O/'routing/routing_map.yaml',routes)
 soft={'software':[{'software':'LJ-X8000A Navi','supported_family':['LJ-X8000A'],'coverage':'OFFICIAL_CONTEXTUAL','source_evidence':[xa_cont]},{'software':'LJ-S Navi','supported_family':['LJ-S8000'],'coverage':'NOT_VERIFIED','source_evidence':[]},{'software':'Simulation Software','supported_family':[],'coverage':'NOT_VERIFIED','source_evidence':[]}]} ;put(O/'software/software_matrix.yaml',soft)
 table=['# Controller family comparison','', '| Capability | LJ-X8000 | LJ-X8000A | LJ-S8000 |','|---|---|---|---|','| Commands | YES baseline | NOT VERIFIED | PARTIAL shared T1/PFR/PFRF |','| Ethernet Non-Procedural | YES | NOT VERIFIED | YES, shared port evidence |','| I/O / timing | YES baseline | NOT VERIFIED | NOT VERIFIED |','| Trigger | YES baseline | DIFFERENT / family tool evidence | NOT VERIFIED |','| Profiles | YES baseline | NOT VERIFIED | PARTIAL shared PFR/PFRF |','| Programs | YES baseline | NOT VERIFIED | NOT VERIFIED |','| Fieldbus | YES baseline | NOT VERIFIED | NOT VERIFIED |','| Software | PARTIAL | LJ-X8000A Navi contextual | NOT VERIFIED |'];(O/'hardware/FAMILY_COMPARISON.md').write_text('\n'.join(table)+'\n',encoding='utf8')
 print(json.dumps({'command_deltas':len(cd),'signal_deltas':len(sd),'workflow_deltas':len(wf),'index':len(index)}))
if __name__=='__main__':main()
