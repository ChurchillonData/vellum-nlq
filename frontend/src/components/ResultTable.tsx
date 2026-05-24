type ResultTableProps = {
  rows: Record<string, unknown>[];
};

export function ResultTable({ rows }: ResultTableProps) {
  if (!rows.length) {
    return <p className="empty-table">No rows returned.</p>;
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="table-frame">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{humanize(column)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{formatCell(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function humanize(value: string) {
  return value.replace(/_/g, " ");
}

function formatCell(value: unknown) {
  if (typeof value === "number") {
    return value < 1 ? value.toFixed(3) : value.toLocaleString();
  }

  return String(value ?? "");
}
