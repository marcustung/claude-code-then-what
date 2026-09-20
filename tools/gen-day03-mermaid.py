# -*- coding: utf-8 -*-
"""Day 3 figures from mermaid sources (paper theme), exported to PNG with tools/export-diagram-png.py.
Sources are also written to examples/kit-review/diagrams/*.mmd for the public repo. Run from repo root."""
import io, os, subprocess

OUT = 'assets/diagrams/v12/investigation-notes'
MMD = 'examples/kit-review/diagrams'
os.makedirs(OUT, exist_ok=True); os.makedirs(MMD, exist_ok=True)

DIAGRAMS = {
'day03-order-state-r1': ('需求只講了一條線：未出貨才能取消', '''stateDiagram-v2
    direction LR
    [*] --> 已下單
    已下單 --> 已付款 : 付款
    已下單 --> 已取消 : 取消（需求）
    已付款 --> 已出貨 : 出貨
    已付款 --> 已取消 : 取消（需求）
    note right of 已出貨 : 已出貨還能取消嗎？需求說不行
    note right of 已取消 : 再取消一次？需求沒說。已付款的取消要退款？需求沒說
'''),
'day03-cancel-sequence-r1': ('程式多走了一步：把「已付款」變成「要求退款」', '''sequenceDiagram
    autonumber
    participant U as 使用者
    participant S as Cancellation.Cancel
    participant P as 付款服務（不存在）
    U->>S: Cancel(order)
    alt order.Shipped
        S-->>U: 原訂單，RefundRequested=false（不丟錯）
    else order.Cancelled
        S-->>U: 原訂單，RefundRequested=false（冪等）
    else 未出貨、未取消
        S->>S: Cancelled = true
        S->>S: RefundRequested = order.Paid
        Note over S,P: 需求沒提退款；程式把 Paid 直接接成 RefundRequested
        S-xP: （沒有呼叫）
        S-->>U: 取消後訂單，RefundRequested
    end
'''),
'day03-review-routing-r1': ('判級先於審查：確定性閘門 → 工具 → AI → Owner', '''flowchart TD
    PR[PR 到達<br/>含五項交接契約] --> G{確定性閘門<br/>路徑・Owner・diff 大小<br/>金額／授權／狀態規則？}
    G -- 是 --> L3
    G -- 否／不明 --> L1
    L1[第一層 工具<br/>編譯・格式・既有測試・靜態與安全規則] -- 失敗 --> R1[退回作者<br/>不准模型解釋掉]
    L1 -- 通過 --> L2[第二層 AI 對照材料<br/>規格版本・呼叫端・測試<br/>發現要附來源；找不到寫不知道]
    L2 -- 發現觸及核心規則 --> L3
    L2 -- 純低風險且政策涵蓋 --> M[簡化程序合併]
    L2 -- 一般修改 --> H[人確認 AI 材料後合併]
    L3[第三層 Owner 決定<br/>核心規則・例外・接受條件<br/>附前後狀態／循序圖] -- 缺依據 --> R2[退件單<br/>缺哪個依據・誰補・怎麼判]
    L3 -- 依據齊全 --> M2[合併＋記錄退回／revert／事故]
    M2 -.每季校準門檻.-> G
'''),
}

HEAD = '''<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>%(title)s</title>
<link href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-tc-webfont@1.2.0/lxgwwenkaitc-regular.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<style>body{background:#FAF6EE;margin:0;padding:24px 32px;font-family:'LXGW WenKai TC','DFKai-SB','標楷體',sans-serif}
h2{margin:0 0 12px;font-size:18px;color:#1F1F1F;font-weight:700}
.wrap{display:inline-block;background:#FAF6EE}
.mermaid{font-family:'LXGW WenKai TC','DFKai-SB','標楷體',sans-serif}
.foot{margin-top:10px;font-size:12px;color:#7A8399;text-align:right}
</style></head><body><div class="wrap" id="cap"><h2>%(title)s</h2>
<pre class="mermaid">%(src)s</pre>
<div class="foot">示意；依 2026-09-15 訂單取消合成實跑整理，非公司系統</div></div>
<script>mermaid.initialize({startOnLoad:true, theme:'base', fontFamily:"'LXGW WenKai TC','DFKai-SB',sans-serif",
 themeVariables:{primaryColor:'#FAF6EE', primaryTextColor:'#1F1F1F', primaryBorderColor:'#1F1F1F', lineColor:'#2B4C7E', secondaryColor:'#F6E27A', tertiaryColor:'#FDF3D0', noteBkgColor:'#F6E27A', noteTextColor:'#1F1F1F', noteBorderColor:'#F0A35E', actorBkg:'#FAF6EE', actorBorder:'#1F1F1F', signalColor:'#2B4C7E', signalTextColor:'#1F1F1F', labelBoxBkgColor:'#FDF3D0', labelBoxBorderColor:'#F0A35E', fontSize:'16px'},
 flowchart:{htmlLabels:true, curve:'basis', nodeSpacing:40, rankSpacing:48}, sequence:{actorMargin:70, messageMargin:40, width:190}});</script>
</body></html>
'''

def main():
    for name, (title, src) in DIAGRAMS.items():
        io.open(os.path.join(MMD, name.replace('-r1', '') + '.mmd'), 'w', encoding='utf-8', newline='\n').write(src)
        html = HEAD % dict(title=title, src=src)
        p = os.path.join(OUT, name + '.html')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(html)
        png = os.path.join(OUT, name + '.png')
        r = subprocess.run(['python', 'tools/export-diagram-png.py', p, png, '2', '1300', '#cap'], capture_output=True, text=True)
        print(name, 'ok' if r.returncode == 0 else r.stderr[-400:])

if __name__ == '__main__':
    main()
