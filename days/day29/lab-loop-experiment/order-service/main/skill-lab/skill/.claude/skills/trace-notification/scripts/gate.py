"""Day 20 接頭：把 Day 17 的資料接到 Day 19 的 check_result.py（檢查器原封不動）。

用法：python .claude/skills/trace-notification/scripts/gate.py <案例目錄> [結果檔，預設 out/result.json]
每次都重跑 collect.py 產生來源清單，不採用模型留下的 evidence.json。
預期的 notification_id 取自工具收集的發送紀錄，不取自模型回答。
退出碼：0 READY_FOR_REVIEW／NEEDS_FOLLOWUP；1 RETURN_FOR_EVIDENCE；2 輸入錯誤。
"""
from pathlib import Path
import hashlib, json, sys

here = Path(__file__).resolve().parent
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
sys.path.insert(0, str(here))
import collect as C
import check_result as K


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


def main(case, result_path=None):
    case = Path(case)
    result_path = Path(result_path) if result_path else case / 'out' / 'result.json'
    out_dir = case / 'out'; out_dir.mkdir(exist_ok=True)
    ev = C.collect(case)
    (out_dir / 'evidence.tool.json').write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding='utf-8')
    task_src = json.loads((case / 'task.json').read_text(encoding='utf-8-sig'))
    ids = ev['notification_ids']
    report = {'case': case.name, 'result_file': str(result_path.name), 'result_sha256': sha(result_path),
              'task_sha256': sha(case / 'task.json'), 'checker_sha256': sha(here / 'check_result.py'),
              'notification_ids_from_tool': ids}
    if len(ids) != 1:
        report.update(state='INPUT_ERROR', errors=['NOTIFICATION_ID_NOT_UNIQUE'], approved=False, action_executed=False)
        code = 2
    elif not result_path.exists():
        report.update(state='INPUT_ERROR', errors=['RESULT_FILE_MISSING'], approved=False, action_executed=False)
        code = 2
    else:
        task = {'order_id': task_src['order_id'], 'notification_id': ids[0], 'version': task_src['version']}
        try:
            result = json.loads(result_path.read_text(encoding='utf-8-sig'))
            report.update(K.evaluate(result, task, ev))
        except (ValueError, KeyError, TypeError) as exc:
            report.update(state='INPUT_ERROR', errors=[type(exc).__name__], approved=False, action_executed=False)
        code = 0 if report.get('contract_passed') else (2 if report['state'] == 'INPUT_ERROR' else 1)
    (out_dir / 'gate.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
