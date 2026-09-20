using System;

public static class Guard
{
    public static bool CanEnterInterview(bool rejected, bool reopenRequested, bool authorized)
    {
        if (rejected && !(reopenRequested && authorized))
            return false;

        return true;
    }
}
