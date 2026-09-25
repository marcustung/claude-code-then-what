// 訂單取消＋通知的薄 HTTP API。程序內記憶體儲存（不保證重啟持久性）；每 request 一行 logs.jsonl；/metrics 文字格式。
// 通知走 Channel → NotificationWorker → POST 到 fake sink（OC_SINK_URL）。故障注入由 OC_FAULTS 指定的 JSON 檔提供，只供演練。
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Channels;
using OrderCancel.Domain;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
var runDir = Environment.GetEnvironmentVariable("OC_RUN_DIR") ?? "runs/default";
Directory.CreateDirectory(runDir);
var versionFile = Path.Combine(AppContext.BaseDirectory, "VERSION");
var version = File.Exists(versionFile) ? File.ReadAllText(versionFile).Trim() : (Environment.GetEnvironmentVariable("OC_VERSION") ?? "unknown");
var faults = Faults.Load(Environment.GetEnvironmentVariable("OC_FAULTS"));
var store = new OrderStore();
var metrics = new Metrics();
var log = new JsonlLog(Path.Combine(runDir, "logs.jsonl"), version);
var channel = Channel.CreateUnbounded<Notification>();
builder.Services.AddSingleton(store); builder.Services.AddSingleton(metrics); builder.Services.AddSingleton(log); builder.Services.AddSingleton(faults);
builder.Services.AddSingleton(channel);
builder.Services.AddHostedService<NotificationWorker>();
var app = builder.Build();
// 例外中介層：任何未處理例外寫一行 log（型別、訊息、request_id）並回 500；OOM 這類也會留在 logs.jsonl 與 stderr。
app.Use(async (ctx, next) =>
{
    try { await next(); }
    catch (Exception ex)
    {
        var rid = ctx.Request.Headers["X-Request-Id"].FirstOrDefault();
        try { log.Write(new { level = "ERROR", @event = "unhandled_exception", request_id = rid, path = ctx.Request.Path.Value, exception = ex.GetType().FullName, message = ex.Message }); } catch { }
        try { Console.Error.WriteLine($"[unhandled] {ex.GetType().FullName}: {ex.Message} path={ctx.Request.Path} request_id={rid}"); } catch { }
        if (!ctx.Response.HasStarted) { ctx.Response.StatusCode = 500; await ctx.Response.WriteAsync("{\"ok\":false,\"reason\":\"internal_error\"}"); }
    }
});
log.Write(new { level = "INFO", @event = "startup", faults_loaded = faults.Any, sink = Environment.GetEnvironmentVariable("OC_SINK_URL") });

