# 訂單取消開發規則
RULES-TOKEN: oc-sdlc-dev-1

先讀 plan.md、specs/rules-v2.md、design-input/。
理由：RefundRequested 只是提出要求，金流是另一份契約；直接連金流會把未核准的業務決策帶進本次修改。
範圍：只處理 Domain 與測試。不要修改 API、不要新增套件或外部呼叫。
spec 以 v2 為教學目標，v1 只供比較，並非公司核准。
報告要附來源；未讀到不等於不存在；不得把固定分支語法當規格。
本次由外層 runner 執行測試，不宣稱自己執行。
