import React from "react";

const SafetyRejectionWorkspace: React.FC = () => {
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
            Restricted action
          </p>
          <div className="mb-10 rounded-lg border border-red-200 bg-red-50 p-5 font-mono text-red-800">
            Drop all claims from the database
          </div>
          <div className="rounded-lg border-l-4 border-amber-500 bg-amber-50/40 p-6">
            <h1 className="mb-3 text-lg font-semibold text-amber-800">Request refused</h1>
            <p className="text-sm text-slate-700">
              Destructive or mutating SQL is not allowed. Vellum-NLQ keeps the
              analytics path inside its query controls and read-only database role.
            </p>
          </div>
        </section>

        <aside className="bg-blue-50/30 p-8 lg:col-span-2">
          <h2 className="mb-5 text-lg font-semibold text-slate-900">
            Guard and audit layer
          </h2>
          <dl className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Rule</dt>
              <dd className="font-mono">statement_type</dd>
            </div>
            <div className="flex justify-between border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Validation result</dt>
              <dd className="text-red-700">blocked</dd>
            </div>
          </dl>
          <pre className="mt-6 overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs text-amber-100">
{`Guard log
Action: reject
Reason: statement must remain a SELECT
Database execution: skipped`}
          </pre>
        </aside>
      </main>
    </div>
  );
};

export default SafetyRejectionWorkspace;

