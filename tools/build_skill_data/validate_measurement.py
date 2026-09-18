"""Validate measurement/program knowledge in public or local-source mode."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=R/'skill_data'; C=R/'corpus'/'keyence_skill_v1'/'skill_ready'/'retrieval_chunks.jsonl'
def load(p): return json.loads(p.read_text(encoding='utf8'))
def refs_valid(refs, blocks, source_docs, chunks, errors, label):
 for ref in refs:
  if not ref.get('document_id') or not ref.get('source_sha256'): errors.append('invalid evidence metadata '+label)
  elif ref['document_id'] not in source_docs: errors.append('unknown public source document '+label)
  if ref.get('block_id') and ref['block_id'] not in blocks: errors.append('unknown public evidence block '+label)
  if chunks is not None:
   chunk=chunks.get(ref.get('chunk_id'))
   if chunk is None: errors.append('dangling source chunk '+label)
   elif ref.get('evidence_excerpt_hash') and ref['evidence_excerpt_hash']!=chunk.get('text_sha256'): errors.append('source excerpt hash mismatch '+label)
def main():
 p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(); g.add_argument('--public',action='store_true'); g.add_argument('--source',action='store_true'); a=p.parse_args(); mode='source' if a.source else 'public'
 errors=[]; warnings=[]; chunks=None
 if mode=='source':
  if not C.exists(): raise SystemExit('Local source corpus is required for --source validation.')
  chunks={x['chunk_id']:x for x in (json.loads(line) for line in C.open(encoding='utf8'))}
 blocks={load(x)['block_id'] for x in (O/'evidence/manual_source_blocks').glob('*.json')}
 source_docs={x['document_id'] for x in load(R/'sources/source_registry.yaml').get('sources',[])}
 tools=load(O/'measurement/measurement_tools.yaml')['tools']; corrections=load(O/'measurement/corrections.yaml')['records']; preprocessing=load(O/'measurement/preprocessing.yaml')['records']; acquisition=load(O/'measurement/acquisition.yaml')['settings']; contextual=load(O/'measurement/contextual_3d_guidance.yaml')['records']; dataflows=load(O/'communication/data_flow_reference.yaml')['flows']
 if len({x['tool_id'] for x in tools})!=len(tools): errors.append('duplicate tool IDs')
 corr_ids={x['correction_id'] for x in corrections}
 for tool in tools:
  a=tool.get('applicability',{})
  if a.get('controller_family')!='LJ-X8000' or a.get('mode') not in {'2D','3D'}: errors.append('invalid tool family/mode '+tool.get('tool_id','?'))
  refs_valid(tool.get('direct_evidence',[]),blocks,source_docs,chunks,errors,tool['tool_id'])
  for out in tool.get('outputs',[]):
   if not out.get('source_evidence'): errors.append('output lacks evidence '+tool['tool_id'])
   refs_valid(out.get('source_evidence',[]),blocks,source_docs,chunks,errors,tool['tool_id'])
  for ref in tool.get('related_corrections',[]):
   if ref not in corr_ids: errors.append('unknown correction '+ref)
 for record in corrections:
  if record.get('mode') not in {'2D','3D'}: errors.append('invalid correction mode')
  refs_valid(record.get('source_evidence',[]),blocks,source_docs,chunks,errors,record['correction_id'])
 if len({x.get('setting_id') for x in preprocessing})!=len(preprocessing): errors.append('duplicate preprocessing setting IDs')
 for record in preprocessing:
  a=record.get('applicability',{})
  if a.get('controller_family')!='LJ-X8000' or a.get('mode')!='3D': errors.append('invalid preprocessing family/mode '+record.get('setting_id','?'))
  if not record.get('parameter_effects') or not record.get('symptom_relations'): errors.append('incomplete preprocessing guidance '+record.get('setting_id','?'))
  provenance=record.get('legacy_guidance_provenance')
  if provenance and (not (provenance.get('resource_key') or provenance.get('resource_namespace')) or not provenance.get('source_sha256')): errors.append('invalid preprocessing legacy provenance '+record.get('setting_id','?'))
  refs_valid(record.get('source_evidence',[]),blocks,source_docs,chunks,errors,record['setting_id'])
 if len({x.get('guidance_id') for x in contextual})!=len(contextual): errors.append('duplicate contextual guidance IDs')
 for record in contextual:
  if record.get('contextual_scope')!='FAMILY_NOT_ESTABLISHED' or record.get('knowledge_status')!='OFFICIAL_CONTEXTUAL': errors.append('invalid contextual guidance scope '+record.get('guidance_id','?'))
  provenance=record.get('legacy_guidance_provenance',{})
  if not provenance.get('resource_namespace') or not provenance.get('source_sha256'): errors.append('missing contextual guidance provenance '+record.get('guidance_id','?'))
 if len({x.get('setting_id') for x in acquisition})!=len(acquisition): errors.append('duplicate acquisition setting IDs')
 for record in acquisition:
  if record.get('family')!='LJ-X8000' or record.get('mode') not in {'2D_OR_3D_CONTEXT_REQUIRED','3D'}: errors.append('invalid acquisition family/mode '+record.get('setting_id','?'))
  refs_valid(record.get('source_evidence',[]),blocks,source_docs,chunks,errors,record['setting_id'])
 for flow in dataflows:
  refs_valid(flow.get('source_evidence',[]),blocks,source_docs,chunks,errors,flow.get('flow_id','?'))
 operations=load(O/'operations/program_operations.yaml')['operations']
 for operation in operations:
  if operation.get('family')!='LJ-X8000' or not operation.get('mode'): errors.append('invalid program operation applicability')
  refs_valid(operation.get('source_evidence',[]),blocks,source_docs,chunks,errors,operation['operation_id'])
 workflows=load(O/'workflows/measurement_program_workflows.yaml')['workflows']
 if not workflows: errors.append('no measurement workflows')
 for route in load(O/'routing/measurement_routing.yaml')['routes']:
  if not route.get('required_context') or not route.get('targets'): errors.append('incomplete measurement route')
 for path in [O/'measurement/measurement_tool_selection.yaml',O/'measurement/region_model.yaml',O/'measurement/mode_comparison.yaml',O/'measurement/dynamic_measurement_options.yaml',O/'measurement/calculations.yaml',O/'measurement/judgment.yaml',O/'measurement/preprocessing.yaml']:
  if not path.exists(): errors.append('missing '+path.name)
 print(json.dumps({'mode':mode,'errors':errors,'warnings':warnings,'tools':len(tools),'corrections':len(corrections),'acquisition':len(acquisition),'preprocessing':len(preprocessing),'contextual_guidance':len(contextual),'dataflows':len(dataflows),'workflows':len(workflows)}))
 if errors: raise SystemExit(1)
if __name__=='__main__': main()
