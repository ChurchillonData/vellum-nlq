# Frontend Mockups

These files are design references for the future production frontend. They are
kept outside `frontend/` so mockup code does not become application code by
accident.

## Reference Pages

- `page 1.jpeg` and `pages/AnswerWorkspace.tsx`
- `page 2.jpeg` and `pages/ClarificationWorkspace.tsx`
- `page 3.jpeg` and `pages/SafetyRejectionWorkspace.tsx`
- `page 4.jpeg` and `pages/CatalogueExplorer.tsx`

## Production Notes

- Keep the split Ask workspace and the catalogue explorer information hierarchy.
- Render SQL and parameters from the backend. Production SQL must reflect the
  parameterised query path, not inline mockup literals.
- Replace mockup metric versions, owner names, dimensions, and formulas with
  catalogue-backed data when the real frontend is built.
- Use backend reason codes for clarification and safety states. Show confidence
  only if the backend exposes a value that is meaningful to users.
- Describe database protection as a read-only role unless the application later
  adds a real read replica.

