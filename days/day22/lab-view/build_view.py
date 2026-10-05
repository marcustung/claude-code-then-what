# -*- coding: utf-8 -*-
"""Day 22：把 Day 20／21 的真實查核結果整理成團隊工作視圖。

輸入（只讀）：
  ../day20-handoff-pack/runs/<D20>/summary.json 原始 4 次（外層 gate 結果）
  ../day21-skill-eval/runs/<batch>/*/row.json 27 次
  ../day20-handoff-pack/findings/README.md     F1–F5 維護發現
規則：
  - 同一事件（案例＋資料）的多次結果合併成一件工作；狀態取外層 gate，不採模型自述。
  - unknown 一律成為待查工作，不變綠燈、不自動結案。
  - 格式讀不到（RETURN_FOR_EVIDENCE 且條件不是 v2）不算業務工作，歸為流程問題一件。
  - 人工投入沿用 Day 5 定義（準備、查核、返工、維護）；沒有紀錄就寫「未知」，不補零。
輸出：work-view.md、items.json
"""
from pathlib import Path
import json, re, collections

root = Path(__file__).resolve().parent
EX = root.parent

def lab(src, pub):
    """原始 repo 在 examples/<src>，公開 repo 在 days/<pub>；兩種結構都找。"""
    for p in (EX / src, EX.parent / pub):
        if p.exists():
            return p
    raise SystemExit(f'找不到 {src}（公開 repo 裡是 days/{pub}）')


# 固定輸入：Day 20 原始 4 次（10-03）＋ Day 21 Eval 27 次 = 31 筆。
# day20 之後又加了 marketplace 等情境，用 glob 會讀成 37 筆，跟文章對不上（2026-10-06 修正）
D20 = ('complete-20261003-043626', 'missing-20261003-043750', 'no-bash-20261003-043826', 'skill-only-20261003-043901')
DAY20 = lab('day20-handoff-pack', 'day20/lab-handoff')
DAY21 = lab('day21-skill-eval', 'day21/lab-eval') / 'runs' / '20261003-044716'

EVENT = {  # 案例 → 事件說明、接收端事實、下一步、誰接、在等什麼
    'complete': ('通知 7e746d20：資料完整', '兩端紀錄相符', '核對後決定是否結案', '服務 Owner', '等 Owner 核對'),
    'missing-receipts': ('通知 7e746d20：缺接收端收據', '只有發送端紀錄', '向接收端補查收據', '查核者', '等接收端資料'),
    'decoy-receipt': ('通知 7e746d20：收據 ID 不符', '收據屬於另一則通知 3f1c9a7e', '查明 3f1c9a7e 來源，補查本通知收據', '查核者', '等接收端資料'),
}
OK = ('READY_FOR_REVIEW', 'NEEDS_FOLLOWUP')

results = []
for p in sorted(DAY20 / 'runs' / r / 'summary.json' for r in D20):
    s = json.loads(p.read_text(encoding='utf-8'))
    try:
        state = json.loads(s['outer_gate'].get('stdout') or '{}').get('state')
    except Exception:
        state = None
    state = state or 'NOT_RUNNABLE'
    results.append({'src': f'day20/{p.parent.name}', 'case': s['case'], 'cond': 'v2', 'state': state,
                    'seconds': s.get('seconds'), 'cost': s.get('cost_usd'), 'scenario': s['scenario']})
for p in sorted(DAY21.glob('*/row.json')):
    r = json.loads(p.read_text(encoding='utf-8'))
    results.append({'src': f'day21/{p.parent.name}', 'case': r['case'], 'cond': r['cond'], 'state': r['outer_gate'],
                    'seconds': r['seconds'], 'cost': r['cost_usd'], 'scenario': 'eval'})

items = []
by_event = collections.defaultdict(list)
fmt_fail, not_runnable = [], []
for r in results:
    if r['state'] in OK:
        by_event[r['case']].append(r)
    elif r['state'] == 'NOT_RUNNABLE' or r['scenario'] == 'skill-only':
        not_runnable.append(r)
    else:
        fmt_fail.append(r)

