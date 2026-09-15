"""Recover LJ-X8000 I/O, timing and handshake facts from focused source pages."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'skill_data'; PDF=ROOT/'Downloads/AS_166309_LJ-X8000_UM_N04GB_WW_GB_2036_1.pdf'
DOC='KEYENCE-E3E51B234B56'; SHA='e3e51b234b56ea11182e78b39574678f5c7244c65d6455664927f580dd1a47c3'
PAGES={274:'9-52',276:'9-54',277:'9-55',279:'9-57',280:'9-58',281:'9-59',286:'9-64',287:'9-65',288:'9-66',292:'9-70',293:'9-71',295:'9-73',296:'9-74',298:'9-76',299:'9-77',300:'9-78',301:'9-79',302:'9-80'}
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def capture():
 if digest(PDF)!=SHA: raise RuntimeError('registered PDF SHA mismatch')
 d=fitz.open(PDF); q=OUT/'evidence/manual_source_blocks';q.mkdir(parents=True,exist_ok=True); out={}
 for page,printed in PAGES.items():
  t=d[page-1].get_text('text');bid=f'MSB-LJX8000-{page:03d}-IO_TIMING'
  x={'block_id':bid,'document_id':DOC,'source_sha256':SHA,'pdf_page_index':page,'printed_page':printed,'bbox':None,'block_type':'timing_diagram' if page>=292 else 'terminal_table','native_text_sha256':hashlib.sha256(t.encode()).hexdigest(),'visual_verification':page in {293,295,296,298,299,300,301,302},'evidence_status':'DIRECT_VISUAL' if page in {293,295,296,298,299,300,301,302} else 'DIRECT_NATIVE','fields_supported':['I/O/timing facts']}
  (q/f'{bid}.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8');out[page]=x
 return out
def ev(x):return {'evidence_quality':x['evidence_status'],'block_id':x['block_id'],'document_id':DOC,'source_sha256':SHA,'pdf_page_index':x['pdf_page_index'],'printed_page':x['printed_page'],'evidence_excerpt_hash':x['native_text_sha256']}
def exact(v,b):return {'value':v,'status':'OFFICIAL_EXACT','evidence':[ev(b)]}
def sig(name,direction,b,meaning,**kw):
 return {'signal_id':'SIG-'+name,'signal_name':name,'controller_family':'LJ-X8000','not_verified_for':['LJ-X8000A','LJ-S8000'],'direction':direction,'physical_context':None,'logic':{'active_level':None,'active_edge':None,'pulse_or_level':None},'meaning':exact(meaning,b),'valid_when':kw.get('valid_when',{'value':None,'status':'UNRESOLVED','evidence':[]}),'causes':kw.get('causes',[]),'effects':kw.get('effects',[]),'timing':kw.get('timing',{}),'related_signals':kw.get('related_signals',[]),'related_commands':kw.get('related_commands',[]),'related_runtime_operations':kw.get('related_runtime_operations',[]),'diagnostic_interpretation':None,'knowledge_status':'OFFICIAL_EXACT','direct_evidence':[ev(b)],'supporting_evidence':[]}
def relation(src,rel,target,b,condition):return {'source_signal':src,'relation':rel,'target_signal_or_operation':target,'condition':condition,'controller_family':'LJ-X8000','not_verified_for':['LJ-X8000A','LJ-S8000'],'status':'OFFICIAL_EXACT','evidence':[ev(b)]}
def main():
 B=capture();
 signals=[
  sig('READY','output',B[295],'indicates whether TRG input can be accepted',causes=[exact('turns OFF after accepted trigger during imaging/transfer; turns ON after imaging/transfer completes',B[295])],effects=[exact('gates TRG input',B[295])],timing={'ready_falling_response_delay':exact('less than 0.5 ms',B[302])},related_signals=['TRG','EXT','LD ON','BUSY'],related_commands=['T1','TE']),
  sig('TRG','input',B[295],'external trigger input',valid_when=exact('accepted while READY is ON',B[295]),timing={'minimum_input_time':{'value':None,'status':'UNRESOLVED','evidence':[]}},related_signals=['READY','ERROR']),
  sig('EXT','input',B[302],'pauses image capture',causes=[exact('EXT ON forces READY OFF',B[302])],effects=[exact('blocks trigger input from external terminals, PLC, RS-232C, Ethernet and mouse; stops capture and measurement processing',B[302])],timing={'minimum_input_time':exact('more than 1 ms',B[302]),'ready_response_delay':exact('less than 0.5 ms',B[302])},related_signals=['READY'],related_commands=['T1']),
  sig('TEST','input',B[301],'cancels terminal output operations',effects=[exact('while ON, forces OUT_DATA[15:0], OR and STO to normal state',B[301])],timing={'response_delay':exact('within 500 microseconds',B[301]),'minimum_input_time':exact('more than 1 ms',B[301])},related_signals=['OUT_DATA','OR','STO']),
  sig('RESET','input',B[300],'sets output terminals to normal state and resets trigger-wait state',causes=[exact('READY goes OFF once during reset and returns ON after reset completes',B[300])],timing={'minimum_input_time':exact('more than 1 ms',B[300]),'response_delay':exact('less than 1 ms',B[300]),'reset_time':exact('less than 1 second',B[300])},related_signals=['READY','BUSY']),
  sig('BUSY','output',B[286],'indicates measurement processing or terminal-block command execution',related_signals=['CST','CMD_READY','ACK','NACK']),
  sig('RUN','output',B[293],'turns ON when system enters Run mode when startup mode is Run mode',related_commands=['R0','S0']),
  sig('CMD_READY','output',B[286],'indicates acceptance of terminal-block command inputs',causes=[exact('turns ON after ACK or NACK turns OFF',B[286])],effects=[exact('CST while CMD_READY is OFF is ignored without ACK/NACK response',B[286])],related_signals=['CST','ACK','NACK','BUSY']),
  sig('ACK','output',B[286],'indicates successful terminal-block command execution',timing={'duration':exact('same as STO output ON time',B[288])},related_signals=['CMD_READY','NACK']),
  sig('NACK','output',B[286],'indicates failed terminal-block command execution',timing={'duration':exact('same as STO output ON time',B[288])},related_signals=['CMD_READY','ACK']),
  sig('STO','output',B[299],'data-strobe output for terminal result data',timing={'output_rise_time':exact('1 to 999 ms',B[299]),'output_time':exact('1 to 999 ms',B[299])},related_signals=['OUT_DATA','PST','OR']),
  sig('OUT_DATA[15:0]','output',B[299],'outputs judgment-result data',related_signals=['STO','OR','PST']),
  sig('OR','output',B[299],'total judgment output in terminal data-output timing',related_signals=['STO','OUT_DATA[15:0]']),
  sig('PST','input',B[299],'handshake input for terminal data switching',effects=[exact('STO turns OFF after PST ON-to-OFF; next data switches after PST OFF-to-ON',B[299])],timing={'off_response':exact('less than 0.5 ms',B[299]),'minimum_input_time':exact('less than 1.0 ms',B[299]),'on_response':exact('less than 0.5 ms',B[299])},related_signals=['STO','OUT_DATA[15:0]']),
 ]
 error=sig('ERROR','output',B[295],'error output is shown for encoder-trigger timing when trigger period is violated')
 error['knowledge_status']='OFFICIAL_CONTEXTUAL'; error['meaning']['status']='OFFICIAL_CONTEXTUAL'
 signals.append(error)
 rel=[relation('READY','gates','TRG',B[295],'TRG accepted only while READY is ON'),relation('TRG','initiates','imaging_and_profile_transfer',B[295],'accepted trigger'),relation('EXT','forces_off','READY',B[302],'EXT input ON'),relation('TEST','clears','terminal_output',B[301],'TEST input ON'),relation('RESET','temporarily_clears','READY',B[300],'reset processing'),relation('CMD_READY','gates','CST',B[286],'terminal command input'),relation('ACK','precedes','CMD_READY',B[286],'ACK turns OFF'),relation('NACK','precedes','CMD_READY',B[286],'NACK turns OFF'),relation('STO','strobes','OUT_DATA[15:0]',B[299],'terminal result output')]
 put=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 put(OUT/'operations/io_signal_reference.yaml',{'schema_version':2,'signals':signals});put(OUT/'operations/signal_relations.yaml',{'schema_version':2,'relations':rel})
 methods=[{'method_id':'external_trigger','controller_family':'LJ-X8000','initiator':'TRG input','required_state':'READY ON','related_signal_or_command':['TRG','READY'],'timing_restrictions':['encoder period must not fall below trigger-period setting'], 'source_evidence':[ev(B[295])]}, {'method_id':'software_trigger','controller_family':'LJ-X8000','initiator':'T1 command','required_state':'trigger accepted / trigger input enabled','related_signal_or_command':['T1','READY','TE'],'timing_restrictions':[],'source_evidence':[ev(B[295])]}, {'method_id':'continuous_trigger','controller_family':'LJ-X8000','initiator':'configured continuous trigger','required_state':'READY is always OFF','related_signal_or_command':['READY'],'timing_restrictions':[],'source_evidence':[ev(B[296])]}, {'method_id':'encoder_trigger','controller_family':'LJ-X8000','initiator':'encoder','required_state':'READY is always OFF','related_signal_or_command':['READY','ERROR'],'timing_restrictions':['encoder trigger period must not fall below trigger-period setting'],'source_evidence':[ev(B[295])]}, {'method_id':'multiple_trigger','controller_family':'LJ-X8000','initiator':'external trigger','required_state':'READY ON after transfer completes','related_signal_or_command':['TRG','READY'],'timing_restrictions':[],'source_evidence':[ev(B[298])]}]
 put(OUT/'operations/trigger_methods.yaml',{'methods':methods})
 timing={'sequences':[{'sequence_id':'external-trigger-cycle','status':'OFFICIAL_EXACT','steps':['READY ON','TRG accepted','imaging/profile transfer while READY OFF','READY ON after transfer complete'],'evidence':[ev(B[295])]}, {'sequence_id':'continuous-trigger-cycle','status':'DERIVED_OPERATIONAL_SEQUENCE','steps':['configured trigger cycle','imaging/transfer','measurement processing may run in parallel','judgment/output'],'evidence':[ev(B[296])]}],'numeric_constraints':[{'name':'startup_ready_delay','value':'more than 5 ms after stated startup stage','evidence':[ev(B[293])]}, {'name':'terminal_output_rise_time','value':'1 to 999 ms','evidence':[ev(B[299])]}]}
 put(OUT/'operations/trigger_timing.yaml',timing)
 terminals={'mappings':[{'controller_family':'LJ-X8000','connector':'parallel I/O interface','terminal':pin,'signal':name,'direction':direction,'electrical_specification':None,'knowledge_status':'OFFICIAL_EXACT','source_evidence':[ev(B[274])]} for pin,name,direction in [('14 / IN12','CST','input'),('15 / IN13','RESET','input'),('16 / IN14','PST','input'),('18 / OUT0','ACK','output'),('19 / OUT1','NACK','output'),('20 / OUT2','BUSY','output'),('21 / OUT3','CMD_READY','output'),('24..39 / OUT6..OUT21','OUT_DATA[15:0]','output')]], 'electrical_coverage':{'input_circuit':exact('maximum applied voltage 26.4 V; thresholds differ by input circuit',B[280]),'output_circuit':exact('maximum applied voltage 30 V; maximum sink current 50 mA',B[281]),'laser_on_input':exact('I/O connector terminal 5; non-voltage input',B[279])}}
 put(OUT/'operations/io_terminal_reference.yaml',terminals)
 # Cross-link only; command remains canonical in its own file.
 cmd=json.loads((OUT/'operations/command_reference.yaml').read_text(encoding='utf8'));by={x['command']:x for x in cmd['commands']}
 for c,links in {'T1':['TRG','READY'],'TE':['TRG','READY'],'R0':['RUN'],'S0':['RUN'],'RS':['READY','BUSY']}.items():
  if c in by: by[c]['related_signals']=links
 cmd['commands']=[by[k] for k in sorted(by)];put(OUT/'operations/command_reference.yaml',cmd)
 # Deterministic indexes and narrow diagnostic/routing views.
 put(OUT/'routing/signal_index.json',[{'id':x['signal_id'],'signal':x['signal_name'],'aliases':[x['signal_name'].lower(),x['signal_name'].lower()+' signal']} for x in signals]);put(OUT/'routing/trigger_index.json',[{'id':x['method_id'],'aliases':[x['method_id'].replace('_',' ')]} for x in methods])
 put(OUT/'routing/runtime_operation_index.json',[{'id':'runtime-trigger','aliases':['trigger','trigger cycle'],'targets':['SIG-READY','SIG-TRG']},{'id':'runtime-terminal-command','aliases':['CST','command handshake'],'targets':['SIG-CMD_READY','SIG-ACK','SIG-NACK']}])
 routes=json.loads((OUT/'routing/routing_map.yaml').read_text(encoding='utf8')); existing={x['intent'] for x in routes['intent_families']}
 for i in ['trigger_not_working','ready_off','external_trigger','software_trigger','continuous_trigger','encoder_trigger','error_signal','busy_signal','result_ready','io_wiring','io_timing']:
  if i not in existing: routes['intent_families'].append({'intent':i,'required_context':['controller_family'],'canonical_targets':['operations/io_signal_reference.yaml','operations/signal_relations.yaml','operations/trigger_timing.yaml','operations/trigger_methods.yaml']})
 put(OUT/'routing/routing_map.yaml',routes)
 play={'playbooks':[{'playbook_id':i,'canonical_targets':['operations/io_signal_reference.yaml','operations/signal_relations.yaml','operations/trigger_methods.yaml'],'knowledge_status':'OFFICIAL_EXACT'} for i in ['trigger-ignored','READY-off','controller-not-running','error-active','measurement-does-not-start','result-not-produced']]};put(OUT/'diagnostics/troubleshooting_playbooks.yaml',play)
 put(OUT/'routing/troubleshooting_index.json',[{'id':x['playbook_id'],'aliases':[x['playbook_id'].replace('-',' ')]} for x in play['playbooks']])
 lines=['# I/O signal reference','']+[f"- **{s['signal_name']}** ({s['direction']}): {s['meaning']['value']}" for s in signals];putmd=lambda p,t:p.write_text(t,encoding='utf8');putmd(OUT/'operations/IO_SIGNAL_REFERENCE.md','\n'.join(lines)+'\n');putmd(OUT/'operations/TRIGGER_TIMING_REFERENCE.md','# Trigger and timing reference\n\n'+ '\n'.join(f"- {x['sequence_id']}: {' -> '.join(x['steps'])}" for x in timing['sequences'])+'\n')
 # append manual evidence index idempotently
 ep=OUT/'evidence/evidence_index.jsonl'; old=ep.read_text(encoding='utf8') if ep.exists() else '';ids={json.loads(x).get('record_id') for x in old.splitlines() if x}
 with ep.open('a',encoding='utf8') as f:
  for b in B.values():
   if b['block_id'] not in ids:f.write(json.dumps({'record_id':b['block_id'],'knowledge_file':'evidence/manual_source_blocks','knowledge_key':b['block_id'],'document_id':DOC,'page':b['pdf_page_index'],'printed_page':b['printed_page'],'source_sha':SHA,'evidence_excerpt_hash':b['native_text_sha256'],'evidence_status':b['evidence_status']})+'\n')
 print(json.dumps({'signals':len(signals),'relations':len(rel),'trigger_methods':len(methods),'source_blocks':len(B)}))
if __name__=='__main__':main()

