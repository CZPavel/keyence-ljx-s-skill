import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]; S=R/'benchmarks/skill_v1/scenarios.json'
def main():
 scenarios=json.loads(S.read_text(encoding='utf-8-sig'))['scenarios']; passed=[];failed=[];unresolved=[]
 for s in scenarios:
  cmd=[sys.executable,str(R/'tools/skill_lookup.py'),s['lookup_kind'],s['lookup_query'],'--json']
  if s.get('controller'): cmd += ['--controller',s['controller']]
  if s.get('mode'): cmd += ['--mode',s['mode']]
  try: out=json.loads(subprocess.check_output(cmd,text=True,encoding='utf-8-sig'))
  except Exception as e: failed.append({'id':s['id'],'reason':str(e)});continue
  ok=bool(out['matches'])
  if s.get('expect_unresolved'):
   (unresolved if not ok else failed).append({'id':s['id'],'reason':'recognized unresolved' if not ok else 'unexpected canonical cross-family match'})
  elif ok: passed.append(s['id'])
  else: failed.append({'id':s['id'],'reason':'route did not resolve'})
 report={'total':len(scenarios),'passed':len(passed),'failed':failed,'unresolved_by_design':unresolved}
 (S.parent/'benchmark_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8-sig')
 print(json.dumps(report,ensure_ascii=False))
 if failed: raise SystemExit(1)
if __name__=='__main__':main()

