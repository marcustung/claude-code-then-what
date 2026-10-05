import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { HookEvent, Item, Result, Snapshot } from '../types'

// Day 22：hook 負責擋，這個看板只負責讓人看見每件工作做到哪一步、卡在哪裡。
// 看板不自己判斷：步驟狀態直接讀查核結果（results/NN.json），誰接讀工作清單，退回讀 hook 紀錄。
const PANE = 'work-view'
const EMPTY: Snapshot = { source: '', items: [], blocks: [], results: {}, checkedAt: 0 }
const snapshot = atom({ plugin: 'work-view', key: 'snapshot' } as const, EMPTY)

// 工作清單的欄位名稱每次不一定一樣（owner／誰接、waiting_for／waiting_on…），取第一個有的
const pick = (it: Record<string, unknown>, keys: string[]): unknown => {
  for (const k of Object.keys(it)) {
    if (keys.some(w => k.toLowerCase().includes(w))) return it[k]
  }
  return ''
}

const load = async ($: any): Promise<Snapshot> => {
  // 先找目前工作目錄剛跑完的結果，找不到就讀練習包裡的 demo 資料
  const cwd: string = await $.session.cwd()
  for (const dir of [cwd, `${$.plugin.root}/../demo`]) {
    if (!(await $.fs.exists(`${dir}/out/worklist.json`))) continue
    try {
      const raw = JSON.parse(String(await $.fs.read(`${dir}/out/worklist.json`)).replace(/^﻿/, ''))
      const items: Item[] = (raw.items ?? []).map((it: Record<string, unknown>) => {
        const ids = pick(it, ['merge', '合併'])
        return {
          title: String(pick(it, ['title', '標題']) ?? ''),
          owner: String(pick(it, ['owner', '誰接']) ?? ''),
          waiting: String(pick(it, ['wait', '在等']) ?? ''),
          today: String(pick(it, ['today', '今天']) ?? ''),
          next: String(pick(it, ['next', '下一步']) ?? ''),
          ids: Array.isArray(ids) ? ids.map(x => String(x).padStart(2, '0')) : [],
        }
      })
      const results: Record<string, Result> = {}
      for (const id of new Set(items.flatMap(it => it.ids))) {
        const path = `${dir}/results/${id}.json`
        if (!(await $.fs.exists(path))) continue
        const r = JSON.parse(String(await $.fs.read(path)))
        results[id] = { sender: r.result?.sender_status ?? '沒有結果', receiver: r.result?.receiver_status ?? '沒有結果', gate: r.gate_state ?? '' }
      }
      let blocks: HookEvent[] = []
      if (await $.fs.exists(`${dir}/out/hook-log.jsonl`)) {
        blocks = String(await $.fs.read(`${dir}/out/hook-log.jsonl`)).split('\n').filter(Boolean).map(l => JSON.parse(l))
      }
      return { source: dir, items, blocks, results, checkedAt: await $.clock.now() }
    } catch (err) {
      return { ...EMPTY, source: dir, error: String(err), checkedAt: await $.clock.now() }
    }
  }
  return { ...EMPTY, error: '找不到 out/worklist.json', checkedAt: await $.clock.now() }
}

// 只做計數與翻譯，不判斷對錯
const ZH: Record<string, string> = {
  confirmed: '已確認', unknown: '還不能確定', READY_FOR_REVIEW: '可交人確認',
  NEEDS_FOLLOWUP: '還要再查', RETURN_FOR_EVIDENCE: '被退回（寫法不合）',
}
const tally = (values: string[]) => {
  const counts: Record<string, number> = {}
  for (const v of values) counts[v] = (counts[v] ?? 0) + 1
  return Object.entries(counts).map(([v, n]) => `${ZH[v] ?? v} ${n}`).join('、') || '—'
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'work-view', description: '打開 Day 22 工作看板：每件事做到哪一步、卡在哪裡、誰該接' })
    await update($, snapshot, () => EMPTY)
    $.clock.every(3000, async () => { const latest = await load($); await update($, snapshot, () => latest) })
    return next(e)
  })

  on('command.run', { command: 'work-view' }, async $ => {
    const fresh = await load($)
    await update($, snapshot, () => fresh)
    await $.ui.open({ id: PANE, title: '今天的工作看板' })
    return { text: '工作看板已打開。' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const s = await read($, snapshot)
    if (s.error) return <Text color="yellow">{s.error}</Text>
    if (!s.items.length) return <Text dimColor>讀取中…</Text>

    const blocked = s.blocks.filter(b => b.action === 'block')
    const hit = new Set(blocked.flatMap(b => b.items ?? []).map(t => t.slice(0, 20)))
    const res = (it: Item) => it.ids.map(id => s.results[id]).filter(Boolean)

    return (
      <Box flexDirection="column">
        <Text bold>hook 擋過 {blocked.length} 次{blocked.length ? '，已退回重排' : ''}</Text>
        {blocked.map(b => <Text color="red">  退回：{(b.items ?? []).join('、').slice(0, 80)}</Text>)}
        <Box marginTop={1}><Text bold>今天的工作（{s.items.length} 件）</Text></Box>
        {s.items.map(it => (
          <Box flexDirection="column" marginTop={1}>
            <Text bold color={hit.has(it.title.slice(0, 20)) ? 'red' : undefined}>
              {it.title.slice(0, 42)}{hit.has(it.title.slice(0, 20)) ? '（曾被 hook 退回）' : ''}
            </Text>
            <Text dimColor>  ① 發送端：{tally(res(it).map(r => r.sender))}</Text>
            <Text dimColor>  ② 接收端：{tally(res(it).map(r => r.receiver))}</Text>
            <Text dimColor>  ③ 自動檢查：{tally(res(it).map(r => r.gate))}</Text>
            <Text color={it.owner.includes('Owner') ? 'green' : 'cyan'}>  ④ 交給：{it.owner || '（未填）'}　今天做：{it.today === 'true' ? '是' : '否'}</Text>
            {it.waiting && <Text dimColor>     在等：{it.waiting.slice(0, 56)}</Text>}
          </Box>
        ))}
        <Box marginTop={1}><Text dimColor>資料來源：{s.source}（{Object.keys(s.results).length} 筆查核結果）</Text></Box>
      </Box>
    )
  })
}
