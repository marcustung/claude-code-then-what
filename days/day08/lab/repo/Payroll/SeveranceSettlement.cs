using System;
using Demo.Data;

namespace Demo.Payroll
{
    public sealed class SeveranceSettlement
    {
        private readonly DependentRepository _repo;
        public SeveranceSettlement(DependentRepository repo) { _repo = repo; }

        public int DependentsAtTermination(int companyId, int employeeId, DateTime terminationDate)
        {
            var rows = _repo.ListEffectiveInPeriod(companyId, employeeId, terminationDate, terminationDate);
            return rows.Count;
        }
    }
}
