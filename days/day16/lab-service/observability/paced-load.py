# -*- coding: utf-8 -*-
"""分段施壓：讓 Prometheus（5 秒抓一次）在一段時間窗內取得多個樣本。
tools/load.py 一輪只跑 0.6 秒，單跑會在時間序列上變成一根針，看不出趨勢。

  python observability/paced-load.py --label healthy --rounds 10 --gap 8
"""
import argparse, subprocess, sys, time, os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True)
    ap.add_argument('--rounds', type=int, default=10)
    ap.add_argument('--gap', type=float, default=8.0, help='每輪之間的間隔秒數')
    ap.add_argument('--orders', type=int, default=300)
    ap.add_argument('--concurrency', type=int, default=12)
    ap.add_argument('--api', default='http://127.0.0.1:5080')
    a = ap.parse_args()

    out = os.path.join(ROOT, 'observability', '.run', 'paced-' + a.label)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    rounds = []
    for i in range(1, a.rounds + 1):
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'load.py'),
                            '--api', a.api, '--run-id', '%s-%02d' % (a.label, i),
                            '--out', os.path.join(out, '%02d' % i),
                            '--orders', str(a.orders), '--concurrency', str(a.concurrency),
                            '--repeat', '2', '--seed', str(7 + i)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        line = (r.stdout or '').strip().splitlines()[-1] if r.stdout else '(no output)'
        print('[%s %02d/%02d] %s' % (a.label, i, a.rounds, line[:160]), flush=True)
        rounds.append({'round': i, 'at': time.time(), 'stdout_tail': line[:400], 'exit': r.returncode})
        if i < a.rounds:
            time.sleep(a.gap)
    window = {'label': a.label, 'start_epoch': t0, 'end_epoch': time.time(),
              'start_iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)),
              'end_iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'rounds': rounds}
    with open(os.path.join(out, 'window.json'), 'w', encoding='utf-8') as f:
        json.dump(window, f, ensure_ascii=False, indent=2)
    print('window %s: %s .. %s' % (a.label, window['start_iso'], window['end_iso']))


if __name__ == '__main__':
    main()
