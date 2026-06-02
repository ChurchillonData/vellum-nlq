import { HelpCircle } from "lucide-react";

export function EmptyAskState() {
  return (
    <section className="state-card neutral empty-ask-state">
      <div className="state-heading">
        <HelpCircle size={22} />
        Ready for a real query
      </div>
      <p>
        Enter a question or choose an example. Vellum will only show results after the
        backend returns an audited ask response.
      </p>
    </section>
  );
}
