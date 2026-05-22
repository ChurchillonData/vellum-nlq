# Codebase Standards

Vellum-NLQ should be easy for a junior or mid-level data scientist to read,
change, test, and extend.

## Python

- Prefer small modules with one clear responsibility.
- Prefer plain functions and typed data models over clever abstractions.
- Keep scripts short. Split a script when setup, domain logic, and I/O become
  hard to scan together.
- Add concise docstrings to public modules, classes, and functions when their
  purpose or inputs are not obvious from the name.
- Use names that describe the business meaning, not only the implementation.
- Validate inputs close to the boundary and raise errors that explain what must
  be fixed.
- Keep LLM code behind a narrow provider boundary. Core catalogue, planning,
  SQL, and safety logic must stay testable without an API call.

## Tests

- Add focused tests beside each new behavior.
- Prefer small fixtures that show the business case under test.
- Use integration tests when behavior crosses the database, API, or catalogue
  boundary.

## Repository Hygiene

- Do not keep dead scripts, unused experiments, or duplicate helpers in the
  main tree.
- Do not add files for hypothetical future work before the next phase needs
  them.
- Remove generated files and temporary artifacts unless they are intentionally
  versioned assets.
- Keep documentation aligned with what exists today and what is still a target.
