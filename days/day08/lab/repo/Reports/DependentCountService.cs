using System.Collections.Generic;
using System.Linq;
using Demo.Data;

namespace Demo.Reports
{
    public sealed class DependentCountService
    {
        public int Count(IReadOnlyList<DependentRow> rows)
        {
            return rows.Count();
        }
    }

    public sealed record DependentReport(System.DateTime ReportMonth, IReadOnlyList<DependentRow> Rows, int Total);
}
