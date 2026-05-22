import React, { useState } from "react";

type Metric = {
  id: string;
  label: string;
  definition: string;
  formula: string;
  version: string;
  timeAnchor: string;
};

const metrics: Metric[] = [
  {
    id: "loss_ratio",
    label: "Loss Ratio",
    definition: "Incurred claims divided by earned premium.",
    formula: "SUM(claims.net_incurred_amount) / SUM(premium.earned_amount)",
    version: "1.2.0",
    timeAnchor: "claims.incurred_date",
  },
  {
    id: "paid_claims",
    label: "Paid Claims",
    definition: "Claim payments posted in the selected period.",
    formula: "SUM(claim_lines.net_paid_amount)",
    version: "1.0.0",
    timeAnchor: "claim_lines.paid_date",
  },
  {
    id: "claim_frequency",
    label: "Claim Frequency",
    definition: "Claims per thousand member months.",
    formula: "COUNT(DISTINCT claims.id) / SUM(enrolment_months.member_months)",
    version: "1.0.0",
    timeAnchor: "claims.incurred_date",
  },
];

const CatalogueExplorer: React.FC = () => {
  const [selectedId, setSelectedId] = useState("loss_ratio");
  const selected = metrics.find((metric) => metric.id === selectedId) ?? metrics[0];

  return (
    <div className="min-h-screen bg-slate-50 font-sans antialiased">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between">
          <div className="flex items-center gap-10">
            <span className="text-xl font-semibold text-slate-900">Vellum-NLQ</span>
            <nav className="flex gap-6 text-sm font-medium">
              <span>Ask</span>
              <span className="border-b-2 border-teal-600 pb-1 text-teal-700">
                Catalogue
              </span>
              <span>Audit</span>
            </nav>
          </div>
          <span className="text-sm text-teal-700">health-uk active</span>
        </div>
      </header>

      <main className="mx-auto flex max-w-[1600px] flex-col bg-white md:flex-row">
        <aside className="w-full border-r border-slate-200 p-5 md:w-72">
          <h2 className="mb-4 text-xs font-semibold uppercase text-slate-500">
            Metric registry
          </h2>
          <div className="space-y-2">
            {metrics.map((metric) => (
              <button
                className={`block w-full rounded-lg border px-4 py-4 text-left ${
                  metric.id === selected.id
                    ? "border-teal-200 bg-teal-50 text-teal-900"
                    : "border-transparent text-slate-700 hover:bg-slate-50"
                }`}
                key={metric.id}
                onClick={() => setSelectedId(metric.id)}
              >
                <span className="block font-medium">{metric.label}</span>
                <span className="block font-mono text-xs">{metric.id}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="flex-1 p-6 md:p-8">
          <h1 className="text-3xl font-semibold text-slate-900">{selected.label}</h1>
          <p className="mt-2 text-slate-600">{selected.definition}</p>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div>
              <h2 className="text-xs font-semibold uppercase text-teal-700">Formula</h2>
              <pre className="mt-2 overflow-x-auto rounded-lg bg-teal-50 p-4 text-sm">
                {selected.formula}
              </pre>
            </div>
            <div>
              <h2 className="text-xs font-semibold uppercase text-teal-700">
                Time anchor
              </h2>
              <p className="mt-2 font-mono text-sm">{selected.timeAnchor}</p>
              <h2 className="mt-6 text-xs font-semibold uppercase text-teal-700">
                Version
              </h2>
              <p className="mt-2 font-mono text-sm">{selected.version}</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default CatalogueExplorer;
