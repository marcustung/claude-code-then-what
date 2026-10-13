'use strict';
/**
 * 實驗 4 的輸入：彙整實驗 1–3 的迴圈紀錄（只讀，不改任何議題）。
 *   node tools/loop-metrics.js [--since 2026-10-07] [--engine <HOME>/loopdeck]
 * 輸出：metrics/loop-metrics-<日期>.json 與 .md（指標定義只由人修改，見 governance/Stability_Goals.md）。
 *
 * 時間點全取自 workspace 的 git 紀錄（LoopDeck 每個動作一個 commit）：
 *   建立＝「create <id>」、Gate 1＝「transition <id> — review→ready」、合併＝「transition <id> — …→done」
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const WS = path.resolve(__dirname, '..');
const ENGINE = arg('--engine', '<HOME>/loopdeck');
const SINCE = arg('--since', '1970-01-01');
const issues = require(path.join(ENGINE, 'lib/workspace-issues'));
const REASONS = require(path.join(ENGINE, 'lib/approval-policy')).REJECT_REASONS;

const median = (a) => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const r2 = (x) => (x == null ? null : Math.round(x * 100) / 100);
const hours = (a, b) => (a && b ? (new Date(b) - new Date(a)) / 3600e3 : null);

// git 紀錄：每個議題的 create / gate1 / done 時間
const log = execFileSync('git', ['log', '--reverse', `--since=${SINCE}`, '--format=%cI\t%s'], { cwd: WS, encoding: 'utf8' });
const times = {};
for (const line of log.split('\n').filter(Boolean)) {
  const [at, subject] = line.split('\t');
  const m = /^LoopDeck: (\w+) (\S+)(?: — (.*))?$/.exec(subject || '');
  if (!m) continue;
  const t = (times[m[2]] ||= {});
  if (m[1] === 'create') t.created ||= at;
  if (m[1] === 'transition' && /^review→ready/.test(m[3] || '')) t.gate1 ||= at;
  if (m[1] === 'transition' && /→done/.test(m[3] || '')) t.done ||= at;
}

const all = issues.listIssues(WS).map((x) => issues.getIssue(WS, x.id));
const costOf = (id) => issues.listRuns(WS, id).reduce((sum, r) => {
  const text = fs.readFileSync(path.join(issues.issueDir(WS, id), 'runs', r.file || r), 'utf8');
  const m = /- 成本：([\d.]+)/.exec(text);
  return sum + (m ? Number(m[1]) : 0);
}, 0);

const loops = {};
for (const d of all.filter((x) => /^l-/.test(x.id))) {
  loops[d.id] = { proposals: 0, approved: 0, autoApproved: 0, rejected: 0, pending: 0, merged: 0,
    reasons: {}, riskBias: { lowRejectedForRisk: 0, highApproved: 0 }, gate1Hours: [], mergeHours: [], costUsd: costOf(d.id) };
}
for (const d of all.filter((x) => x.fields?.origin && loops[x.fields.origin])) {
  const L = loops[d.fields.origin];
  const f = d.fields, t = times[d.id] || {};
  if (t.created && t.created < SINCE) continue;
  L.proposals++;
  const risk = Number(f.risk);
  if (f.proposal_verdict === 'approved' || f.proposal_verdict === 'auto-approved') {
    L.approved++; if (f.proposal_verdict === 'auto-approved') L.autoApproved++;
    if (risk >= 7) L.riskBias.highApproved++;
  } else if (f.proposal_verdict === 'rejected') {
    L.rejected++;
    if (f.proposal_reason) L.reasons[f.proposal_reason] = (L.reasons[f.proposal_reason] || 0) + 1;
    if (f.proposal_reason === 'risk' && risk <= 3) L.riskBias.lowRejectedForRisk++;
  } else L.pending++;
  if (d.state === 'done') L.merged++;
  const g = hours(t.created, t.gate1); if (g != null) L.gate1Hours.push(g);
  const mh = hours(t.created, t.done); if (mh != null) L.mergeHours.push(mh);
  L.costUsd += costOf(d.id);
}
for (const L of Object.values(loops)) {
  const decided = L.approved + L.rejected;
  L.approvalRate = decided ? r2(L.approved / decided) : null;
  L.gate1HoursMedian = r2(median(L.gate1Hours)); L.mergeHoursMedian = r2(median(L.mergeHours));
  L.costUsd = r2(L.costUsd);
  delete L.gate1Hours; delete L.mergeHours;
}

// 人力：裁決耗時（引擎 runs/decision-times.jsonl，只取本 workspace）
const dtPath = path.join(ENGINE, 'runs', 'decision-times.jsonl');
const dts = fs.existsSync(dtPath) ? fs.readFileSync(dtPath, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l))
  .filter((x) => path.resolve(x.workspace) === WS && x.at.slice(0, 10) >= SINCE) : [];
const perDay = {};
for (const x of dts) perDay[x.at.slice(0, 10)] = (perDay[x.at.slice(0, 10)] || 0) + x.decision_ms / 60000;
const human = {
  decisions: dts.length,
  minutesPerDay: Object.fromEntries(Object.entries(perDay).map(([k, v]) => [k, r2(v)])),
  minutesPerDayMedian: r2(median(Object.values(perDay))),
  under30sRatio: dts.length ? r2(dts.filter((x) => x.decision_ms < 30000).length / dts.length) : null, // 橡皮圖章警訊
};

const today = new Date().toISOString().slice(0, 10);
const out = { generatedAt: new Date().toISOString(), since: SINCE, loops, human, reasonLabels: REASONS };
fs.mkdirSync(path.join(WS, 'metrics'), { recursive: true });
fs.writeFileSync(path.join(WS, 'metrics', `loop-metrics-${today}.json`), JSON.stringify(out, null, 2) + '\n');
const md = [`# 迴圈紀錄彙整 ${today}（since ${SINCE}）`, '',
  '| 迴路 | 提案 | 核准 | 退回 | 待審 | 已合併 | 核准率 | Gate1 中位小時 | 合併中位小時 | 成本 US$ | 退回理由 |', '|---|---|---|---|---|---|---|---|---|---|---|',
  ...Object.entries(loops).map(([id, L]) => `| ${id} | ${L.proposals} | ${L.approved} | ${L.rejected} | ${L.pending} | ${L.merged} | ${L.approvalRate ?? '—'} | ${L.gate1HoursMedian ?? '—'} | ${L.mergeHoursMedian ?? '—'} | ${L.costUsd} | ${Object.entries(L.reasons).map(([k, v]) => `${REASONS[k] || k} ${v}`).join('、') || '—'} |`),
  '', `人力：裁決 ${human.decisions} 次，每日分鐘中位數 ${human.minutesPerDayMedian ?? '—'}，30 秒內核准比例 ${human.under30sRatio ?? '—'}`, ''].join('\n');
fs.writeFileSync(path.join(WS, 'metrics', `loop-metrics-${today}.md`), md);
console.log(md);
