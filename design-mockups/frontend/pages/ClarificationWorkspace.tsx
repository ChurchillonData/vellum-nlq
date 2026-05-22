import React from "react";

const ClarificationWorkspace: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 font-sans antialiased">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between">
          <div className="flex items-center gap-10">
            <span className="text-xl font-semibold text-slate-900">Vellum-NLQ</span>
            <nav className="flex gap-6 text-sm font-medium">
              <span className="border-b-2 border-blue-600 pb-1 text-blue-700">Ask</span>
              <span>Catalogue</span>
              <span>Audit</span>
            </nav>
          </div>
          <span className="text-sm text-teal-700">health-uk active</span>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] grid-cols-1 lg:grid-cols-5">
        <section className="border-r border-slate-200 bg-white p-8 lg:col-span-3">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">
            Natural language query
          </p>
          <div className="mb-8 rounded-lg border border-teal-100 bg-teal-50/40 p-5">
            How are the claims numbers looking?
          </div>
          <div className="rounded-lg border-l-4 border-amber-500 bg-amber-50/50 p-6">
            <h1 className="mb-2 text-lg font-semibold text-slate-900">
              Clarification needed
            </h1>
            <p className="mb-5 text-sm text-slate-700">
              Claims numbers can refer to multiple business metrics. Select the
              intended KPI.
            </p>
            <div className="grid gap-3 md:grid-cols-3">
              {["Loss Ratio", "Paid Claims (GBP)", "Claim Frequency"].map((label) => (
                <button
                  className="rounded-lg border border-slate-200 bg-white p-4 text-left text-sm font-medium text-slate-800"
                  key={label}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </section>

        <aside className="bg-blue-50/30 p-8 lg:col-span-2">
          <h2 className="mb-5 text-lg font-semibold text-slate-900">Resolution state</h2>
          <dl className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Query analysis</dt>
              <dd className="text-amber-700">ambiguous metric</dd>
            </div>
            <div className="flex justify-between border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Candidate metrics</dt>
              <dd className="font-mono text-xs">loss_ratio, paid_claims, claim_frequency</dd>
            </div>
          </dl>
          <pre className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-4 text-xs text-slate-500">
{`-- No SQL generated until the metric is resolved.
-- Select a metric to build the deterministic query.`}
          </pre>
        </aside>
      </main>
    </div>
  );
};

export default ClarificationWorkspace;

