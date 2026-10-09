from pathlib import Path
import shutil,hashlib,json
r=Path(__file__).resolve().parent
src=r.parent/'day26-live-lab/service'
for project in ['Api','Domain','FakeSink']:
 shutil.copytree(src/'src'/project,r/'service/src'/project,ignore=shutil.ignore_patterns('bin','obj'),dirs_exist_ok=True)
(r/'service/VERSION').write_text('day26-threadpool-teaching-v1',encoding='utf-8')
p=r/'service/src/Api/Program.cs'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('var app = builder.Build();','var app = builder.Build();\nLabTelemetry.Start(runDir);')
anchor='    var result = Cancellation.Cancel(before);'
assert anchor in s
s=s.replace(anchor,'''    // Teaching-only fake external lookup: identical delay, different waiting mechanism.
    if (Environment.GetEnvironmentVariable("LAB_WAIT_MODE") == "blocking")
        LabLookup.WaitSynchronously();
    else
        await LabLookup.WaitAsynchronously();
'''+anchor)
s+='''
// Isolated experiment: no ThreadPool min/max override. Delay simulates I/O, not a real dependency.
static class LabLookup
{
    public static async Task WaitAsynchronously() { await Task.Delay(500); }
    public static void WaitSynchronously() { WaitAsynchronously().GetAwaiter().GetResult(); }
}
static class LabTelemetry
{
    public static void Start(string runDir)
    {
        // Dedicated OS thread: monitoring must not wait for the starving ThreadPool.
        var t = new Thread(() => {
            using var f = new StreamWriter(Path.Combine(runDir, "runtime.jsonl"));
            var proc = System.Diagnostics.Process.GetCurrentProcess();
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var prev = proc.TotalProcessorTime.TotalMilliseconds; var last = sw.Elapsed.TotalMilliseconds;
            while (true) {
                var now = sw.Elapsed.TotalMilliseconds; var cpu = proc.TotalProcessorTime.TotalMilliseconds;
                ThreadPool.GetAvailableThreads(out var available, out var io);
                ThreadPool.GetMaxThreads(out var max, out var maxIo);
                f.WriteLine(JsonSerializer.Serialize(new { elapsed_ms = now, ts = DateTimeOffset.UtcNow,
                    threads = ThreadPool.ThreadCount, pending = ThreadPool.PendingWorkItemCount,
                    completed = ThreadPool.CompletedWorkItemCount, available, max,
                    cpu_core_percent = (cpu-prev)/Math.Max(now-last,1)*100,
                    gc_heap_bytes = GC.GetTotalMemory(false), working_set_bytes = Environment.WorkingSet,
                    processor_count = Environment.ProcessorCount }));
                f.Flush(); prev=cpu; last=now; Thread.Sleep(100);
            }
        });
        t.IsBackground=true; t.Name="LabTelemetry"; t.Start();
    }
}
'''
p.write_text(s,encoding='utf-8')
manifest={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.glob('src/*/*.cs')}
(r/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Teaching copy created; original files unchanged.')
