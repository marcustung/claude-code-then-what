# RULE-01
marker: RULE-CONTEXT-7-KITE-0911
version: demo-v2
scope: Single synthetic rejected-to-interview guard.
rule: If rejected, allow only when reopenRequested AND authorized; otherwise this guard does not block.
reason: Prevent bypassing rejection; allow deliberate, explicitly authorized exceptions.
unknowns: Authorization source, audit storage, API and other state rules are unspecified. Do not invent them.
