"""Grade the dashboard Claude built against claude-dashboard-criteria.md (auto part D1–D5).
Reads the dashboard through the local Grafana API and executes every panel query itself."""
from pathlib import Path
import base64, json, re, sys, time, urllib.parse, urllib.request

ROOT = Path(__file__).resolve().parent
G = 'http://127.0.0.1:3224'
AUTH = {'Authorization': 'Basic ' + base64.b64encode(b'admin:admin').decode()}  # local teaching Grafana only


def get(path):
    with urllib.request.urlopen(urllib.request.Request(G + path, headers=AUTH), timeout=20) as r: return json.load(r)


def panels(dash):
    out = []
    for p in dash.get('panels', []):
        out += panels(p) if p.get('type') == 'row' and p.get('panels') else [p]
    return out


def prom(expr):
    q = urllib.parse.urlencode({'query': expr})
    try: return get(f'/api/datasources/proxy/uid/prometheus/api/v1/query?{q}')['data']['result']
    except Exception as e: return {'error': str(e)}


def loki(expr):
    now = time.time_ns(); q = urllib.parse.urlencode({'query': expr, 'start': now-3600*10**9, 'end': now, 'limit': 20})
    try: return get(f'/api/datasources/proxy/uid/loki/loki/api/v1/query_range?{q}')['data']['result']
    except Exception as e: return {'error': str(e)}


def main():
    w = ROOT/(sys.argv[1] if len(sys.argv) > 1 else (ROOT/'latest-claude-dashboard-run.txt').read_text().strip())
    uid = sys.argv[2] if len(sys.argv) > 2 else 'day25-work-view'
    try: dash = get(f'/api/dashboards/uid/{uid}')['dashboard']
    except Exception as e:
        out = {'D1': False, 'error': str(e)}; (w/'grading.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8'); print(out); return
    ps = panels(dash); report = []
    for p in ps:
        for t in p.get('targets', []):
            raw = t.get('expr') or ''
            # Substitute Grafana template variables the way the dashboard would at view time (all runs, 1h range).
            expr = raw.replace('${run}', '.*').replace('$run', '.*').replace('$__range', '1h').replace('$__rate_interval', '2m').replace('$__interval', '1m')
            kind = 'loki' if ('service_name' in expr and '{' in expr and '|' in expr) or str((t.get('datasource') or p.get('datasource') or {})).lower().find('loki') >= 0 else 'prom'
            res = loki(expr) if kind == 'loki' else prom(expr)
            report.append({'panel': p.get('title'), 'type': p.get('type'), 'kind': kind, 'expr': raw, 'evaluated_as': expr, 'result': res})
    def vals_for(run):
        v = []
        for r in report:
            if r['kind'] == 'prom' and isinstance(r['result'], list):
                for s in r['result']:
                    if s.get('metric', {}).get('run') == run:
                        try: v.append((r['expr'], float(s['value'][1])))
                        except Exception: pass
        return v
    d1 = len(ps) >= 3
    d2 = any(abs(x-1/3) < 0.01 or abs(x-100/3) < 0.5 for _, x in vals_for('sep-missing'))
    bad = [r['expr'] for r in report if 'sender_reported_sent' in r['expr'] and ('work_expected' in r['expr'] or '/' in r['expr'])]
    d3 = not bad
    d4 = any('work_status' in r['expr'] for r in report) or any(r['kind'] == 'loki' and 'unknown' in r['expr'] for r in report)
    d5 = any(r['kind'] == 'loki' and 'day25-work-view' in r['expr'] and 'notification' in json.dumps(r['result'], ensure_ascii=False) for r in report)
    s1 = any(r['type'] == 'stat' and 'work_status' in r['expr'] for r in report)
    s2 = any('work_stage_count' in r['expr'] for r in report)
    n1 = any('next_step' in r['expr'] or 'owner' in r['expr'] for r in report)
    p1 = any(r['type'] in ('bargauge', 'gauge') and r['kind'] == 'prom' and isinstance(r['result'], list) and any(s.get('metric', {}).get('run') == 'sep-missing' and abs(float(s['value'][1]) - 1/3) < 0.01 or s.get('metric', {}).get('run') == 'sep-missing' and abs(float(s['value'][1]) - 100/3) < 0.5 for s in r['result']) for r in report)
    out = {'uid': uid, 'N1': n1, 'P1': p1, 'S1': s1, 'S2': s2, 'panels': len(ps), 'D1': d1, 'D2': d2, 'D3': d3, 'D3_offending': bad, 'D4': d4, 'D5': d5,
           'sep_missing_values': vals_for('sep-missing'), 'sep_slow_values': vals_for('sep-slow'),
           'queries': [{k: v for k, v in r.items() if k != 'result'} | {'series': len(r['result']) if isinstance(r['result'], list) else r['result']} for r in report]}
    (w/'grading.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    (w/'dashboard-from-grafana.json').write_text(json.dumps(dash, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'queries'}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
