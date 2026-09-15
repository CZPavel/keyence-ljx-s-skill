import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert (root/'skill/keyence-ljx/SKILL.md').read_text(encoding='utf-8-sig').lstrip().startswith('---')
for p in [root/'skill_data/operations/command_reference.yaml',root/'skill_data/routing/command_index.json']:
 json.loads(p.read_text(encoding='utf8'))
print('public skill/command structure: ok')
