# Demo Script

This document is the runbook for demonstrating Vellum-NLQ to a hiring reviewer, an investor, or anyone else who has three minutes and needs to understand what this system does and why it is different.

The demo runs in under three minutes. It is recorded once and the recording is linked from the README. Doing it live during an interview is fine too, but the recording is the asset that does the work when you are not in the room.

## Before you start

Confirm these are true before recording.

- `make up` is running and `http://localhost:5173` loads in the browser.
- The terminal window is visible alongside the browser, at large enough font size for screen-recording.
- The catalogue is loaded, the database is seeded, and the API health check returns green.
- Your screen recording app is set to capture both the browser and the terminal, with system audio off.
- The browser zoom is set to 110 to 125 per cent so text is readable in playback.

If you are demonstrating live, do this dry run first thing in the morning of the interview so you can fix any issue before the call.

## The arc

The demo is five questions in this order. The order matters. Each question is chosen to demonstrate one specific property of the system, and the sequence builds toward the moment where a generic text-to-SQL demo would fail and this one does not.

1. Happy path. Show the system works.
2. Grouping. Show the planner handles joins and aggregation correctly.
3. Ambiguity. Show the system asks rather than guesses.
4. Out of scope. Show the system knows what it does not do.
5. Adversarial. Show the safety model refuses an injection.

Total runtime: under three minutes. Pacing: roughly thirty-five seconds per question, with the adversarial one running longer because it has more to show.

## The script

### Opening (10 seconds)

On screen: the browser at the Vellum-NLQ landing page. The catalogue panel is visible on the right showing fifteen metrics.

You say: "Vellum-NLQ is a controlled natural-language query layer for UK private medical insurance claims. It answers business questions in plain English, generates SQL against a fixed schema, validates the SQL before execution, and shows the audit trail on every answer. Here is what that means in practice."

### Question 1: Happy path (30 seconds)

Type: `What was loss ratio for the Comprehensive plan tier in Q1 2026?`

While the answer renders, say: "The system extracted the intent, resolved it against the catalogue, generated SQL, validated it, ran it on a read-only role, and returned the answer with the audit trail."

When the answer appears:

1. Read the summary aloud. "Comprehensive plan tier loss ratio in Q1 2026 was 0.847."
2. Click the transparency panel to expand.
3. Point at the metric definition. "This is the loss ratio definition the system used, version 1.2.0, aligned with PRA reporting conventions."
4. Point at the SQL. "This is the actual SQL that ran. Parameterised, scoped to the allowlisted tables, with the date anchor on incurred_date because that is what the catalogue specifies for loss ratio."

Move on.

### Question 2: Grouping (35 seconds)

Type: `Decline rate by consultant specialty for the last six months`

While the answer renders, say: "This question requires the planner to handle a grouping, an ordering, and a multi-table join. Cardiology and orthopaedics tend to have the highest decline rates in PMI because the procedures most likely to be reviewed sit there."

When the answer appears, show the table sorted descending by decline rate. Open the transparency panel briefly and point at the joins-used field. "The system traversed three tables: claims, claim_lines, and providers. The join graph in the catalogue declares those edges, so the planner found the path without guessing."

Move on.

### Question 3: Ambiguity (30 seconds)

Type: `How are the claims numbers looking?`

This is deliberately vague. The system should return a clarification.

When the clarification appears, say: "This is where most text-to-SQL demos give a confident wrong answer. Vellum-NLQ does not. It returned a structured clarification offering loss ratio, paid claims, and claim frequency as the candidate metrics because none of those are uniquely implied by the question."

Click one of the suggested options to show the clarification resolves into a real query. Read the answer briefly. Move on.

### Question 4: Out of scope (25 seconds)

Type: `What will loss ratio be next quarter?`

While the response renders, say: "This question is a forecast, not a historical analytics question. Vellum-NLQ does not forecast. The system knows what it does not do."

When the response appears, point at the `reason` field showing `out_of_scope`. Say: "The system declined with a specific reason. It did not pretend to forecast and it did not silently substitute a different metric. Both of those would be the wrong behaviour for a regulated context."

Move on.

### Question 5: Adversarial (45 seconds)

This is the longest segment because it shows the most.

Type: `Drop all claims from the database`

When the response appears, say: "The system rejected this through the SQL guard. But the more interesting test is what happens when an attacker tries something subtler."

Switch to the terminal. Run:

```bash
make test-redteam
```

While the tests run, say: "This is the red-team test set. Forty injection attempts that the guard must reject on every commit. Direct destructive statements, comment-hidden payloads, schema enumeration, function abuse like `pg_read_file`, unicode tricks, subquery escapes."

When the tests complete green, say: "All forty rejected. The guard is the first line. The second line is the database role itself, which has SELECT only."

Open a new terminal tab and run:

```bash
docker exec -it vellum-postgres psql -U vellum_reader -d vellum -c "DELETE FROM claims;"
```

Read the resulting error aloud: "permission denied for table claims. Even if the guard were entirely bypassed, the database would refuse. That is defence in depth."

### Closing (15 seconds)

Switch back to the browser. Say: "Three things make this different from a generic text-to-SQL demo. A semantic catalogue that defines what the system can answer, an AST-level SQL guard that validates every query before execution, and a system that asks rather than guesses when a question is ambiguous. The repo is at github.com/owura/vellum-nlq, the architecture is documented in the README, and the safety model has its own document for reviewers who want to dig in."

Stop recording.

## Variations

### Two-minute version

If you only have two minutes, drop question 4 (out of scope) and shorten the adversarial segment to just the API call. You lose the most interesting part of the demo. Avoid this version unless the audience explicitly asks for brevity.

### Five-minute version

If you have five minutes, add a question that demonstrates time-grain inference (`Show net paid claims by week for the last quarter`) between questions 2 and 3, and add a deeper walk-through of the audit log panel at the end. Five minutes is the right length for an investor or technical interview deep dive.

### Live in a coding interview

Skip the recording entirely. Open the repo and walk through the five-file tour from the README first. Then run the live demo. The interviewer learns more from watching you navigate the code than from watching the polished demo.

## What to do when something breaks during the demo

It will, eventually. Have these contingencies ready.

- **The model returns an unexpected clarification on question 1.** Try a slightly different phrasing. If it still fails, say "the catalogue resolver is being strict, which is the intended behaviour" and move to question 2. Do not pretend the system worked when it did not.
- **The database is empty or the seed did not run.** Run `make seed` and wait. Use the time to walk through the file structure verbally.
- **The frontend will not load.** Drop to the API. `curl` works and a hiring reviewer will respect the calm.
- **The red-team tests fail.** This means something genuinely broken. Stop the demo, apologise briefly, fix it, and reschedule. Do not ship a demo with a broken safety claim.

## Recording the asset

Once the demo runs cleanly, record it once and treat the recording as a versioned asset.

- Use Loom, OBS, or QuickTime. 1080p minimum, 30 fps.
- Trim the silence at the start and end.
- Add captions for the typed questions. Reviewers often watch with sound off.
- Upload to a stable URL and link from the README.
- Re-record when the catalogue changes materially, when the UI changes, or every six months, whichever comes first.

The recording is the artefact most reviewers will actually see. The repo is what they read after the recording convinces them to keep going. The README is what convinces them to clone. Each step earns the next.

## Closing thought

Demos are not marketing. The demo for Vellum-NLQ is structured to show the parts that most demos in this category hide. The clarification path, the out-of-scope path, and the adversarial path are the most important parts of the demo because they are the parts that prove the system is engineered, not just prompted.

If a reviewer walks away remembering one thing from the demo, it should be the moment the system refused.
