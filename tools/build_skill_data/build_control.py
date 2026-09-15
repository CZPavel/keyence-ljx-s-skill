"""Second deterministic pass: control/integration discovery from chunks and tables."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; READY=ROOT/'corpus/keyence_skill_v1/skill_ready'; OUT=ROOT/'skill_data'
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
 chunks=[json.loads(x) for x in open(READY/'retrieval_chunks.jsonl',encoding='utf8')]; tables=[json.loads(x) for x in open(READY/'tables.jsonl',encoding='utf8')]
 ev=[]
 def evidence(x,quality='DIRECT'):
  r={'evidence_quality':quality,'document_id':x.get('source_reference',{}).get('document_id') or x.get('document_id'),'source_sha256':x['source_sha256'],'page':x.get('source_unit') or x.get('pdf_page'),'section_id':x.get('section_id'),'chunk_id':x.get('chunk_id'),'table_id':x.get('table_id'),'evidence_excerpt_hash':x.get('text_sha256') or x.get('cell_content_sha256')};ev.append(r);return r
 # Discover commands from prose headings/tables instead of a fixed known list.
 found={}
 for x in chunks:
  for m in re.finditer(r'\b([A-Z][A-Z0-9]{1,5})\s+command\b',x['text']):found.setdefault(m.group(1),[]).append(x)
 for x in tables:
  for c in re.findall(r'\b([A-Z][A-Z0-9]{1,5})\s+command\b',x.get('markdown','')):found.setdefault(c,[]).append(x)
 commands=[]
 for name,src in sorted(found.items()):
  direct=src[0]; text=(direct.get('text') or direct.get('markdown',''))
  commands.append({'command_id':'CMD-'+name,'command':name,'controller_family':'LJ-X8000' if 'LJ-X8000' in str(direct) else None,'communication_method':'EtherNet/IP' if 'EtherNet/IP' in text else None,'direction':'controller_control','operation_category':'discovered_command','purpose':None,'syntax':{'request':None,'parameters':[],'terminator':None,'status':'unresolved'},'response':{'normal_response':None,'error_response':None},'requirements':[],'effects':[],'related_commands':[],'related_signals':[],'related_data_flows':[],'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(direct)]})
 put(OUT/'operations/command_reference.yaml',{'discovery_method':'command headings and command tables','commands':commands})
 # Exact documented EtherNet/IP command-number mapping from table text is source direct.
 mappings=[]
 for t in tables:
  text=t.get('markdown','')
  if 'Number-specified' in text and 'Command' in text:
   for cmd,num in re.findall(r'\b([A-Z]{2,5})\s+command\s*\|\s*(\d+)',text):mappings.append({'command':cmd,'number_specified_command_no':int(num),'knowledge_status':'OFFICIAL_EXACT','source_evidence':[evidence(t)]})
 # Signals and relations: discover standard signal labels only when source text/table contains them.
 sigs={}
 for name in ('READY','TRG','TRG_ACK','EXT','ERROR','RUN','Command request flag','Command complete flag','Command error flag'):
  hit=next((x for x in chunks if re.search(r'\b'+re.escape(name)+r'\b',x['text'],re.I)),None)
  if hit:sigs[name]={'signal':name,'family':'LJ-X8000','direction':None,'logical_meaning':None,'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(hit)]}
 relations=[]
 for a,b,term,rel in [('TRG','READY',r'TRG.*READY|READY.*TRG','gated_by'),('Command request flag','Command complete flag',r'Command request flag|Command complete flag','acknowledged_by'),('Command error flag','Command complete flag',r'Command error flag','reports_error_after')]:
  hit=next((x for x in chunks if re.search(term,x['text'],re.I)),None)
  if hit:relations.append({'from':a,'relation':rel,'to':b,'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(hit)]})
 put(OUT/'operations/io_signal_reference.yaml',{'signals':list(sigs.values())});put(OUT/'operations/signal_relations.yaml',{'relations':relations})
 methods=[]
 for name in ('EtherNet/IP','PROFINET','EtherCAT','PLC-Link','RS-232C','FTP','Ethernet'):
  hit=next((x for x in chunks if name.lower() in x['text'].lower()),None)
  if hit:methods.append({'method_id':'COM-'+name.replace('/','-'),'method':name,'controller_applicability':None,'transport':None,'command_support':None,'result_support':None,'profile_support':None,'program_control_support':None,'framing':None,'mutual_exclusions':[],'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(hit)]})
 put(OUT/'communication/communication_matrix.yaml',{'methods':methods,'ethernet_ip_command_number_mapping':mappings})
 conflicts=[]
 for x in chunks:
  if re.search(r'cannot be used simultaneously|cannot communicate using|exclusive|unavailable when',x['text'],re.I):conflicts.append({'feature_A':None,'feature_B':None,'condition':'SOURCE_TEXT_NOT_REDISTRIBUTED; inspect local source locator','knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(x)]})
 put(OUT/'communication/communication_conflicts.yaml',{'conflicts':conflicts})
 flows=[]
 for fid,term in [('command-response','command.*response'),('async-result','result.*output'),('profile-read','profile.*read'),('program-switch','switching the program'),('ethernet-ip-command','command request flag')]:
  hit=next((x for x in chunks if re.search(term,x['text'],re.I)),None)
  if hit:flows.append({'flow_id':fid,'initiator':None,'source':'PC/PLC','destination':'controller','transport':None,'trigger':None,'request_payload':None,'response':None,'status_handshake':None,'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(hit)]})
 put(OUT/'communication/data_flow_reference.yaml',{'flows':flows})
 ops=[]
 for oid,term in [('select-program','program'),('save-settings','Saving settings'),('read-current-program','Obtaining the current program'),('command-execution','How to Execute Commands')]:
  hit=next((x for x in chunks if term.lower() in x['text'].lower()),None)
  if hit:ops.append({'operation_id':oid,'purpose':term,'where_performed':None,'persistent_effect':None,'knowledge_status':'OFFICIAL_CONTEXTUAL','source_evidence':[evidence(hit)]})
 put(OUT/'operations/program_operations.yaml',{'operations':ops});put(OUT/'operations/runtime_operations.yaml',{'operations':ops})
 put(OUT/'operations/pc_integration.yaml',{'official_facts':methods,'engineering_guidance':['Treat a TCP stream as a stream; do not assume one receive call equals one application message.']})
 put(OUT/'operations/plc_integration.yaml',{'fieldbus_methods':methods,'command_mapping':mappings})
 pb=[{'playbook_id':x,'canonical_targets':['operations/io_signal_reference.yaml','operations/signal_relations.yaml','communication/data_flow_reference.yaml'],'knowledge_status':'OFFICIAL_CONTEXTUAL' if x in ('command-error','trigger-ignored') else 'UNRESOLVED'} for x in ['pc-cannot-connect','command-no-response','command-error','trigger-ignored','READY-off','measurement-result-missing','profile-read-fails','wrong-program-active','PLC-link-not-working','fieldbus-data-not-updating']]
 put(OUT/'diagnostics/troubleshooting_playbooks.yaml',{'playbooks':pb})
 routes=['DEVICE','CONNECT','CONFIGURE_COMMUNICATION','COMMAND','TRIGGER','SIGNAL','PROGRAM','RESULT','PROFILE','PLC','FIELDBUS','BACKUP','RESTORE','DIAGNOSE','ERROR','MEASUREMENT'];put(OUT/'routing/routing_map.yaml',{'intent_families':[{'intent':x,'required_context':['controller_family'],'canonical_targets':['operations/command_reference.yaml','communication/communication_matrix.yaml']} for x in routes]})
 slots=['controller_family','controller_model','head_model','software_version','firmware_version','2D_or_3D_mode','communication_method','program_number','trigger_method','PC_or_PLC','symptom','command','signal'];put(OUT/'routing/context_schema.yaml',{'slots':[{'slot':s,'optional':True,'required_for':['COMMAND','TRIGGER','CONNECT','PLC']} for s in slots]})
 for n,rows in [('command_index.json',commands),('signal_index.json',list(sigs.values())),('communication_index.json',methods),('data_flow_index.json',flows),('program_operation_index.json',ops),('runtime_operation_index.json',ops),('troubleshooting_index.json',pb)]:put(OUT/'routing'/n,[{'id':x.get('command_id') or x.get('signal') or x.get('method_id') or x.get('flow_id') or x.get('operation_id') or x.get('playbook_id'),'aliases':[]} for x in rows])
 path=OUT/'evidence/evidence_index.jsonl';old=path.read_text(encoding='utf8') if path.exists() else '';path.write_text(old+''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in ev),encoding='utf8')
 md='# Control and integration review\n\nSafe now: EtherNet/IP command-number mapping and command handshake evidence where marked exact. Contextual records require raw corpus lookup for syntax/limits.\n';(OUT/'CONTROL_INTEGRATION_REVIEW.md').write_text(md,encoding='utf8')
 print(json.dumps({'commands_discovered':len(commands),'exact_mappings':len(mappings),'signals':len(sigs),'relations':len(relations),'methods':len(methods),'flows':len(flows),'evidence':len(ev)}))
if __name__=='__main__':main()

