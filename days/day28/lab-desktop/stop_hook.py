"""UserPromptSubmit hook for the Day 28 Desktop experiment (E3).
Logs every invocation; blocks only when the prompt is the d28-desktop-lab scheduled task AND a STOP file exists."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(r'C:\<AUTHOR>\d28-desktop-work')
data = json.load(sys.stdin)
prompt = data.get('prompt', '') or ''
is_task = 'scheduled-task name="d28-desktop-lab"' in prompt or 'd28-desktop-lab' in prompt
stop = (HERE / 'STOP').exists()
with open(HERE / 'hook.log', 'a', encoding='utf-8') as f:
    f.write(json.dumps({'at': datetime.now(timezone.utc).isoformat(), 'session': data.get('session_id'),
                        'is_task': is_task, 'stop': stop}) + '\n')
if is_task and stop:
    print(json.dumps({'decision': 'block', 'reason': 'STOP：連續失敗，停止派送，已交回人處理。'}))
sys.exit(0)
