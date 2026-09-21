using System;
using System.Collections.Generic;

namespace Demo.Data
{
    // 教學示範 repo：扶養親屬主檔的兩支查詢。名稱、欄位皆為示例，非公司程式。
    public sealed class DependentRow
    {
        public int EmployeeId { get; set; }
        public string Name { get; set; } = "";
        public DateTime EffectiveFrom { get; set; }
        public DateTime? EffectiveTo { get; set; }
    }

    public sealed class DependentRepository
    {
        private readonly IDbExecutor _db;
        public DependentRepository(IDbExecutor db) { _db = db; }

        public IReadOnlyList<DependentRow> ListForPayrollGroup(int companyId, int employeeId, int payrollGroupId)
        {
            const string sql = @"
                SELECT d.EmployeeId, d.Name, d.EffectiveFrom, d.EffectiveTo
                FROM Dependent d
                JOIN Employee e ON e.Id = d.EmployeeId
                WHERE e.CompanyId = @companyId
                  AND d.EmployeeId = @employeeId
                  AND e.PayrollGroupId = @payrollGroupId";
            return _db.Query<DependentRow>(sql, new { companyId, employeeId, payrollGroupId });
        }

        public IReadOnlyList<DependentRow> ListEffectiveInPeriod(int companyId, int employeeId, DateTime periodStart, DateTime periodEnd)
        {
            const string sql = @"
                SELECT d.EmployeeId, d.Name, d.EffectiveFrom, d.EffectiveTo
                FROM Dependent d
                JOIN Employee e ON e.Id = d.EmployeeId
                WHERE e.CompanyId = @companyId
                  AND d.EmployeeId = @employeeId
                  AND d.EffectiveFrom <= @periodEnd
                  AND (d.EffectiveTo IS NULL OR d.EffectiveTo >= @periodStart)";
            return _db.Query<DependentRow>(sql, new { companyId, employeeId, periodStart, periodEnd });
        }
    }

    public interface IDbExecutor
    {
        IReadOnlyList<T> Query<T>(string sql, object parameters);
    }
}
