# Morning Briefing — July 19, 2026

## Recent Build Cycles

- **Loop setup and scope:** The brain/worker loop was verified end to end, the interview gate was explicitly waived, the 12-lesson v1 path was locked, and the founder approved build start with a content-model-first sequence.
- **Content model and curriculum:** A validated static JSON lesson model was defined with L01 as the fixture. L02–L12 were then authored across four units, completing the full beginner curriculum. Practice types were moved into the manifest and checked against every lesson.
- **Backend foundation:** FastAPI now serves the curriculum and lessons, grades completions, unlocks progression, and persists completion state in SQLite. Connection handling was hardened with explicit closes.
- **Learning app:** The SwiftUI app gained a two-tab shell, curriculum Home screen, lesson detail flow, exercises, completion feedback, retry states, and navigation. The complete learning loop is usable in the iPhone simulator.
- **AI coaching:** The pipeline was designed around normalized transcript input, structured Anthropic diagnosis, deterministic lesson routing, safety/privacy handling, and stored reports. The text backend and consent-gated iOS Coaching UI now support diagnosis, evidence-backed reports, lesson recommendations, history, detail, and deletion.
- **Live-run fixes:** The first real launch exposed two runtime issues that tests missed: legacy letterboxed mode from a missing launch-screen setting, and a blank Home screen caused by attaching the load task to an empty view. Both are fixed, and the app rendered all four units with progress persisting.

## Current State

- **Content:** The v1 content model is stable enough for the full authored set. All 12 lessons validate and are served through the manifest-backed API. One naming mismatch is recorded: L09 is `Read the room` in the enforced manifest while the planning document says `Notice interest and boundaries`.
- **Backend:** Curriculum, lesson completion, progression, SQLite persistence, and the coaching text path are implemented. Coaching reports preserve their original recommendation kind, so later lesson completion does not rewrite historical recommendations. v1 still uses caller-supplied `user_id` and has no authentication.

## Test Status

- Backend suites progressed from **10 passed** to **12 passed** for curriculum work, then to **26 passed, 1 skipped** and finally **27 passed, 1 skipped** after coaching and its regression fix. The skip is the opt-in live Anthropic smoke test.
- iOS generation, builds, and build-for-testing succeeded. Brain-run simulator checks reached **4**, then **10**, then **16 XCTest tests green**. Some worker sandbox attempts could not execute simulator tests because CoreSimulatorService/simdiskimaged was unavailable; no failing application tests were reported.

## Human Decision Needed

Fable paused the autonomous loop because the remaining coaching work is founder-gated. To continue, the founder must confirm that a test `ANTHROPIC_API_KEY` is safely available in the local environment so the real text-diagnosis smoke test can run. The screenshot-coaching path also needs founder-provided, consented real chat screenshots; those examples are required to evaluate quality before pinning the vision model. Without those inputs, the brain needs either a new founder-independent product/design direction or explicit approval to proceed with mocked screenshot work only.