app.MapGet("/health", () => Results.Ok(new { ok = true, version }));
app.MapGet("/ready", () => Results.Ok(new { ready = true, version }));   // 記憶體儲存無外部依賴；readiness＝程序起來
app.MapPost("/orders", async (HttpRequest req) =>
{   // 建單（測試用）：body {id, shipped, paid}
    using var doc = await JsonDocument.ParseAsync(req.Body); var r = doc.RootElement;
    var id = r.GetProperty("id").GetString()!;
    var order = new Order(r.TryGetProperty("shipped", out var s) && s.GetBoolean(), r.TryGetProperty("paid", out var p) && p.GetBoolean(), false);
    store.Put(id, order);
    return Results.Ok(new { id, order });
});
app.MapGet("/orders/{id}", (string id) => store.TryGet(id, out var o) ? Results.Ok(new { id, order = o }) : Results.NotFound());
app.MapPost("/orders/{id}/cancel", async (string id, HttpRequest req) =>
{
    var t0 = DateTime.UtcNow;
    string? payload = null;
    if (req.ContentLength > 0) { using var sr = new StreamReader(req.Body); payload = await sr.ReadToEndAsync(); }
    if (faults.RetainPayloads) Retained.Keep(id, payload);   // 演練注入：把每筆 request body 留在記憶體，無上限
    var rid = req.Headers["X-Request-Id"].FirstOrDefault() ?? Guid.NewGuid().ToString("N")[..12];
    var runId = req.Headers["X-Run-Id"].FirstOrDefault();
    var actor = req.Headers["X-Actor"].FirstOrDefault();
    if (string.IsNullOrEmpty(actor))
    {
        metrics.Inc("cancel_requests_total", "unauthorized");
        log.Write(new { level = "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, result = "unauthorized" });
        return Results.Json(new { ok = false, reason = "unauthorized", request_id = rid }, statusCode: 401);
    }
    if (!store.TryGet(id, out var before))
    {
        metrics.Inc("cancel_requests_total", "not_found");
        log.Write(new { level = "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, result = "not_found" });
        return Results.Json(new { ok = false, reason = "not_found", request_id = rid }, statusCode: 404);
    }
    var result = Cancellation.Cancel(before);
    bool transitioned = Cancellation.Transitioned(before, result);
    string outcome; int status;
    if (before.Shipped) { outcome = "rejected_shipped"; status = 409; }          // BR-02，不通知（NC-03）
    else if (transitioned) { outcome = "ok"; status = 200; store.Put(id, result.Order); }
    else { outcome = "idempotent"; status = 200; }                               // BR-04／NC-02，不通知
    metrics.Inc("cancel_requests_total", outcome);
    if (transitioned)
    {
        metrics.Inc("transitions_total");
        var n = new Notification(Guid.NewGuid().ToString("N"), id, rid, runId, "order_cancelled", result.RefundRequested);
        metrics.Inc("notify_enqueued_total");
        if (faults.SyncNotify)
            await NotificationWorker.SendOnce(n, metrics, log, Environment.GetEnvironmentVariable("OC_SINK_URL") ?? "http://127.0.0.1:5081/notify");   // 演練注入：在請求路徑上同步等接收端
        else
            await channel.Writer.WriteAsync(n);
    }
    var lat = (DateTime.UtcNow - t0).TotalMilliseconds;
    metrics.ObserveLatency(lat);
    log.Write(new { level = status == 200 ? "INFO" : "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, actor, result = outcome, transitioned, refund_requested = result.RefundRequested, latency_ms = Math.Round(lat, 1), queue_depth = channel.Reader.Count });
    return Results.Json(new { ok = status == 200, transitioned, refund_requested = result.RefundRequested, reason = status == 200 ? null : outcome, request_id = rid, order = status == 200 ? result.Order : before }, statusCode: status);
});
app.MapGet("/metrics", () => Results.Text(metrics.Render(channel.Reader.Count, version), "text/plain"));
app.Run();

record Notification(string NotificationId, string OrderId, string RequestId, string? RunId, string Kind, bool RefundRequested, int Deferrals = 0);

sealed class OrderStore
{
    readonly Dictionary<string, Order> _d = new(); readonly object _g = new();
    public void Put(string id, Order o) { lock (_g) _d[id] = o; }
    public bool TryGet(string id, out Order o) { lock (_g) return _d.TryGetValue(id, out o!); }
}

sealed class Metrics
{
    readonly Dictionary<string, long> _c = new(); readonly object _g = new();
    public void Inc(string name, string? label = null)
    {
        var k = label is null ? name : name + "{result=\"" + label + "\"}";
        lock (_g) _c[k] = _c.GetValueOrDefault(k) + 1;
    }
    static readonly double[] Buckets = { 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000 };
    readonly long[] _hist = new long[Buckets.Length + 1]; double _latSum; long _latCount;
    public void ObserveLatency(double ms)
    {
        lock (_g) { _latSum += ms; _latCount++; int i = 0; while (i < Buckets.Length && ms > Buckets[i]) i++; _hist[i]++; }
    }
    public string Render(int depth, string version)
    {
        lock (_g)
        {
            var sb = new System.Text.StringBuilder();
            foreach (var kv in _c.OrderBy(k => k.Key)) sb.Append("oc_").Append(kv.Key).Append(' ').Append(kv.Value).Append('\n');
            sb.Append("oc_notify_queue_depth ").Append(depth).Append('\n');
            long cum = 0;
            for (int i = 0; i < Buckets.Length; i++) { cum += _hist[i]; sb.Append("oc_request_latency_ms_bucket{le=\"").Append(Buckets[i]).Append("\"} ").Append(cum).Append('\n'); }
            cum += _hist[Buckets.Length]; sb.Append("oc_request_latency_ms_bucket{le=\"+Inf\"} ").Append(cum).Append('\n');
            sb.Append("oc_request_latency_ms_sum ").Append(Math.Round(_latSum, 1)).Append('\n').Append("oc_request_latency_ms_count ").Append(_latCount).Append('\n');
            sb.Append("oc_gc_heap_bytes ").Append(GC.GetTotalMemory(false)).Append('\n');
            sb.Append("oc_working_set_bytes ").Append(Environment.WorkingSet).Append('\n');
            sb.Append("oc_gc_collections_gen2 ").Append(GC.CollectionCount(2)).Append('\n');
            sb.Append("oc_info{version=\"").Append(version).Append("\"} 1\n");
            return sb.ToString();
        }
    }
}

sealed class JsonlLog
{
    readonly string _p; readonly string _v; readonly object _g = new();
    public JsonlLog(string p, string v) { _p = p; _v = v; }
    public void Write(object o)
    {
        var d = JsonSerializer.SerializeToNode(o)!.AsObject();
        d["ts"] = DateTimeOffset.Now.ToString("o"); d["version"] = _v;
        lock (_g) File.AppendAllText(_p, d.ToJsonString() + "\n");
    }
}

// 演練注入 retain_payloads 的落點（v1.2.0 修復後）：客服查詢暫存改為有上限的環狀緩衝——最多 MaxItems 筆、每筆只留前 MaxBodyChars 字與原長度。
// v1.1.0 之前是無上限的 List，壓力下把 heap 撐到上限（見 evidence/runs/oom-retained-payloads-*、diagnosis/oom）。
static class Retained
{
    const int MaxItems = 256, MaxBodyChars = 256;
    static readonly Queue<(string OrderId, string Head, int Length)> _items = new(); static readonly object _g = new();
    public static void Keep(string orderId, string? body)
    {
        var b = body ?? "";
        lock (_g) { _items.Enqueue((orderId, b.Length > MaxBodyChars ? b[..MaxBodyChars] : b, b.Length)); while (_items.Count > MaxItems) _items.Dequeue(); }
    }
    public static int Count { get { lock (_g) return _items.Count; } }
}

sealed class Faults
{
    public int? DropOverQueue; public int DelayMs; public bool RetainPayloads; public bool SyncNotify;
    public bool Any => DropOverQueue is not null || DelayMs > 0 || RetainPayloads || SyncNotify;
    public static Faults Load(string? path)
    {
        var f = new Faults();
        if (string.IsNullOrEmpty(path) || !File.Exists(path)) return f;
        using var doc = JsonDocument.Parse(File.ReadAllText(path)); var r = doc.RootElement;
        if (r.TryGetProperty("notify_drop_over_queue", out var q)) f.DropOverQueue = q.GetInt32();
        if (r.TryGetProperty("notify_delay_ms", out var d)) f.DelayMs = d.GetInt32();
        if (r.TryGetProperty("retain_payloads", out var rp)) f.RetainPayloads = rp.GetBoolean();
        if (r.TryGetProperty("sync_notify", out var sn)) f.SyncNotify = sn.GetBoolean();
        return f;
    }
}

// 通知 worker：從 channel 取出 → POST sink → 失敗重試 3 次（200／400／800 ms）→ 超過進 dead_letter（NC-05）。
// 故障 notify_drop_over_queue（演練用）：佇列深度超過 N 時觸發「壓力延後」路徑。
// v1.0.0 的行為是記一行 notify_deferred 後不再重送、sent 計數照加（服務說送了、接收端沒收據）；v1.1.0 改為重排到隊尾、sent 只在 ack 後才加。
// 這條故障設計移植自 O 服務 fault-A；是演練用注入，不是自然事故。
sealed class NotificationWorker : BackgroundService
{
    readonly Channel<Notification> _ch; readonly Metrics _m; readonly JsonlLog _log; readonly Faults _f; readonly HttpClient _http = new();
    readonly string _sink = Environment.GetEnvironmentVariable("OC_SINK_URL") ?? "http://127.0.0.1:5081/notify";
    static readonly int[] Backoff = { 200, 400, 800 };
    const int MaxDeferrals = 5;
    public NotificationWorker(Channel<Notification> ch, Metrics m, JsonlLog log, Faults f) { _ch = ch; _m = m; _log = log; _f = f; }
    static readonly HttpClient SharedHttp = new();
    /// 同步送一次（含重試），供 sync_notify 演練路徑使用；計數規則與 worker 相同。
    public static async Task SendOnce(Notification n, Metrics m, JsonlLog log, string sink)
    {
        bool sent = false;
        for (int attempt = 0; attempt <= Backoff.Length && !sent; attempt++)
        {
            try
            {
                var body = JsonSerializer.Serialize(new { notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, kind = n.Kind, refund_requested = n.RefundRequested, attempt });
                var resp = await SharedHttp.PostAsync(sink, new StringContent(body, System.Text.Encoding.UTF8, "application/json"));
                sent = resp.IsSuccessStatusCode;
            }
            catch (Exception e) { log.Write(new { level = "WARN", @event = "notify_attempt_failed", notification_id = n.NotificationId, attempt, error = e.GetType().Name }); }
            if (!sent && attempt < Backoff.Length) await Task.Delay(Backoff[attempt]);
        }
        if (sent) { m.Inc("notify_sent_total"); log.Write(new { level = "INFO", @event = "notify_sent", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, sync = true }); }
        else { m.Inc("notify_failed_total"); m.Inc("notify_dead_letter_total"); log.Write(new { level = "ERROR", @event = "notify_dead_letter", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, attempts = Backoff.Length + 1 }); }
    }
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await foreach (var n in _ch.Reader.ReadAllAsync(ct))
        {
            if (_f.DelayMs > 0) await Task.Delay(_f.DelayMs, ct);
            if (_f.DropOverQueue is int q && _ch.Reader.Count > q)
            {   // v1.1.0 修復：壓力下不再「假裝送了」。延後＝重排到隊尾（最多 MaxDeferrals 次），sent_total 只在接收端 ack 後才加；延後另計。
                if (n.Deferrals < MaxDeferrals)
                {
                    _m.Inc("notify_deferred_total");
                    _log.Write(new { level = "INFO", @event = "notify_deferred", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, queue_depth = _ch.Reader.Count, deferrals = n.Deferrals + 1, requeued = true });
                    await _ch.Writer.WriteAsync(n with { Deferrals = n.Deferrals + 1 }, ct);
                    continue;
                }
                _log.Write(new { level = "WARN", @event = "notify_deferral_limit", notification_id = n.NotificationId, deferrals = n.Deferrals, note = "超過延後上限，改走一般送出／重試路徑" });
            }
            bool sent = false;
            for (int attempt = 0; attempt <= Backoff.Length && !sent; attempt++)
            {
                try
                {
                    var body = JsonSerializer.Serialize(new { notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, kind = n.Kind, refund_requested = n.RefundRequested, attempt });
                    var resp = await _http.PostAsync(_sink, new StringContent(body, System.Text.Encoding.UTF8, "application/json"), ct);
                    sent = resp.IsSuccessStatusCode;
                    if (!sent) _log.Write(new { level = "WARN", @event = "notify_attempt_failed", notification_id = n.NotificationId, attempt, status = (int)resp.StatusCode });
                }
                catch (Exception e) when (!ct.IsCancellationRequested)
                {
                    _log.Write(new { level = "WARN", @event = "notify_attempt_failed", notification_id = n.NotificationId, attempt, error = e.GetType().Name });
                }
                if (!sent && attempt < Backoff.Length) await Task.Delay(Backoff[attempt], ct);
            }
            if (sent)
            {
                _m.Inc("notify_sent_total");
                _log.Write(new { level = "INFO", @event = "notify_sent", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId });
            }
            else
            {
                _m.Inc("notify_failed_total"); _m.Inc("notify_dead_letter_total");
                _log.Write(new { level = "ERROR", @event = "notify_dead_letter", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, attempts = Backoff.Length + 1 });
            }
        }
    }
}
