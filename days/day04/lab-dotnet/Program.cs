using System.Text.Json;

// Public synthetic teaching fixture. Not company code or a Claude session replay.
var mode = args.FirstOrDefault() ?? "all";
var failed = 0;
void Check(string name, bool pass)
{
    Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {name}");
    if (!pass) failed++;
}

if (mode is "all" or "baseline")
{
    // Synthetic person-minutes; elapsed minutes are a separate dimension.
    var before = new Work(20, 30, 15, 5, 240);
    var after = new Work(15, 10, 25, 20, 180);
    Console.WriteLine($"SYNTHETIC before_effort={before.Effort}; after_effort={after.Effort}; before_elapsed={before.Elapsed}; after_elapsed={after.Elapsed}");
    Check("faster elapsed is not lower human effort", before.Effort == after.Effort && after.Elapsed < before.Elapsed);
}
if (mode is "all" or "contract")
{
    var ready = new Delivery("demo-v1", "ready_for_review", ["RULE-01"], ["run.txt"], []);
    var bad = ready with { Evidence = [] };
    var blocked = ready with { Status = "blocked", Unknowns = ["Who may reopen?"] };
    Check("ready requires evidence", Validate(ready).Count == 0);
    Check("missing evidence rejected", Validate(bad).Contains("missing evidence"));
    Check("unknown prevents ready", Validate(ready with { Unknowns = ["unknown rule"] }).Count > 0);
    Check("blocked can be valid but is not accepted", Validate(blocked).Count == 0 && blocked.Status != "ready_for_review");
    Check("unknown status rejected", Validate(ready with { Status = "done" }).Count > 0);
    Console.WriteLine(JsonSerializer.Serialize(ready));
}
if (mode is "all" or "bug")
{
    var cases = new[] {
        new Scenario("direct return forbidden", true, false, false, false),
        new Scenario("request without authority forbidden", true, true, false, false),
        new Scenario("authority without explicit request forbidden", true, false, true, false),
        new Scenario("authorized explicit reopen allowed", true, true, true, true),
        new Scenario("non-rejected outside this guard", false, false, false, true)
    };
    int oldFailures = 0;
    foreach (var c in cases)
    {
        var oldResult = !c.Rejected;
        if (oldResult != c.Expected) oldFailures++;
        Console.WriteLine($"BEFORE {c.Name}: {(oldResult == c.Expected ? "PASS" : "FAIL")}");
        Check("AFTER " + c.Name, CanEnterInterview(c.Rejected, c.ReopenRequested, c.Authorized) == c.Expected);
    }
    Check("regression reproduces old bug", oldFailures == 1);
}
if (mode is "all" or "context")
{
    var a = "Task: review proposed code return !rejected; and decide whether each input may pass this guard. Inputs (rejected,reopenRequested,authorized): (true,false,false), (true,true,false), (true,false,true), (true,true,true), (false,false,false). Rule RULE-01: direct return is forbidden; explicit authorized reopening is allowed. Non-rejected states are outside this guard. Output per-input decision, rule_id, unknowns. Do not invent other system rules.";
    var reason = " Reason: direct return bypasses the rejection decision; explicit authorized reopening records a deliberate exception.";
    var b = a + reason;
    Check("B differs only by specified reason", b.StartsWith(a) && b[a.Length..] == reason);
    Console.WriteLine("PROMPT_A=" + a);
    Console.WriteLine("PROMPT_B=" + b);
    Console.WriteLine("MODEL_RESULTS=NOT_RUN; no superiority claim");
}
if (mode is not ("all" or "baseline" or "contract" or "bug" or "context"))
{
    Console.Error.WriteLine("Usage: dotnet run -- [all|baseline|contract|bug|context]");
    return 2;
}
return failed == 0 ? 0 : 1;

static bool CanEnterInterview(bool rejected, bool reopenRequested, bool authorized)
    => !rejected || (reopenRequested && authorized);

static List<string> Validate(Delivery d)
{
    var errors = new List<string>();
    if (string.IsNullOrWhiteSpace(d.Revision)) errors.Add("missing revision");
    if (d.Status is not ("ready_for_review" or "blocked")) errors.Add("invalid status");
    if (d.Rules.Length == 0) errors.Add("missing rule");
    if (d.Status == "ready_for_review" && d.Evidence.Length == 0) errors.Add("missing evidence");
    if (d.Status == "ready_for_review" && d.Unknowns.Length > 0) errors.Add("unresolved unknowns");
    if (d.Status == "blocked" && d.Unknowns.Length == 0) errors.Add("missing blocker");
    return errors;
}
record Work(int Context, int Implementation, int Review, int Rework, int Elapsed)
{
    public int Effort => Context + Implementation + Review + Rework;
}
record Delivery(string Revision, string Status, string[] Rules, string[] Evidence, string[] Unknowns);
record Scenario(string Name, bool Rejected, bool ReopenRequested, bool Authorized, bool Expected);
