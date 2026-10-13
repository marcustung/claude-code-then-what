# {{PRODUCT_NAME}} — 專案 SSOT（Single Source of Truth）

> 狀態：第一版（v1）｜對應系統：{{PRODUCT_NAME}}
> 定位：{{PRODUCT_ONE_LINER}}
> 本文件是本專案的最高**意圖**事實來源（Why）：定義「我為何存在、我由什麼組成、
> 我如何被使用」。結構（What）與行為（How）不在此重寫，而是**指向**既有權威文件。
> 任何 Agent 與人在演化系統前必須先讀本文件，演化後必須回寫。姊妹文件：
> 《Evolution_Goals.md》（往哪演化）與《Stability_Goals.md》（演化的安全邊界）。

---

## 第一部分 — 我的存在價值（Why I Exist）

### 1.1 產品北極星指標（North Star）

> **{{NORTH_STAR_ONE_SENTENCE}}**

{{NORTH_STAR_CORE_PROMISE—北極星不可被稀釋的核心承諾，一段話}}

### 1.2 思考框架（價值鏈節點）

本系統把「{{VALUE_CHAIN_SUBJECT，例如：一個職缺的一生／客戶問題的一生}}」拆成
N 個節點。每個節點各有要降低的成本；標記 ★ 者為當前**主要施力點**。

| 節點 | 目標 | 機制／模組 | 施力 |
| :--- | :--- | :--- | :---: |
| ① {{NODE_1}} | {{NODE_1_GOAL}} | {{NODE_1_MECHANISM}} | |
| ② {{NODE_2}} | {{NODE_2_GOAL}} | {{NODE_2_MECHANISM}} | **★** |
| … | | | |

### 1.3 子目標（依優先序）

1. **{{SUBGOAL_1}}** —（已落地／部分落地／roadmap）
2. **{{SUBGOAL_2}}** —
3. **{{SUBGOAL_3}}** —

> **價值鐵律**：任何新功能／提案在進入 backlog 前，必須能對映到上述某一子目標，
> 並說明它降低了哪一段成本、或改善《Evolution_Goals.md》哪一項輸入指標。
> **無法對映者不做。**

---

## 第二部分 — 我的組成方式（What I'm Made Of）

> **本部分為「指向」而非「重寫」**：SSOT 只做地圖，細節以被指向文件為準；
> 不一致時以被指向文件為準並回報矛盾。

- 產品架構：{{POINTER_TO_ARCH_DOCS}}
- 系統架構與工程慣例：{{POINTER_TO_CONVENTIONS}}
- 狀態機／核心行為：{{POINTER_TO_BEHAVIOR_DOCS}}

### SSOT 三層與權威來源

| 層級 | 事實類型 | 權威來源 | 回寫規則 |
| :--- | :--- | :--- | :--- |
| **結構** | 是什麼 | {{STRUCTURE_AUTHORITY，如 domain 型別＋glossary}} | 型別變更與文件同一 PR 更新 |
| **行為** | 怎麼做 | {{BEHAVIOR_AUTHORITY，如 conventions＋狀態機}} | 規則只改一處，外層不得繞過 |
| **意圖** | 為什麼 | 本文件 §1 + README + {{DECISION_LOG，如 ADR}} | 每輪有效演化回寫動機與指標變化 |

> **鐵律**：三層任一落後即為技術債；有 diff 無紀錄視為違規（對映 Stability「透明性」KPI）。

---

## 第三部分 — 我的使用方式（How I'm Used）

依角色列舉典型使用場景：{{ROLES_AND_SCENARIOS}}

---

## 附錄 — cs-loop 治理迴路（實作層）

### 角色與權限（雙 Gate）

| 角色 | 權限 | 不可做 |
| :--- | :--- | :--- |
| {{OWNER_NAME}}（人類） | Gate 1：backlog「裁決」欄核准權；Gate 2：落地合併權 | — |
| cs-loop routine（agent） | 觀測、提案（待審列＋issue 檔）、寫報告、對已核准案開 land/* 分支實作、回寫與覆盤 | 填裁決欄、合併、{{PUSH_POLICY，本地模式加：push}}、在 main 直改 app code |

### 提案 ID 慣例

{{PROPOSAL_ID_RULE，例如：來自票務系統的案直接用卡號；自主發現用 P-YYYY-MM-DD-NN}}

### 迴路檔案地圖

`cs-loop/backlog/backlog.md`（狀態索引）・`cs-loop/issues/`（一案一檔）・
`cs-loop/health-reports/`（每日報告）・`CHANGELOG.md`（回寫）・
`.claude/commands/cs-loop.md`（八步例行）
