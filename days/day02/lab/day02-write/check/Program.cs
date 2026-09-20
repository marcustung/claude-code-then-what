using System;

int pass = 0;
int fail = 0;

void Check(string name, bool actual, bool expected)
{
    if (actual == expected)
    {
        Console.WriteLine($"PASS: {name}");
        pass++;
    }
    else
    {
        Console.WriteLine($"FAIL: {name} (expected {expected}, got {actual})");
        fail++;
    }
}

// Not rejected: always allowed regardless of other flags.
Check("NotRejected_NoReopen_NoAuth", Guard.CanEnterInterview(false, false, false), true);
Check("NotRejected_Reopen_Auth", Guard.CanEnterInterview(false, true, true), true);

// Rejected, no reopen requested: blocked regardless of authorization.
Check("Rejected_NoReopen_NoAuth", Guard.CanEnterInterview(true, false, false), false);
Check("Rejected_NoReopen_Auth", Guard.CanEnterInterview(true, false, true), false);

// Rejected, reopen requested but not authorized: blocked.
Check("Rejected_Reopen_NoAuth", Guard.CanEnterInterview(true, true, false), false);

// Rejected, reopen requested and authorized: allowed (explicit reversal path).
Check("Rejected_Reopen_Auth", Guard.CanEnterInterview(true, true, true), true);

Console.WriteLine($"\n{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
