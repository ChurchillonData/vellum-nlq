export function HighlightedAnswer({ text }: { text: string }) {
  const parts = text.split(/(0\.\d{3}|\d{1,3}\.\d%)/g);

  return (
    <>
      {parts.map((part, index) =>
        /^(0\.\d{3}|\d{1,3}\.\d%)$/.test(part) ? (
          <strong
            className={part.endsWith("%") ? "answer-percent" : "answer-number"}
            key={`${part}-${index}`}
          >
            {part}
          </strong>
        ) : (
          part
        )
      )}
    </>
  );
}
