"""Build the conservative, source-grounded LJ-X8000 measurement/program layer.

The normalizer uses only matching FAST-PASS chunks.  Missing source fields remain
null/UNRESOLVED; it does not infer parameters, limits, or cross-mode support.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'skill_data'
CHUNKS=ROOT/'corpus'/'keyence_skill_v1'/'skill_ready'/'retrieval_chunks.jsonl'

def write(path, value):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def load_chunks(): return [json.loads(x) for x in CHUNKS.open(encoding='utf8')]
def evidence(chunks, phrase, mode=None):
 for c in chunks:
  if phrase.lower() in c.get('text','').lower() and (mode is None or mode.lower() in c['document_id'].lower()):
   return {'evidence_quality':'DIRECT_NATIVE','document_id':c['source_reference']['document_id'],'source_sha256':c['source_sha256'],'page':c.get('source_unit'),'section_id':c['section_id'],'chunk_id':c['chunk_id'],'evidence_excerpt_hash':c['text_sha256']}
 return None
def req(chunks, phrase, mode=None):
 e=evidence(chunks,phrase,mode)
 if not e: raise RuntimeError('missing required source phrase: '+phrase)
 return e

def main():
 c=load_chunks()
 by_chunk={x['chunk_id']:x for x in c}
 def direct_chunk(chunk_id):
  x=by_chunk[chunk_id]
  return {'evidence_quality':'DIRECT_NATIVE','document_id':x['source_reference']['document_id'],'source_sha256':x['source_sha256'],'page':x.get('source_unit'),'section_id':x['section_id'],'chunk_id':x['chunk_id'],'evidence_excerpt_hash':x['text_sha256']}
 op_evidence={
  'select':direct_chunk('CHK-AS-111562-LJ-X8000-SG-600X40-WW-GB-2050-3-BAF1B51B5A0E-U0002-C008'),
  'read':direct_chunk('CHK-LJ-X8000-SERIES-3D-EASY-CONFIGURATION-MANUAL-ETHERNET-IP-EDITION-ALLEN-BRADLEY-CONTROLLOGIX-SERIES-D48GB-0A6360680FCE-U0033-C007'),
  'command':direct_chunk('CHK-LJ-X8000-SERIES-3D-EASY-CONFIGURATION-MANUAL-ETHERNET-IP-EDITION-ALLEN-BRADLEY-CONTROLLOGIX-SERIES-D48GB-0A6360680FCE-U0035-C001')}
 e2d={k:req(c,v) for k,v in {'height_difference_width':'Height Difference/Width','height_position':'Height and Position Measurement','angle':'Angle Measurement','r_measurement':'R Measurement','profile_length':'Profile Length','cross_section_area':'Cross-Section Area','position_correction':'Position correction processes are performed in order'}.items()}
 e3d={k:req(c,v) for k,v in {'cross_section':'cross-section can be measured','profile_flattening':'Profile Flattening Correction','installation_tilt':'Installation Tilt Correction Angle','tool_output':'Height Measurement tool','save':'Saves the current program settings and global settings'}.items()}
 tools=[]
 for tool_id,name,purpose,outputs in [
  ('height-difference-width','Height Difference/Width','Measures source-described height difference and width in a configured area.',['height difference','width']),
  ('height-position','Height and Position','Measures source-described height (Z) and position (X) of a feature.',['height','position']),
  ('angle','Angle Measurement','Measures angle where the tool is selected/configured.',['angle']),
  ('r-measurement','R Measurement','Measures R/radius where the tool is selected/configured.',['radius']),
  ('profile-length','Profile Length','Measures profile length.',['profile length']),
  ('cross-section-area','Cross-Section Area','Measures cross-section area.',['cross-section area']),
 ]:
  key=tool_id.replace('-','_')
  tools.append({'tool_id':tool_id,'official_name':name,'applicability':{'controller_family':'LJ-X8000','mode':'2D','head_requirements':None},'purpose':purpose,'measurement_principle':None,'inputs':['profile/measurement region: exact configuration remains source-specific'],'regions':{'canonical_roles':['measurement_region'],'official_terms_unresolved':True},'configuration_parameters':[],'outputs':[{'name':x,'semantic_meaning':x,'unit':None,'coordinate_semantics':None,'invalid_behavior':None,'source_evidence':[e2d[key]]} for x in outputs],'filters':[],'scaling':None,'offset':None,'judgment':{'status':'SOURCE_CONTEXTUAL','upper_lower_limits':None},'position_correction_support':'UNRESOLVED_PER_TOOL','limitations':['Do not use this 2D record for 3D routing.'],'related_tools':[],'related_corrections':['position-correction'],'direct_evidence':[e2d[key]],'supporting_evidence':[],'knowledge_status':'OFFICIAL_CONTEXTUAL'})
 tools.append({'tool_id':'cross-section-measurement','official_name':'Cross-section measurement','applicability':{'controller_family':'LJ-X8000','mode':'3D','head_requirements':None},'purpose':'A specified location cross-section can be measured for documented height, width, angle, and cross-section area.','measurement_principle':None,'inputs':['3D cross-section at specified location'],'regions':{'canonical_roles':['cross_section_location'],'official_terms_unresolved':True},'configuration_parameters':[],'outputs':[{'name':x,'semantic_meaning':x,'unit':None,'coordinate_semantics':None,'invalid_behavior':None,'source_evidence':[e3d['cross_section']]} for x in ['height','width','angle','cross-section area']],'filters':[],'scaling':None,'offset':None,'judgment':{'status':'SOURCE_CONTEXTUAL','upper_lower_limits':None},'position_correction_support':'UNRESOLVED_PER_TOOL','limitations':['This record is 3D-only; it is not a 2D tool alias.'],'related_tools':[],'related_corrections':['profile-flattening-correction','installation-tilt-correction'],'direct_evidence':[e3d['cross_section']],'supporting_evidence':[],'knowledge_status':'OFFICIAL_CONTEXTUAL'})
 write(OUT/'measurement'/'measurement_tools.yaml',{'tools':tools})
 corrections=[
  {'correction_id':'position-correction','official_name':'Position Correction','family':'LJ-X8000','mode':'2D','purpose':'Correction processes are performed in source-defined screen order.','input':None,'reference_definition':None,'degrees_of_freedom':'UNRESOLVED','effect_on_profile_result':None,'configuration':None,'limitations':['Documented coordinate space and per-tool follow behavior require targeted source lookup.'],'order_dependencies':'Source states correction processes are performed top-to-bottom.','compatible_tools':[],'source_evidence':[e2d['position_correction']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},
  {'correction_id':'profile-flattening-correction','official_name':'Profile Flattening Correction','family':'LJ-X8000','mode':'3D','purpose':'Source documents this named correction.','input':None,'reference_definition':None,'degrees_of_freedom':'UNRESOLVED','effect_on_profile_result':None,'configuration':'[Profile Flattening Correction] settings','limitations':['Do not generalize to arbitrary 3D/yaw correction.'],'order_dependencies':None,'compatible_tools':[],'source_evidence':[e3d['profile_flattening']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},
  {'correction_id':'installation-tilt-correction','official_name':'Installation Tilt Correction Angle','family':'LJ-X8000','mode':'3D','purpose':'Source documents this named installation tilt correction setting.','input':None,'reference_definition':None,'degrees_of_freedom':'UNRESOLVED','effect_on_profile_result':None,'configuration':None,'limitations':['No claim of correcting any unverified rotation axis.'],'order_dependencies':None,'compatible_tools':[],'source_evidence':[e3d['installation_tilt']],'knowledge_status':'OFFICIAL_CONTEXTUAL'}]
 write(OUT/'measurement'/'corrections.yaml',{'records':corrections})
 acquire=[{'setting_id':'trigger-and-acquisition','setting':'Trigger/acquisition configuration','family':'LJ-X8000','mode':'2D_OR_3D_CONTEXT_REQUIRED','allowed_values':None,'effect':'Use the existing trigger-method reference for exact method semantics.','trade_off':None,'related_trigger_method_refs':['measurement/trigger_methods.yaml'],'source_evidence':[e3d['tool_output']],'knowledge_status':'OFFICIAL_CONTEXTUAL'}]
 write(OUT/'measurement'/'acquisition.yaml',{'settings':acquire})
 stages=['acquisition','correction','measurement_tool','judgment','output','program_persistence']
 write(OUT/'measurement'/'program_structure.yaml',{'controller_family':'LJ-X8000','stages':[{'stage_id':x,'name':x.replace('_',' '),'purpose':None,'mode_applicability':'CONTEXT_REQUIRED','depends_on':stages[:i],'produces':None,'configuration_location':None,'source_evidence':[e3d['save']],'knowledge_status':'OFFICIAL_CONTEXTUAL'} for i,x in enumerate(stages)]})
 operations=[{'operation_id':'select-program','operation':'select/switch','family':'LJ-X8000','mode':'CONTEXT_REQUIRED','where_performed':'controller UI or documented communication path','online_offline':'UNRESOLVED','input':None,'effect':'Selects a program; exact method depends on source path.','persistent':'UNRESOLVED','related_command':None,'classification':'STATE_CHANGING','source_evidence':[op_evidence['select']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},{'operation_id':'read-current-program','operation':'read current program','family':'LJ-X8000','mode':'3D','where_performed':'fieldbus/control context','online_offline':'UNRESOLVED','input':None,'effect':'Obtains the current program.','persistent':'UNRESOLVED','related_command':None,'classification':'READ_ONLY','source_evidence':[op_evidence['read']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},{'operation_id':'save-program-settings','operation':'save','family':'LJ-X8000','mode':'3D','where_performed':'controller/software UI per source context','online_offline':'UNRESOLVED','input':'current program and global settings','effect':'Saves current program settings and global settings.','persistent':'YES','related_command':None,'classification':'STATE_CHANGING','source_evidence':[e3d['save']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},{'operation_id':'command-execution','operation':'execute documented command','family':'LJ-X8000','mode':'3D','where_performed':'documented communication context','online_offline':'UNRESOLVED','input':None,'effect':'Use canonical command reference for syntax.','persistent':'UNRESOLVED','related_command':None,'classification':'STATE_CHANGING_OR_READ_ONLY_DEPENDS_ON_COMMAND','source_evidence':[op_evidence['command']],'knowledge_status':'OFFICIAL_CONTEXTUAL'}]
 write(OUT/'operations'/'program_operations.yaml',{'operations':operations})
 write(OUT/'measurement'/'calculations.yaml',{'capabilities':[],'coverage_status':'UNRESOLVED_NO_NORMALIZED_DIRECT_SOURCE_IN_THIS_PASS'})
 write(OUT/'measurement'/'judgment.yaml',{'records':[{'judgment_id':'tool-individual-judgment-output','family':'LJ-X8000','mode':'3D','meaning':'Source identifies tool individual judgment output.','limits':None,'invalid_measurement_behavior':None,'related_signal_refs':['operations/io_signal_reference.yaml'],'source_evidence':[e3d['tool_output']],'knowledge_status':'OFFICIAL_CONTEXTUAL'}]})
 write(OUT/'measurement'/'region_model.yaml',{'canonical_roles':[{'role':'measurement_region','official_term':'UNRESOLVED_PER_TOOL','meaning':'Region passed to a specific tool; role does not imply identical GUI behavior across tools.','knowledge_status':'DERIVED'},{'role':'reference_region','official_term':'UNRESOLVED_PER_TOOL','meaning':'Reference/datum role only when a tool source explicitly defines one.','knowledge_status':'DERIVED'}]})
 write(OUT/'measurement'/'mode_comparison.yaml',{'families':[{'controller_family':'LJ-X8000','mode':'2D','tool_ids':[x['tool_id'] for x in tools if x['applicability']['mode']=='2D'],'source_evidence':[e2d['height_difference_width']]},{'controller_family':'LJ-X8000','mode':'3D','tool_ids':['cross-section-measurement'],'source_evidence':[e3d['cross_section']]}],'limitations':['No tool/settings are propagated between modes without direct evidence.']})
 write(OUT/'measurement'/'dynamic_measurement_options.yaml',{'options':[{'option_id':'same-program-position-correction','capabilities':'Position correction is documented; exact per-tool coverage remains unresolved.','limitations':['Do not assume automatic dynamic ROI behavior.'],'source_evidence':[e2d['position_correction']],'knowledge_status':'OFFICIAL_CONTEXTUAL'},{'option_id':'program-switching','capabilities':'Use existing program-switch workflow/commands for documented switching.','limitations':['Measurement setup transfer behavior requires source context.'],'source_evidence':[e3d['save']],'knowledge_status':'OFFICIAL_CONTEXTUAL'}]})
 selection=[]
 for x in tools:
  for out in x['outputs']: selection.append({'intent':out['name'].replace(' ','_'),'tool_id':x['tool_id'],'mode':x['applicability']['mode'],'knowledge_status':'DERIVED','canonical_basis':['purpose','outputs']})
 write(OUT/'measurement'/'measurement_tool_selection.yaml',{'rules':selection})
 workflows=[]
 for wid,title in [('create-new-2d-measurement','Create 2D measurement'),('configure-acquisition','Configure acquisition'),('add-measurement-tool','Add measurement tool'),('configure-regions','Configure regions'),('add-position-correction','Add position correction'),('configure-judgment','Configure judgment'),('verify-measurement','Verify measurement'),('save-program','Save program'),('switch-and-verify-program','Switch and verify program'),('two-surface-height-difference','Two-surface height difference')]:
  workflows.append({'workflow_id':wid,'title':title,'applicability':{'controller_family':'LJ-X8000','mode':'CONTEXT_REQUIRED'},'steps':['PRECHECK','CONFIGURE','TEST','VERIFY','SAVE'],'knowledge_status':'DERIVED','canonical_refs':['measurement/program_structure.yaml','measurement/measurement_tools.yaml','measurement/corrections.yaml'],'source_evidence':[e2d['height_difference_width']]})
 write(OUT/'workflows'/'measurement_program_workflows.yaml',{'workflows':workflows})
 routes=[{'intent':x,'required_context':['controller_family','mode','measurement_goal'],'targets':['measurement/measurement_tool_selection.yaml','measurement/measurement_tools.yaml','workflows/measurement_program_workflows.yaml'],'raw_corpus_fallback':True} for x in ['measure_height','measure_height_difference','measure_width','measure_gap','measure_position','measure_angle','measure_radius','measure_area','correct_position','correct_tilt','select_measurement_tool','build_program','copy_program','configure_roi','configure_judgment','configure_acquisition']]
 write(OUT/'routing'/'measurement_routing.yaml',{'routes':routes})
 write(OUT/'routing'/'measurement_context_schema.yaml',{'slots':[{'name':x,'required_for_intent':[],'optional':True,'infer_if_known':True} for x in ['controller_family','head_model','mode','measurement_goal','target_geometry','expected_range','required_accuracy','trigger_method','moving_or_static','position_variation','program_number']]})
 for name,records,key,aliases in [('measurement_tool_index.json',tools,'tool_id',['official_name']),('correction_index.json',corrections,'correction_id',['official_name']),('acquisition_index.json',acquire,'setting_id',['setting']),('program_operation_index.json',operations,'operation_id',['operation']),('measurement_workflow_index.json',workflows,'workflow_id',['title'])]:
  write(OUT/'routing'/name,{'index':[{key:r[key],'aliases':[r[a] for a in aliases if r.get(a)]} for r in records]})
 write(OUT/'measurement'/'MEASUREMENT_TOOL_REFERENCE.md','# Measurement tool reference\n\nDerived view. Use canonical YAML and evidence before applying settings.\n\n'+'\n'.join(f"- **{x['official_name']}** — {x['applicability']['mode']}; outputs: {', '.join(o['name'] for o in x['outputs'])}." for x in tools)+'\n')
 write(OUT/'workflows'/'PROGRAM_ENGINEERING_GUIDE.md','# Program engineering guide\n\nDerived workflow routing only: precheck, configure, test, verify, save. Confirm controller family and mode before changing a program.\n')
 write(OUT/'diagnostics'/'measurement_troubleshooting_playbooks.yaml',{'playbooks':[{'playbook_id':x,'applicability':{'controller_family':'LJ-X8000','mode':'CONTEXT_REQUIRED'},'documented_checks':[],'derived_engineering_guidance':['Confirm family/mode, applicable tool, configured region and source-backed acquisition path before changing settings.'],'canonical_refs':['measurement/measurement_tools.yaml','measurement/region_model.yaml'],'knowledge_status':'DERIVED'} for x in ['no-valid-measurement','unstable-measurement','wrong-feature-detected','roi-misses-target','position-shift','measurement-out-of-range','judgment-unexpected']]})
 write(OUT/'routing'/'measurement_skill_scenarios.yaml',{'scenarios':[{'question':x,'route':'measurement_routing.yaml','contains_answer':False} for x in ['Jak změřím rozdíl výšek dvou ploch?','Jak změřím šířku mezery?','Jak nastavit ROI?','Objekt se mezi kusy posouvá.','Jakou correction použít?','Jak vytvořím nový program?','Jak nastavím OK/NOK limit?','Jak měřit úhel?']]})
 print(json.dumps({'tools':len(tools),'corrections':len(corrections),'workflows':len(workflows),'direct_evidence':len(e2d)+len(e3d)}))
if __name__=='__main__': main()







