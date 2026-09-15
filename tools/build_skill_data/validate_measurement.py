"""Validate the conservative measurement/program knowledge layer."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=R/'skill_data'; C=R/'corpus'/'keyence_skill_v1'/'skill_ready'/'retrieval_chunks.jsonl'
def load(p): return json.loads(p.read_text(encoding='utf8'))
def main():
 errors=[]; warnings=[]
 chunk_ids={json.loads(x)['chunk_id'] for x in C.open(encoding='utf8')}
 tools=load(O/'measurement'/'measurement_tools.yaml')['tools']; corrections=load(O/'measurement'/'corrections.yaml')['records']
 if len({x['tool_id'] for x in tools})!=len(tools): errors.append('duplicate tool IDs')
 corr_ids={x['correction_id'] for x in corrections}
 for tool in tools:
  a=tool.get('applicability',{})
  if a.get('controller_family')!='LJ-X8000' or a.get('mode') not in {'2D','3D'}: errors.append('invalid tool family/mode '+tool.get('tool_id','?'))
  for ref in tool.get('direct_evidence',[]):
   if ref.get('chunk_id') not in chunk_ids: errors.append('dangling tool evidence '+tool['tool_id'])
  for out in tool.get('outputs',[]):
   if not out.get('source_evidence'): errors.append('output lacks evidence '+tool['tool_id'])
  for ref in tool.get('related_corrections',[]):
   if ref not in corr_ids: errors.append('unknown correction '+ref)
 for record in corrections:
  if record.get('mode') not in {'2D','3D'}: errors.append('invalid correction mode')
  for ref in record.get('source_evidence',[]):
   if ref.get('chunk_id') not in chunk_ids: errors.append('dangling correction evidence')
 operations=load(O/'operations'/'program_operations.yaml')['operations']
 for operation in operations:
  if operation.get('family')!='LJ-X8000' or not operation.get('mode'):
   errors.append('invalid program operation applicability')
  for ref in operation.get('source_evidence',[]):
   if ref.get('chunk_id') not in chunk_ids: errors.append('dangling program operation evidence')
 workflows=load(O/'workflows'/'measurement_program_workflows.yaml')['workflows']
 if not workflows: errors.append('no measurement workflows')
 for route in load(O/'routing'/'measurement_routing.yaml')['routes']:
  if not route.get('required_context') or not route.get('targets'): errors.append('incomplete measurement route')
 for path in [O/'measurement'/'measurement_tool_selection.yaml',O/'measurement'/'region_model.yaml',O/'measurement'/'mode_comparison.yaml',O/'measurement'/'dynamic_measurement_options.yaml',O/'measurement'/'calculations.yaml',O/'measurement'/'judgment.yaml']:
  if not path.exists(): errors.append('missing '+path.name)
 (O/'validation_measurement.md').write_text(f'# Measurement validation\n\nErrors: {len(errors)}. Warnings: {len(warnings)}. Tools: {len(tools)}. Corrections: {len(corrections)}. Workflows: {len(workflows)}.\n',encoding='utf8')
 print(json.dumps({'errors':errors,'warnings':warnings,'tools':len(tools),'corrections':len(corrections),'workflows':len(workflows)}))
 if errors: raise SystemExit(1)
if __name__=='__main__': main()

