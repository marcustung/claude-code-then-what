"""Copy the publishable part of the third-party benchmark runs into this folder.
Source: ../order-cancel-lifecycle/evidence/bench3p (local only).
- RCAEval (MIT): per-run result.json (answer, truth, solved, seconds, cost, turns) and final.md (Claude's answer), plus selection.json.
- o11y-bench (AGPL-3.0, run locally, not redistributed): only our per-run result.json (score, seconds, cost, turns) and selection.json.
  Task text, rubric (rewards.json), setup and raw logs are NOT copied; get tasks from the official repo.
Then writes SUMMARY.md from the copied files."""
from pathlib import Path
import json, shutil, statistics as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent/'order-cancel-lifecycle/evidence/bench3p'

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)

def main():
    for d in ('rcaeval', 'o11y'):
        if (ROOT/d).exists(): shutil.rmtree(ROOT/d)
    sel = json.loads((SRC/'rcaeval/base/selection.json').read_text(encoding='utf-8'))
    (ROOT/'rcaeval').mkdir(parents=True)
    # case_dir: keep only the dataset-relative part (RE3-OB/adservice_f3/2), drop the local data root.
    for c in sel['cases']:
        c['case_dir'] = '/'.join(Path(c['case_dir']).parts[-3:])
    sel = json.dumps(sel, ensure_ascii=False, indent=1)
    (ROOT/'rcaeval/selection.json').write_text(sel, encoding='utf-8')
    rc = []
    for run in sorted((SRC/'rcaeval/base').glob('R*')):
        if (run/'final.md').exists(): copy(run/'final.md', ROOT/'rcaeval'/run.name/'final.md')
        r = json.loads((run/'result.json').read_text(encoding='utf-8'))
        # outside_reads holds raw commands (scratch-file heredocs with local paths); publish only the count.
        r['outside_reads'] = len(r.get('outside_reads') or [])
        (ROOT/'rcaeval'/run.name/'result.json').write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
        rc.append(r)
    groups = {'base': SRC/'o11y/base', 'mod-v02': SRC/'o11y-mod/mod-v02', 'stoponly': SRC/'o11y-mod/stoponly'}
    o = {}
    for g, d in groups.items():
        if (d/'selection.json').exists(): copy(d/'selection.json', ROOT/'o11y'/g/'selection.json')
        rows = []
        for run in sorted(p for p in d.iterdir() if p.is_dir()):
            if (run/'result.json').exists():
                copy(run/'result.json', ROOT/'o11y'/g/run.name/'result.json')
                rows.append(json.loads((run/'result.json').read_text(encoding='utf-8')))
        o[g] = rows
    copy(SRC/'O11Y-MOD-COMPARISON.md', ROOT/'O11Y-MOD-COMPARISON.md')
    L = ['# Day 26：第三方題庫成績（由 export.py 依本目錄檔案產生）', '',
         '題目不是作者出的：從 [RCAEval](https://github.com/phamquiluan/RCAEval)（MIT）與 [o11y-bench](https://github.com/grafana/o11y-bench)（AGPL-3.0）各選 20 題，每題讓 Claude Code（sonnet）跑兩次。',
         '本目錄只放成績：RCAEval 每次的 `result.json`（答案、正解、秒數、費用、回合）與 `final.md`（Claude 的回答）；o11y-bench 每次的 `result.json`（官方判分）。',
         'o11y-bench 的題目、評分準則與執行紀錄不在這裡（授權與個人資訊考量），題目請到官方 repo 取得。`selection.json` 是選題清單。', '',
         '## RCAEval（20 題 × 2 次，sonnet；第一名猜中根因服務才算對）', '',
         '| 子類 | 答對 | 次數 |', '|---|---:|---:|']
    by = {}
    for r in rc: by.setdefault(r['suite'], []).append(r['solved'])
    for k in sorted(by): L.append(f'| {k} | {sum(by[k])} | {len(by[k])} |')
    L += [f'| 合計 | {sum(r["solved"] for r in rc)} | {len(rc)} |', '',
          f'前三名有正解：{sum(r["in_top3"] for r in rc)}／{len(rc)}；平均每次 {st.mean(r["seconds"] for r in rc):.0f} 秒、US${st.mean(r["cost_usd"] for r in rc):.3f}。', '',
          '## o11y-bench（20 題 × 2 次，sonnet；官方判分，分數是評分平均，滿分 1，不是答對率）', '',
          '| 組別 | 全部 | 調查題 | 次數 |', '|---|---:|---:|---:|']
    for g, rows in o.items():
        inv = [r['score'] for r in rows if r['category'] == 'investigation']
        L.append(f'| {g} | {st.mean(r["score"] for r in rows):.3f} | {st.mean(inv):.3f} | {len(rows)} |')
    L += ['', '- base：一般工具流程；mod-v02：加查證清單與收工檢查；stoponly：只留收工檢查。詳見 O11Y-MOD-COMPARISON.md。',
          '- 限制：單一模型；每題兩次；o11y-bench 每次重新產生遙測資料；保留組曾看過部分失敗內容。題庫成績不是診斷正確率。']
    (ROOT/'README.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L))

if __name__ == '__main__': main()
