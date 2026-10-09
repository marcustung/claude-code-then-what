from pathlib import Path
import json,sys
R=Path(__file__).resolve().parent
# Reuse the already exercised client without invoking its original five-run main routine.
s=(R/'run.py').read_text(encoding='utf-8').split('summaries=[]')[0]
s=s.replace("RUN=R/'runs'/", "RUN=R/'blind-runs'/")
ns={'__file__':str(R/'run.py')};exec(s,ns)
ws=Path((R/'workspace.txt').read_text())
ns['API']=ws/'src/Api/bin/Release/net9.0/Api.dll'
results=[ns['one']('incident',0),ns['one']('incident',1,True)]
(ns['RUN']/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
(R/'latest-blind.txt').write_text(str(ns['RUN'].relative_to(R)),encoding='utf-8')
print('DONE',ns['RUN'])
