"""Validate source-grounded LJ-X8000 and LJ-S8000 I/O/timing records."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'skill_data'
def main():
 errors=[];warnings=[]; blocks={}
 for p in (OUT/'evidence/manual_source_blocks').glob('*.json'):
  x=json.loads(p.read_text(encoding='utf8'));blocks[x['block_id']]=x
 sig=json.loads((OUT/'operations/io_signal_reference.yaml').read_text(encoding='utf8'))['signals']; names={x['signal_name'] for x in sig}
 for x in sig:
  family=x['controller_family']
  if family=='LJ-X8000' and set(x.get('not_verified_for',[]))!={'LJ-X8000A','LJ-S8000'}:errors.append(f"family applicability: {x['signal_name']}")
  elif family=='LJ-S8000' and set(x.get('not_verified_for',[]))!={'LJ-X8000','LJ-X8000A'}:errors.append(f"family applicability: {x['signal_name']}")
  elif family not in {'LJ-X8000','LJ-S8000'}:errors.append(f"unknown family: {x['signal_name']}")
  if x['knowledge_status']=='OFFICIAL_EXACT' and not x.get('direct_evidence'):errors.append(f"missing direct evidence: {x['signal_name']}")
  for e in x.get('direct_evidence',[]):
   if e.get('block_id') and e['block_id'] not in blocks:errors.append(f"dangling signal evidence: {x['signal_name']}")
   if not e.get('block_id') and not (e.get('document_id') and e.get('source_sha256') and e.get('chunk_id') and e.get('evidence_excerpt_hash')):errors.append(f"incomplete signal evidence: {x['signal_name']}")
 rel=json.loads((OUT/'operations/signal_relations.yaml').read_text(encoding='utf8'))['relations']
 for r in rel:
  if r['status']=='OFFICIAL_EXACT' and (not r.get('evidence') or r['evidence'][0].get('block_id') not in blocks):errors.append('invalid exact relation')
 for p in [OUT/'operations/trigger_methods.yaml',OUT/'operations/trigger_timing.yaml',OUT/'operations/io_terminal_reference.yaml',OUT/'routing/signal_index.json',OUT/'routing/trigger_index.json']:
  try:json.loads(p.read_text(encoding='utf8'))
  except Exception as e:errors.append(f'invalid {p.name}: {e}')
 report=f'# I/O and timing validation\n\nErrors: {len(errors)}. Warnings: {len(warnings)}. Signals: {len(sig)}. Relations: {len(rel)}.\n'
 if errors:report+='\n'+'\n'.join('- '+x for x in errors)+'\n'
 (OUT/'validation_io_timing.md').write_text(report,encoding='utf8');print(json.dumps({'errors':errors,'warnings':warnings,'signals':len(sig),'relations':len(rel)}))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