for case, rs in by_event.items():
    title, fact, nxt, owner, wait = EVENT[case]
    states = collections.Counter(r['state'] for r in rs)
    items.append({'kind': '業務', 'title': title, 'state': states.most_common(1)[0][0], 'fact': fact,
                  'next': nxt, 'owner': owner, 'waiting': wait, 'results_merged': len(rs),
                  'unknown_is_work': states.most_common(1)[0][0] == 'NEEDS_FOLLOWUP'})
if fmt_fail:
    conds = collections.Counter(r['cond'] for r in fmt_fail)
    items.append({'kind': '流程', 'title': '未用 v2 方法包的結果無法被檢查器驗證', 'state': 'RETURN_FOR_EVIDENCE',
                  'fact': f"條件分布 {dict(conds)}；判斷本身正確，引用是自由文字", 'next': '日常查核一律用 v2.0.2；實驗對照組保留不處理',
                  'owner': 'Skill 維護者', 'waiting': '無', 'results_merged': len(fmt_fail), 'unknown_is_work': False})
if not_runnable:
    items.append({'kind': '流程', 'title': '只交 SKILL.md 時固定檢查無法執行', 'state': 'NOT_RUNNABLE',
                  'fact': '腳本不存在，Claude 標待查、未自行補寫', 'next': 'INSTALL.md 第一步改為先跑 selftest',
                  'owner': 'Skill 維護者', 'waiting': '無', 'results_merged': len(not_runnable), 'unknown_is_work': False})
findings = re.findall(r'^## (F\d) (.+)$', (DAY20 / 'findings' / 'README.md').read_text(encoding='utf-8'), re.M)
for fid, t in findings:
    items.append({'kind': '維護', 'title': f'{fid} {t}', 'state': '已修（見 CHANGELOG）' if fid in ('F1', 'F2', 'F3') else '已記錄',
                  'fact': 'Day 20 交接實跑發現', 'next': '下次改版重跑 Day 21 的 27 次 Eval', 'owner': 'Skill 維護者',
                  'waiting': '無', 'results_merged': 0, 'unknown_is_work': False})

machine_sec = round(sum(r['seconds'] or 0 for r in results), 1)
cost = round(sum(r['cost'] or 0 for r in results), 3)
open_biz = [i for i in items if i['kind'] == '業務']
summary = {'results': len(results), 'items': len(items), 'business_items': len(open_biz),
           'business_need_human_today': sum(1 for i in open_biz if i['owner'] == '服務 Owner'),
           'unknown_as_work': sum(i['unknown_is_work'] for i in items),
           'machine_seconds_known': machine_sec, 'model_cost_usd': cost,
           'human_minutes': {'準備': '未知', '查核': '未知', '返工': '未知', '維護': '未知'},
           'day21_batch': DAY21.name}
(root / 'items.json').write_text(json.dumps({'summary': summary, 'items': items, 'results': results},
                                            ensure_ascii=False, indent=2), encoding='utf-8')

L = [f"# 今日工作視圖（{len(results)} 筆查核結果 → {len(items)} 件工作）", '',
     '| 類型 | 工作 | 狀態 | 已知事實 | 下一步 | 誰接 | 在等什麼 | 合併幾筆結果 |', '|---|---|---|---|---|---|---|---|']
for i in items:
    L.append(f"| {i['kind']} | {i['title']} | {i['state']} | {i['fact']} | {i['next']} | {i['owner']} | {i['waiting']} | {i['results_merged']} |")
L += ['', '## 投入', '', f"- 機器：{len(results)} 次執行共 {machine_sec} 秒（其中 1 次秒數未記錄），模型費用 US${cost}",
      '- 人工：準備、查核、返工、維護 **皆未知**（本系列未記錄作者工時，不補零）', '',
      f"資料：Day 20 runs、Day 21 batch {DAY21.name}；狀態一律取外層 gate。"]
(root / 'work-view.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('\n'.join(L))
print(json.dumps(summary, ensure_ascii=False))
