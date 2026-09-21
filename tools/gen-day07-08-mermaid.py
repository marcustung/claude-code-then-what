# -*- coding: utf-8 -*-
"""Day 7 / Day 8 figures from the mermaid blocks that used to sit in the article body (iThome does not render
mermaid). Reuses HEAD from gen-day03-mermaid.py; PNG via tools/export-diagram-png.py. Run from repo root."""
import io, os, subprocess, importlib.util
spec = importlib.util.spec_from_file_location('g03', os.path.join('tools', 'gen-day03-mermaid.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
OUT, MMD = g.OUT, g.MMD

DIAGRAMS = {
'day07-context-select-r1': ('Context 跟著任務選：只給能改變這次判斷的東西', '''flowchart LR
    A[眼前任務<br/>一個狀態判斷] --> B[相關規則與來源<br/>RULE-01 理由卡]
    B --> C[必要程式與反例<br/>目前函式・五個情境]
    C --> D[Claude 提出判斷]
    D --> E[核對引用與判斷<br/>trace 有 Read？標記回來了？五項對？]
''', '示意；依 2026-09-12 與 09-19 三次讀卡實跑整理，非公司系統'),
'day08-report-path-r1': ('報表沒有走我以為的那支查詢', '''flowchart TD
    A[報表入口] --> B[列表查詢<br/>WHERE 只有公司・員工・薪資群組<br/>沒有任何日期條件]
    B --> C[計數<br/>LINQ 直接數，不看生效日]
    D[我原本假設的那支查詢<br/>有日期條件・SQL 正確] --> E[另外三個作業<br/>多處共用，不得一併修改]
''', '示意；依答案卷更正紀錄的結構重繪，隱去內部名稱'),
}
HEAD = g.HEAD.replace('示意；依 2026-09-15 訂單取消合成實跑整理，非公司系統', '%(foot)s')

def main():
    for name, (title, src, foot) in DIAGRAMS.items():
        io.open(os.path.join(MMD, name.replace('-r1', '') + '.mmd'), 'w', encoding='utf-8', newline='\n').write(src)
        p = os.path.join(OUT, name + '.html')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(HEAD % dict(title=title, src=src, foot=foot))
        png = os.path.join(OUT, name + '.png')
        r = subprocess.run(['python', 'tools/export-diagram-png.py', p, png, '2', '1300', '#cap'], capture_output=True, text=True)
        print(name, 'ok' if r.returncode == 0 else r.stderr[-400:])

if __name__ == '__main__':
    main()
