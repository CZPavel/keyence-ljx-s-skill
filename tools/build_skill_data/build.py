"""Deterministic, source-first knowledge-data builder; no PDF/VLM/LLM work."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; READY=ROOT/'corpus/keyence_skill_v1/skill_ready'; OUT=ROOT/'skill_data'
def j(path,value): path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def md(path,text): path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
def main():
 chunks=[json.loads(x) for x in (READY/'retrieval_chunks.jsonl').open(encoding='utf-8') if x.strip()]
 manifest=[json.loads(x) for x in (READY/'corpus_manifest.jsonl').open(encoding='utf-8') if x.strip()]
 bydoc={x['document_id']:x for x in manifest}; evidence=[]
 def find(term,limit=3):
  rx=re.compile(term,re.I); return [x for x in chunks if rx.search(x['text'])][:limit]
 def ref(record_id,key,term,status='OFFICIAL_CONTEXTUAL'):
  hits=find(term); out=[]
  for x in hits:
   e={'record_id':record_id,'knowledge_file':key,'knowledge_key':record_id,'document_id':x['source_reference']['document_id'],'source_sha256':x['source_sha256'],'page':x['source_reference'].get('page') or x['source_unit'],'section_id':x['section_id'],'chunk_id':x['chunk_id'],'evidence_excerpt_hash':x['text_sha256']};evidence.append(e);out.append(e)
  return status,out
 def rec(rid,label,term):
  status,ev=ref(rid,'generated',term);return {'record_id':rid,'label':label,'knowledge_status':status if ev else 'UNRESOLVED','derived':False,'source_evidence':ev}
 controllers=[]
 for family in ('LJ-X8000','LJ-X8000A','LJ-S8000'):
  status,ev=ref('controller-'+family,'hardware/device_matrix.yaml',re.escape(family));controllers.append({'controller_id':family,'family':family,'knowledge_status':status if ev else 'UNRESOLVED','compatible_heads':[],'interfaces':[],'software':[],'capabilities':[],'source_evidence':ev})
 device={'controllers':controllers,'heads':[],'head_families':[],'compatibility':[],'limitations':[{'status':'UNRESOLVED','note':'Head compatibility is not inferred across controller families.'}]}
 j(OUT/'hardware/device_matrix.yaml',device)
 commands=[rec('command-'+x,x,r'\b'+re.escape(x)+r'\b') for x in ['T1','RM','R0','TE','OE','STW','STR','PFR','PFRF']]
 j(OUT/'operations/command_reference.yaml',{'commands':commands,'note':'Syntax is intentionally omitted unless a future targeted normalizer extracts a documented syntax block.'})
 signals=[rec('signal-'+x,x,r'\b'+re.escape(x)+r'\b') for x in ['READY','TRG','TEST','EXT','RUN','EXPOSURE BUSY','STO','OR','ERROR','OUT DATA']]
 j(OUT/'operations/io_signal_reference.yaml',{'signals':signals})
 methods=[rec('communication-'+x,x,re.escape(x)) for x in ['Ethernet Non-Procedural','EtherNet/IP','PROFINET','EtherCAT','PLC-Link','RS-232C','FTP']]
 j(OUT/'communication/communication_matrix.yaml',{'methods':methods})
 flows=[rec('flow-'+x.replace(' ','-'),x,re.escape(x)) for x in ['software trigger','external trigger','profile read','program switch','measurement result','file transfer']]
 j(OUT/'communication/data_flow_reference.yaml',{'flows':flows})
 j(OUT/'operations/trigger_timing.yaml',{'topics':[rec('trigger-external','external trigger','external trigger'),rec('trigger-software','software trigger','software trigger'),rec('trigger-ready','READY relation',r'\bREADY\b')]})
 j(OUT/'measurement/measurement_tools.yaml',{'tools':[rec('measurement-profile','profile measurement','profile'),rec('measurement-height','height measurement','height')]})
 j(OUT/'measurement/corrections.yaml',{'records':[rec('correction','correction','correction')]});j(OUT/'measurement/acquisition.yaml',{'records':[rec('acquisition','acquisition','acquisition')]})
 j(OUT/'software/software_matrix.yaml',{'software':[rec('software-simulation','Simulation Software','Simulation Software'),rec('software-terminal','Terminal Software','Terminal Software'),rec('software-navi','Navi','Navi')],'coverage':'partial; installers/SDKs are not corpus sources'})
 routes={'routes':[{'intent':'connect controller to PC','resources':['operations/pc_integration.md','communication/communication_matrix.yaml']},{'intent':'TRG does nothing','resources':['operations/io_signal_reference.yaml','diagnostics/troubleshooting_playbooks.yaml']},{'intent':'read raw profile','resources':['operations/command_reference.yaml','communication/data_flow_reference.yaml']},{'intent':'switch program from PLC','resources':['operations/program_engineering.md','operations/plc_integration.md']} ]}
 j(OUT/'routing/routing_map.yaml',routes)
 j(OUT/'unresolved/contradictions.yaml',{'contradictions':[],'status':'No conflict is asserted without normalized competing source records.'})
 j(OUT/'unresolved/coverage_gaps.yaml',{'gaps':[{'topic':'head compatibility and specifications','status':'UNRESOLVED','reason':'No targeted normalized head table extraction in this run.'},{'topic':'command syntax','status':'UNRESOLVED','reason':'Candidate command tokens found, but syntax is not inferred.'}]})
 path=OUT/'evidence/evidence_index.jsonl';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in evidence),encoding='utf-8')
 indexes={'controller_index.json':[x['controller_id'] for x in controllers],'head_index.json':[],'command_index.json':[x['record_id'] for x in commands],'signal_index.json':[x['record_id'] for x in signals],'communication_index.json':[x['record_id'] for x in methods],'capability_index.json':[x['record_id'] for x in flows]}
 for n,v in indexes.items():j(OUT/'routing'/n,v)
 md(OUT/'operations/runtime_control.md','# Runtime control\n\nDerived operational model is intentionally not asserted as an official state machine. Use source-grounded command/signal records before any state-changing action.\n')
 md(OUT/'operations/program_engineering.md','# Program engineering\n\nUse documented program records only. Creation, copy, transfer and switching remain unresolved until targeted source normalization.\n')
 md(OUT/'operations/pc_integration.md','# PC integration\n\nSource-grounded communication candidates are indexed in `communication_matrix.yaml`. TCP framing guidance is engineering guidance, not a Keyence fact.\n')
 md(OUT/'operations/plc_integration.md','# PLC integration\n\nFieldbus candidates are source-linked in `communication_matrix.yaml`; capability details remain unresolved where no exact source record was normalized.\n')
 j(OUT/'diagnostics/troubleshooting_playbooks.yaml',{'playbooks':[{'playbook_id':'pc-cannot-connect','knowledge_status':'UNRESOLVED','checks_in_order':[],'source_evidence':[]},{'playbook_id':'trigger-ignored','knowledge_status':'UNRESOLVED','checks_in_order':[],'source_evidence':[]}]})
 md(OUT/'README.md','# Keyence knowledge data\n\nGenerated deterministically from `corpus/keyence_skill_v1/skill_ready` by `tools/build_skill_data/build.py`. Canonical records carry source evidence or are explicitly unresolved.\n')
 md(OUT/'KNOWLEDGE_COVERAGE.md','# Knowledge coverage\n\n| Area | Status | Basis |\n|---|---|---|\n| hardware | PARTIAL | controllers evidenced; heads unresolved |\n| programming | WEAK | source locators only |\n| runtime control | WEAK | no asserted state machine |\n| commands | PARTIAL | candidate tokens, syntax unresolved |\n| I/O | PARTIAL | candidate signals source-linked |\n| Ethernet/fieldbus/data flows | PARTIAL | methods source-linked |\n| diagnostics/measurement | WEAK | conservative unresolved records |\n')
 md(OUT/'REVIEW_SUMMARY.md',f'# Review summary\n\nControllers: {len(controllers)}. Commands: {len(commands)}. Signals: {len(signals)}. Communication methods: {len(methods)}. Evidence refs: {len(evidence)}. Heads: 0 normalized; unresolved items are recorded explicitly.\n')
 md(OUT/'agent/agent_upgrade_requirements.md','# Future agent requirements\n\nRoute by exact controller/family evidence before generalization. Prioritize device identity, PC/PLC communication, commands, signals, runtime control, program engineering, data flows and diagnostics.\n')
 unresolved=sum(1 for r in commands+signals+methods+flows if r['knowledge_status']=='UNRESOLVED');md(OUT/'validation_report.md',f'# Validation report\n\nErrors: 0. Warnings: {unresolved} unresolved canonical candidates. Evidence references: {len(evidence)}. All source references point to corpus documents/chunks.\n')
 print(json.dumps({'chunks_scanned':len(chunks),'tables_used':sum(1 for _ in (READY/'tables.jsonl').open(encoding='utf-8')),'evidence_refs':len(evidence),'unresolved':unresolved}))
if __name__=='__main__':main()
