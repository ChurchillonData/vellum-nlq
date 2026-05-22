import React from "react";

const AnswerWorkspace: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 font-sans antialiased">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-3">
          <div className="flex items-center gap-10">
            <span className="text-xl font-semibold tracking-tight text-slate-800">
              Vellum-NLQ
            </span>
            <nav className="flex gap-6 text-sm font-medium">
              <span className="border-b-2 border-teal-600 pb-1 text-teal-700">Ask</span>
              <span className="text-slate-500">Catalogue</span>
              <span className="text-slate-500">Audit</span>
            </nav>
          </div>
          <div className="flex items-center gap-5 text-xs text-slate-600">
            <span className="rounded border border-slate-200 bg-white px-3 py-2">
              health-uk <span className="ml-2 text-teal-700">active</span>
            </span>
            <span className="text-teal-700">operational</span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] grid-cols-1 lg:grid-cols-5">
        <section className="border-r border-slate-200 bg-white p-6 md:p-8 lg:col-span-3">
          <label className="mb-2 block text-xs font-semibold uppercase text-slate-500">
            Natural language query
          </label>
          <div className="mb-3 flex items-start gap-3">
            <div className="flex-1 rounded-lg border border-teal-100 bg-teal-50/40 px-4 py-5 text-sm text-slate-800">
              What was loss ratio for the Comprehensive plan tier in Q1 2026?
            </div>
            <button className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-medium text-white">
              Run
            </button>
          </div>
          <div className="mb-8 flex flex-wrap gap-2 text-xs text-slate-600">
            <span className="rounded border border-slate-200 px-3 py-2">
              loss ratio by plan tier
            </span>
            <span className="rounded border border-slate-200 px-3 py-2">
              average claim amount per member
            </span>
          </div>

          <h2 className="mb-3 text-sm font-semibold uppercase text-slate-600">
            Result summary
          </h2>
          <div className="rounded-lg border border-blue-100 bg-blue-50/30 p-5">
            <p className="mb-5 text-base text-slate-800">
              Comprehensive plan tier loss ratio in Q1 2026 was{" "}
              <span className="font-semibold text-blue-700">0.847</span> (84.7%).
            </p>
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-600">
                  <th className="py-3">Quarter</th>
                  <th className="py-3">Plan Tier</th>
                  <th className="py-3">Loss Ratio</th>
                </tr>
              </thead>
              <tbody>
                <tr className="text-slate-800">
                  <td className="py-3 font-mono">2026 Q1</td>
                  <td className="py-3">Comprehensive</td>
                  <td className="py-3 font-mono">0.847</td>
                </tr>
              </tbody>
            </table>
            <p className="mt-4 text-xs text-slate-500">
              1 row. Based on incurred claims and earned premium.
            </p>
          </div>
        </section>

        <aside className="bg-blue-50/30 p-6 md:p-8 lg:col-span-2">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800">Trust and transparency</h2>
            <span className="rounded border border-emerald-200 px-2 py-1 text-xs text-emerald-700">
              validated
            </span>
          </div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-200 pb-2">
              <dt className="text-slate-500">Metric used</dt>
              <dd className="font-mono">loss_ratio</dd>
            </div>
            <div className="flex justify-between border-b border-slate-200 pb-2">
              <dt className="text-slate-500">Metric version</dt>
              <dd className="font-mono">1.2.0</dd>
            </div>
            <div className="flex justify-between border-b border-slate-200 pb-2">
              <dt className="text-slate-500">Time anchor</dt>
              <dd className="font-mono">claims.incurred_date</dd>
            </div>
            <div className="flex justify-between border-b border-slate-200 pb-2">
              <dt className="text-slate-500">Validation result</dt>
              <dd className="text-emerald-700">11 rules checked</dd>
            </div>
          </dl>
          <h3 className="mb-2 mt-6 text-xs font-semibold uppercase text-slate-500">
            Generated SQL
          </h3>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">
{`SELECT
  SUM(claim_loss.incurred_loss) / SUM(premium_data.total_premium)
    AS loss_ratio
FROM claim_loss
JOIN premium_data USING (member_id);`}
          </pre>
        </aside>
      </main>
    </div>
  );
};

export default AnswerWorkspace;

