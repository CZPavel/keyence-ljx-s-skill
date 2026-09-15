import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'skill_data'
def main():
 e=[];w=[];cmd={x['command'] for x in json.loads((O/'operations/command_reference.yaml').read_text(encoding='utf8'))['commands']};sig={x['signal_name'] for x in json.loads((O/'operations/io_signal_reference.yaml').read_text(encoding='utf8'))['signals']};d=json.loads((O/'workflows/operational_workflows.yaml').read_text(encoding='utf8'))['workflows'];ids={x['workflow_id'] for x in d}
 for x in d:
  if x['applicability']['controllers']!=['LJ-X8000']:e.append(x['workflow_id']+': family')
  for s in x['steps']:
   for r in s['command_ref']:
    if r.split(':',1)[1] not in cmd:e.append(x['workflow_id']+': '+r)
   for r in s['signal_ref']:
    if r.split(':',1)[1] not in sig:e.append(x['workflow_id']+': '+r)
   if s['knowledge_status']=='DERIVED' and s['action_classification']=='':e.append(x['workflow_id']+': unclassified derived step')
 routes={x['intent'] for x in json.loads((O/'routing/routing_map.yaml').read_text(encoding='utf8'))['intent_families']}
 for x in json.loads((O/'routing/skill_scenarios.yaml').read_text(encoding='utf8'))['scenarios']:
  if (x['intent'] not in ids and x['intent'] not in routes) or x['route'] not in routes:e.append('scenario '+x['scenario_id'])
 report=f'# Workflow validation\n\nErrors: {len(e)}. Warnings: {len(w)}. Workflows: {len(d)}.\n';(O/'validation_workflows.md').write_text(report,encoding='utf8');print(json.dumps({'errors':e,'warnings':w,'workflows':len(d)}))
 if e:raise SystemExit(1)
if __name__=='__main__':main()

