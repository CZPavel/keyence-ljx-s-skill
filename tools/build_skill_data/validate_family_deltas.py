import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'skill_data'
def main():
 e=[];w=[];d=json.loads((O/'hardware/family_delta.yaml').read_text(encoding='utf8'));allowed={'SAME','DIFFERENT','NOT_SUPPORTED','NOT_VERIFIED','FAMILY_SPECIFIC','REUSABLE_WITH_VARIANT'}
 for group in ['command_deltas','signal_deltas','trigger_deltas','communication_deltas','program_deltas','workflow_deltas']:
  for x in d[group]:
   for fam,c in x['comparison'].items():
    if c['relation'] not in allowed:e.append(x['record_id']+': relation')
    if c['relation'] in {'SAME','DIFFERENT','NOT_SUPPORTED','FAMILY_SPECIFIC','REUSABLE_WITH_VARIANT'} and not c['evidence']:e.append(x['record_id']+': evidence')
    if c['relation']=='NOT_VERIFIED' and c.get('differences'):e.append(x['record_id']+': unverified difference')
 idx=json.loads((O/'routing/family_delta_index.json').read_text(encoding='utf8'))
 ids={x['record_id'] for g in ['command_deltas','signal_deltas','trigger_deltas','communication_deltas','program_deltas','workflow_deltas'] for x in d[g]}
 if {x['record_id'] for x in idx}!=ids:e.append('delta index mismatch')
 route=json.loads((O/'routing/routing_map.yaml').read_text(encoding='utf8'))
 if not route.get('family_applicability_policy',{}).get('require_controller_family_before_controller_dependent_workflow'):e.append('missing family routing policy')
 (O/'validation_family_deltas.md').write_text(f'# Family delta validation\n\nErrors: {len(e)}. Warnings: {len(w)}.\n',encoding='utf8');print(json.dumps({'errors':e,'warnings':w,'records':len(ids)}))
 if e:raise SystemExit(1)
if __name__=='__main__':main()
