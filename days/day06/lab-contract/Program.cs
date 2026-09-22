// Synthetic counterexample; original Validate copied unchanged from v11 fixture.
var ready = new Delivery("demo-v1", "ready_for_review", ["RULE-01"], ["run.txt"], []);
var failures=0;
void Check(string name, bool pass) { Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {name}"); if(!pass) failures++; }
Check("empty evidence rejected", Validate(ready with { Evidence=[] }).Contains("missing evidence"));
Check("declared blocker rejects ready", Validate(ready with { Unknowns=["rule unconfirmed"] }).Count>0);
Check("blocked with reason is structurally valid", Validate(ready with { Status="blocked", Unknowns=["rule unconfirmed"] }).Count==0);
var fake=ready with { Evidence=["deliberately-nonexistent-evidence.txt"] };
Check("fixture evidence file is absent", !File.Exists(fake.Evidence[0]));
Check("nonexistent evidence still passes structure", Validate(fake).Count==0);
Console.WriteLine("SYNTHETIC structure_errors=" + Validate(fake).Count + "; evidence_exists=" + File.Exists(fake.Evidence[0]));
return failures==0 ? 0 : 1;

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
record Delivery(string Revision, string Status, string[] Rules, string[] Evidence, string[] Unknowns);
