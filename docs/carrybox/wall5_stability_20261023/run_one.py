import sys,json
from pathlib import Path
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
import run_engineering_tests as runner
D=Path(__file__).resolve().parent
original=runner.load_frontmatter
index=int(sys.argv[1])
def selected(path):
 task,body=original(path)
 task['tests']=[task['tests'][index]]
 return task,body
runner.load_frontmatter=selected
rows=runner.run(Path('agent/task/carrybox-wall5-stability-20261023.md'),Path.cwd(),3600)
(D/f'receipt_{index}.json').write_text(json.dumps({'schema_version':'robotics-engineering-test-receipts.v1','tests':rows},indent=2)+'\n')
print(json.dumps(rows),flush=True)
raise SystemExit(0 if all(r['result']=='PASS' for r in rows) else 1)
