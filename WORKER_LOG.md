# Worker Log — SmallTalkCoach build loop

Append-only. Every Codex worker appends exactly one entry per task, after
finishing — whether the task succeeded, partially succeeded, or got blocked.
Never edit or delete earlier entries. The brain reads the recent tail at
every cycle start and reviews the newest entry as part of accepting the
task. Enforced by `.claude/skills/brain-worker-loop/worker.sh`, which exits
with code 4 (automatic reject) when a worker finishes without appending.

Entry format (keep an entry under ~15 lines):

```
## YYYY-MM-DD HH:MM UTC — <task title>
- **Model:** gpt-5.6-terra | gpt-5.6-luna
- **Status:** done | partial | blocked
- **What was done:** <1–3 lines>
- **Files touched:** <paths>
- **Result / verification:** <tests run and their real outcomes — never fabricated>
- **Open issues:** <anything the brain should know; "none" if none>
```

---

## 2026-07-18 10:28 UTC — Align README intro with v1 architecture
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Rewrote only the README opening product description to
  reflect v1's Home and AI Coaching tabs and the unimplemented v1 UI.
- **Files touched:** README.md; WORKER_LOG.md
- **Result / verification:** Reviewed the README diff against ARCHITECTURE.md;
  the architecture pointer and placeholder-name paragraph are preserved.
- **Open issues:** none

## 2026-07-18 14:34 UTC — Fix stale brain-worker loop repository paths
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Replaced the two stale repository paths in the loop
  protocol examples with the current repository path.
- **Files touched:** .claude/skills/brain-worker-loop/SKILL.md; WORKER_LOG.md
- **Result / verification:** `git diff --check` passed; the tracked stale-path
  scan returned no matches; the SKILL.md diff contains only the two path substitutions.
- **Open issues:** none

## 2026-07-18 14:37 UTC — Define v1 lesson path and sync build gate
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the locked 12-lesson newcomer beginner path with
  routing, assumptions, non-goals, and deferrals; synced the two stale scope gates.
- **Files touched:** docs/planning/LESSON_PATH_V1.md; docs/planning/ORCHESTRATION.md;
  .claude/skills/brain-worker-loop/SKILL.md; WORKER_LOG.md
- **Result / verification:** `git diff --check` passed; structural checks found
  12 lessons and 12 ids, completion checks, and dimension mappings; each lesson id
  appears in the routing table.
- **Open issues:** none

## 2026-07-18 14:57 UTC — Define lesson content model and author L01 fixture
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the v1 static JSON lesson schema and a complete
  L01 authored fixture; synchronized the two stale build-scope statements.
- **Files touched:** docs/planning/CONTENT_MODEL_V1.md;
  content/lessons/l01-first-hello.json; docs/planning/ORCHESTRATION.md;
  .claude/skills/brain-worker-loop/SKILL.md; WORKER_LOG.md
- **Result / verification:** `python3 -m json.tool` parsed the L01 fixture;
  metadata/content-block assertions and `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 15:07 UTC — Build backend skeleton and curriculum serving
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the validated lesson-path manifest, FastAPI
  curriculum/lesson/completion endpoints, sqlite completion storage, and tests.
- **Files touched:** backend/; content/lesson_path.json; .gitignore; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  10 passed, 1 warning in 0.37s; `git diff --check` passed.
- **Open issues:** No authentication in v1; README documents caller-supplied user_id.

## 2026-07-18 15:12 UTC — Author Unit 1 lessons L02 and L03
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Authored the locked L02 and L03 lessons with setting-led
  exercises, practice, and deterministic plus deferred completion checks; updated content/API tests for all authored lessons.
- **Files touched:** content/lessons/l02-use-the-setting.json; content/lessons/l03-easy-first-question.json; backend/tests/test_content.py; backend/tests/test_api.py; WORKER_LOG.md
- **Result / verification:** Both JSON files parsed with `python3 -m json.tool`; `backend/.venv/bin/python -m pytest backend/tests -q`: 10 passed, 1 warning in 0.37s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 15:17 UTC — Author Unit 2 lessons L04 through L06
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Authored L04–L06 with turn-balance, evidence-spotting,
  and branching-response checks; updated the content/API test expectations for six authored lessons.
- **Files touched:** content/lessons/l04-answer-and-return.json; content/lessons/l05-show-you-heard.json; content/lessons/l06-follow-the-thread.json; backend/tests/test_content.py; backend/tests/test_api.py; WORKER_LOG.md
- **Result / verification:** All three JSON files parsed with `python3 -m json.tool`; metadata exactly matched the manifest; `backend/.venv/bin/python -m pytest backend/tests -q`: 10 passed, 1 warning in 0.35s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 15:23 UTC — Author Unit 3 lessons L07 through L09
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Authored L07–L09 with balance, scenario-judgment, and
  evidence-and-boundary checks; updated content/API expectations for nine authored lessons.
- **Files touched:** content/lessons/l07-share-and-make-space.json; content/lessons/l08-handle-the-pause.json; content/lessons/l09-read-the-room.json; backend/tests/test_content.py; backend/tests/test_api.py; WORKER_LOG.md
- **Result / verification:** All three JSON files parsed with `python3 -m json.tool`; the validating loader accepted them; `backend/.venv/bin/python -m pytest backend/tests -q`: 10 passed, 1 warning in 0.39s; `git diff --check` passed.
- **Open issues:** L09 uses the loader-enforced manifest title `Read the room`; the planning document’s L09 title line says `Notice interest and boundaries`.

## 2026-07-18 15:30 UTC — Author Unit 4 lessons L10 through L12 and complete curriculum tests
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Authored L10–L12 with topic-thread, exit-quality, and
  specificity-and-pressure checks; L12 explicitly accepts declining or uncertainty without pursuit.
  Restructured API coverage for the completed 12-lesson path and a synthetic content-pending case.
- **Files touched:** content/lessons/l10-build-on-common-ground.json; content/lessons/l11-end-warmly.json; content/lessons/l12-make-continuity-easy.json; backend/tests/test_content.py; backend/tests/test_api.py; WORKER_LOG.md
- **Result / verification:** All three JSON files parsed with `python3 -m json.tool`; the validating loader accepted 12 lessons; `backend/.venv/bin/python -m pytest backend/tests -q`: 11 passed, 1 warning in 0.44s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 15:33 UTC — Harden sqlite closes and manifest practice types
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Wrapped every per-call sqlite connection in explicit closing
  contexts while preserving transactions; moved all twelve practice types into
  the manifest and validated authored lesson practice types against it.
- **Files touched:** backend/app/store.py; backend/app/content.py;
  content/lesson_path.json; docs/planning/CONTENT_MODEL_V1.md;
  backend/tests/test_content.py; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  12 passed, 1 warning in 0.43s; a direct manifest-to-lesson check matched all
  12 practice types; `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 16:32 UTC — Build iOS two-tab curriculum scaffold
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added the xcodegen iOS project, Home and AI Coaching tab shell,
  typed API models/client, curriculum Home UI, and four focused XCTest cases.
- **Files touched:** ios/project.yml; ios/SmallTalkCoach/; ios/SmallTalkCoachTests/;
  ios/README.md; WORKER_LOG.md
- **Result / verification:** `xcodegen generate` and the required generic-simulator
  `xcodebuild build` succeeded; `build-for-testing` also succeeded. The required
  iPhone 16 test command could not run: CoreSimulatorService returned connection refused.
- **Open issues:** Tests were written and compiled but not executed; run them on a host
  with the iPhone 16 / iOS 18.2 simulator service available.

## 2026-07-18 16:43 UTC — Design v1 AI Coaching pipeline
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the build-ready Messages-API coaching pipeline
  contract: normalized transcript, structured diagnosis, deterministic manifest
  routing, API/error shapes, safety/privacy boundaries, and test plan.
- **Files touched:** docs/planning/COACHING_PIPELINE_V1.md; WORKER_LOG.md
- **Result / verification:** Reviewed against the required architecture, brief,
  routing manifest, decisions, and backend service; 7 required sections present,
  document is 350 lines, and whitespace validation reported no errors.
- **Open issues:** Exact model ids require current API-doc review and vision-model
  pinning remains gated on the required real-chat-screenshot quality evaluation.

## 2026-07-18 16:51 UTC — iOS lesson detail and completion-check flow
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added navigable unlocked/completed lesson rows, a six-block
  SwiftUI lesson detail view, local exercise/free-draft state, and protocol-backed
  completion submission with success, feedback, and retry states.
- **Files touched:** ios/SmallTalkCoach/APIClient.swift; ios/SmallTalkCoach/HomeView.swift;
  ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/LessonDetailView.swift;
  ios/SmallTalkCoach/LessonDetailViewModel.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `xcodegen generate --spec ios/project.yml --project ios`, the
  generic-simulator `xcodebuild build`, and `build-for-testing` all succeeded; `git diff --check`
  passed. The required iPhone 16 / iOS 18.2 `xcodebuild test` attempt could not execute tests:
  CoreSimulatorService returned `Connection refused` and no simulator runtimes were discoverable.
- **Open issues:** Run the XCTest suite on a host with CoreSimulatorService available.

## 2026-07-18 17:03 UTC — Implement text coaching backend pipeline
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added text normalization, lazy structured Anthropic diagnosis with retry/validation,
  deterministic manifest routing, report storage, coaching endpoints, safety/refusal handling, and opt-in live smoke coverage.
- **Files touched:** backend/app/transcript.py; backend/app/diagnosis.py; backend/app/routing.py;
  backend/app/coaching.py; backend/app/main.py; backend/app/store.py; backend/requirements.txt; backend/tests/; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m compileall -q backend/app` passed;
  `backend/.venv/bin/python -m pytest backend/tests -q`: 26 passed, 1 skipped, 1 warning in 0.96s; `git diff --check` passed.
- **Open issues:** The live smoke remains intentionally skipped unless both documented environment flags are set.

## 2026-07-18 20:27 UTC — Persist immutable coaching recommendation kind
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Stored the routed recommendation kind with each coaching report and
  made report reads use that immutable value; removed timestamp-based completion reconstruction.
  Added a regression test that completes the routed lesson then verifies the report remains `new`.
- **Files touched:** backend/app/store.py; backend/app/coaching.py; backend/tests/test_coaching.py; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  27 passed, 1 skipped, 1 warning in 1.18s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-18 23:40 UTC — Build iOS Coaching text diagnosis, reports, and history
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Replaced the Coaching placeholder with consent-gated pasted-text diagnosis,
  coaching-disabled and safety-guidance states, evidence-backed report/lesson navigation, and report history/detail/delete.
  Added a typed CoachingAPI seam, backend-detail error mapping, backend-shape Codable models, and injected-fake XCTest coverage.
- **Files touched:** ios/SmallTalkCoach/APIClient.swift; ios/SmallTalkCoach/Models.swift;
  ios/SmallTalkCoach/CoachingView.swift; ios/SmallTalkCoach/CoachingViewModel.swift; ios/SmallTalkCoach/RootView.swift;
  ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `xcodegen generate --spec ios/project.yml --project ios` passed; generic simulator build and
  `build-for-testing` passed; `git diff --check` passed. iPhone 16 / iOS 18.2 `xcodebuild test` was attempted but
  CoreSimulatorService/simdiskimaged is unavailable in this sandbox, so tests could not execute.
- **Open issues:** Simulator test execution needs a working CoreSimulatorService; reviewer can run the compiled tests.

## 2026-07-18 20:56 UTC — Fix generated iOS launch-screen configuration
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the app target's generated `UILaunchScreen` configuration key.
- **Files touched:** ios/project.yml; WORKER_LOG.md
- **Result / verification:** `xcodegen generate --spec ios/project.yml --project ios` and the required generic-simulator `xcodebuild build` both passed; `plutil -p` on the built app's Info.plist reported `UILaunchScreen`.
- **Open issues:** none

## 2026-07-18 21:00 UTC — Fix Home initial curriculum loading
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Moved Home's load task to NavigationStack and made both idle and nil-curriculum states visible loading UI. Reviewed CoachingView: its availability task already wraps visible content in every state, so no change was needed.
- **Files touched:** ios/SmallTalkCoach/HomeView.swift; WORKER_LOG.md
- **Result / verification:** Generic iOS Simulator `xcodebuild build` passed (`BUILD SUCCEEDED`); `git diff --check` passed. Attempted the iPhone 16/iOS 18.2 XCTest run, but CoreSimulatorService/simdiskimaged is unavailable in this sandbox, so tests could not execute.
- **Open issues:** Simulator test execution requires a working CoreSimulatorService.

## 2026-07-19 12:12 UTC — Enforce Haiku-only coaching model and simulator verification protocol
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the Haiku-only coaching model constant and source-scan regression test; inserted the mandatory iPhone 16 build, launch, screenshot, and scoped brain-fix rule in the loop protocol.
- **Files touched:** backend/app/diagnosis.py; backend/tests/test_coaching.py; .claude/skills/brain-worker-loop/SKILL.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 28 passed, 1 skipped, 1 warning in 1.42s; required forbidden-model grep over backend/app and backend/tests returned no matches; `git diff --check` passed.
- **Open issues:** none

## 2026-07-19 12:39 UTC — Implement asynchronous screenshot coaching pipeline
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added Haiku-only structured vision extraction, strict image/transcript validation, and an in-memory, ownership-scoped screenshot job/polling flow that reuses diagnosis, routing, and report storage. Added mocked coverage for validation, jobs, attribution, failures, escalation, and model locking.
- **Files touched:** backend/app/vision.py; backend/app/jobs.py; backend/app/coaching.py; backend/tests/test_coaching.py; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 41 passed, 1 skipped, 1 warning in 1.72s; `git diff --check` passed; forbidden-model scan of backend/app and backend/tests returned no matches.
- **Open issues:** none

## 2026-07-19 12:50 UTC — Build iOS screenshot coaching upload and polling flow
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added PhotosPicker screenshot composition, side selection, size-aware JPEG encoding,
  typed 202/job polling models, and consent-gated upload/poll state handling with friendly image failures.
  Added fake-client XCTest coverage for decoding, gating, polling outcomes, timeout/retry, safety, and encoding threshold.
- **Files touched:** ios/SmallTalkCoach/APIClient.swift; ios/SmallTalkCoach/CoachingView.swift;
  ios/SmallTalkCoach/CoachingViewModel.swift; ios/SmallTalkCoach/Models.swift;
  ios/SmallTalkCoach/ScreenshotImageEncoder.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `xcodegen generate`, generic-simulator `xcodebuild build`, and `build-for-testing` passed;
  `git diff --check` passed. `xcodebuild test` was attempted but CoreSimulatorService has no concrete simulator device.
- **Open issues:** XCTest execution needs an available CoreSimulatorService; tests compile and await reviewer simulator run.

## 2026-07-19 16:14 UTC — Make diagnosis validation Haiku-tolerant
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Allowed empty evidence quotes while preserving exact-substring checks; coerced over-returned improvements and strengths before reports are stored or served; tightened the diagnosis prompt and documented the Haiku-driven tolerance.
- **Files touched:** backend/app/diagnosis.py; backend/tests/test_coaching.py; docs/planning/COACHING_PIPELINE_V1.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 45 passed, 1 skipped, 1 warning in 2.07s; `git diff --check` passed; forbidden-model scan of backend/app and backend/tests returned no matches.
- **Open issues:** none

## 2026-07-19 16:45 UTC — Bind coaching to user responses
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added stimulus-only and user-reply diagnosis modes, role-bound validation and prompting, response coaching/examples/takeaway fields, focus-dimension routing, and other-party defaults for unlabeled text and unknown-side screenshots.
- **Files touched:** backend/app/transcript.py; backend/app/diagnosis.py; backend/app/routing.py; backend/app/coaching.py; backend/app/vision.py; backend/tests/test_coaching.py; docs/planning/COACHING_PIPELINE_V1.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 50 passed, 1 skipped, 1 warning in 2.32s; `backend/.venv/bin/python -m compileall -q backend/app` passed; `git diff --check` passed; forbidden-model scan of backend/app and backend/tests returned no matches.
- **Open issues:** Live smoke intentionally not run; reviewer performs live verification.

## 2026-07-19 16:49 UTC — Make diagnosis schema API-compatible
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Removed array cardinality keywords from the diagnosis schema and replaced the nullable dimensions type union with an `anyOf` object-or-null schema; existing app-side validation retains the 1–2 example-response rule.
- **Files touched:** backend/app/diagnosis.py; WORKER_LOG.md
- **Result / verification:** Schema compatibility audit passed (no unsupported array constraints or type unions); `backend/.venv/bin/python -m pytest backend/tests -q`: 50 passed, 1 skipped, 1 warning in 1.73s; forbidden-model scan returned no matches; `git diff --check` passed.
- **Open issues:** none

## 2026-07-19 16:57 UTC — Render response-oriented iOS coaching reports
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added schema-v2 diagnosis models and response-oriented report cards, including interpretation, optional reply scores, adaptable examples, and a highlighted takeaway. Updated the composer hint and added both-mode decoding/display-visibility coverage.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/CoachingView.swift;
  ios/SmallTalkCoach/CoachingViewModel.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `xcodegen generate --spec ios/project.yml --project ios`, generic-simulator `xcodebuild build`, and `build-for-testing` passed (with derived data under `/private/tmp`). `xcodebuild test` was attempted, but CoreSimulatorService has no usable simulator device in this sandbox; tests were compiled but not executed. `git diff --check` passed.
- **Open issues:** Reviewer should run the XCTest suite on an available simulator.

## 2026-07-19 17:53 UTC — Fix vision extraction schema numeric constraint
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Removed the unsupported JSON-schema `minimum` from screenshot turn indices,
  audited the remaining extraction schema constraints, and made non-negative contiguous indices explicit in app validation.
  Added negative-index coverage to the screenshot extraction validation test.
- **Files touched:** backend/app/vision.py; backend/tests/test_coaching.py; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests/test_coaching.py -q`:
  39 passed, 1 warning in 1.64s; `backend/.venv/bin/python -m pytest backend/tests -q`:
  51 passed, 1 skipped, 1 warning in 1.36s; forbidden-model scan was clean; `git diff --check` passed.
- **Open issues:** none

## 2026-07-19 18:30 UTC — Fix screenshot unreadable-transcript copy and submission-mode coverage
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added a screenshot-specific unreadable-conversation error mapped for screenshot upload and poll failures; kept text mapping unchanged. Added founder-scenario tests for screenshot-only polling failure, short-text 422, and screenshot mode with non-empty text.
- **Files touched:** ios/SmallTalkCoach/CoachingViewModel.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `xcodegen generate --spec ios/project.yml --project ios`, generic-simulator `xcodebuild build`, and `xcodebuild build-for-testing` passed; `git diff --check` passed. `xcodebuild test` was attempted but CoreSimulatorService returned connection refused/no simulator runtimes, so XCTest did not execute.
- **Open issues:** Run the compiled XCTest suite on a host with a working iPhone 16 / iOS 18.2 simulator service.

## 2026-07-20 20:42 UTC — Sync stale VISION and ARCHITECTURE status to rebuilt v1
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Updated VISION.md with post-restart/v1 status annotations and added the rebuilt-v1 banner to ARCHITECTURE.md. Added the T-A decision record without rewriting historical content.
- **Files touched:** VISION.md; ARCHITECTURE.md; DECISIONS.md; WORKER_LOG.md
- **Result / verification:** Spot-verified the cited restart, rebuild, model-lock, pipeline, and roadmap records; `git diff --check` passed before this append.
- **Open issues:** Pre-existing uncommitted PROGRESS.md change was retained; task edits touch only the four files above.

## 2026-07-20 20:53 UTC — Build vision-quality eval harness
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the isolated vision extraction eval CLI, scoring, live-mode double gate,
  synthetic mock fixtures, protected real-case directory, consent checklist, and mock-only tests.
- **Files touched:** .gitignore; backend/eval/; backend/tests/test_vision_eval.py; WORKER_LOG.md
- **Result / verification:** Synthetic mock CLI produced one pass and one intentional failure (exit 1);
  ungated live CLI refused with exit 2; `backend/.venv/bin/python -m pytest backend/tests -q`:
  57 passed, 1 skipped, 1 warning; `git diff --check` passed.
- **Open issues:** Real consented screenshots and manual failure inspection remain founder-gated.

## 2026-07-20 20:59 UTC — Harden diagnosis retries and failure logging
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Made diagnosis attempts lazily configurable (default three), retried invalid
  responses and transient provider failures, and added content-free per-attempt/exhaustion logs.
- **Files touched:** backend/app/diagnosis.py; backend/tests/test_coaching.py; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests/test_coaching.py -q`:
  46 passed, 1 warning; `backend/.venv/bin/python -m pytest backend/tests -q`:
  64 passed, 1 skipped, 1 warning; `git diff --check` passed.
- **Open issues:** none

## 2026-07-20 21:06 UTC — Add deterministic streak and Today endpoint backend
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added timezone-aware replayed streak/freeze computation from raw
  lesson completions and coaching reports, plus the next-unlocked-lesson Today endpoint.
  Added parsing, DST, freeze, malformed-row, and endpoint contract coverage.
- **Files touched:** backend/app/streak.py; backend/app/store.py; backend/app/main.py;
  backend/tests/test_streak.py; backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  72 passed, 1 skipped, 1 warning; `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 00:16 UTC — Build iOS Today card and opt-in daily reminder
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added forward-compatible streak decoding/API access, a first-section
  Today card with lesson deep links and shared curriculum/streak refresh, plus opt-in local
  reminder scheduling, persisted time/preferences, denial handling, and focused fake-backed tests.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/APIClient.swift;
  ios/SmallTalkCoach/HomeView.swift; ios/SmallTalkCoach/TodayCard.swift;
  ios/SmallTalkCoach/ReminderScheduler.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, generic-simulator `xcodebuild build`,
  and `xcodebuild build-for-testing` passed; `git diff --check` passed. iPhone 16 / iOS 18.2
  build and XCTest were attempted but CoreSimulatorService had no available runtime, so tests did not execute.
- **Open issues:** Run the compiled XCTest suite on a host with a working iPhone 16 / iOS 18.2 simulator service.

## 2026-07-20 21:24 UTC — Build deterministic longitudinal skill profile endpoint
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added pure profile aggregation of valid coaching reports and completions,
  the read-only profile store query, and `GET /users/{user_id}/profile`.
- **Files touched:** backend/app/profile.py; backend/app/store.py; backend/app/main.py;
  backend/tests/test_profile.py; backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  78 passed, 1 skipped, 1 warning; `compileall` and `git diff --check` passed.
- **Open issues:** none

## 2026-07-20 21:31 UTC — Render iOS skill profile on Home
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added profile models/API seam, a shared Home profile view model and
  summary row, profile detail sections/history/lesson deep links, and focused fake-backed tests.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/APIClient.swift;
  ios/SmallTalkCoach/HomeView.swift; ios/SmallTalkCoach/ProfileView.swift;
  ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, generic-simulator `xcodebuild build`,
  and `build-for-testing` passed using `/private/tmp` derived data; `git diff --check` passed.
  iPhone 16 / iOS 18.2 build and XCTest were attempted but CoreSimulatorService refused connections.
- **Open issues:** Run the XCTest suite on a host with a working iPhone 16 / iOS 18.2 simulator service.

## 2026-07-20 21:37 UTC — Add reflection records backend and profile aggregation
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added deterministic reflection persistence, validated lesson/report reflection APIs,
  ownership checks, and a privacy-preserving reflection summary in the profile response.
  Added coverage for API contracts, ordering, validation, profile aggregation, and streak isolation.
- **Files touched:** backend/app/store.py; backend/app/main.py; backend/app/profile.py;
  backend/tests/test_reflections.py; backend/tests/test_profile.py; backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  84 passed, 1 skipped, 1 warning in 1.91s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-20 21:47 UTC — Build iOS reflection prompt and profile copy fix
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added typed reflection submission/profile decoding, session-gated pending
  markers from completed lessons and coaching reports, Home sheet presentation, retry-safe
  prompt submission/dismissal, and singular profile-summary copy.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/APIClient.swift;
  ios/SmallTalkCoach/ReflectionPrompt.swift; ios/SmallTalkCoach/HomeView.swift;
  ios/SmallTalkCoach/LessonDetailViewModel.swift; ios/SmallTalkCoach/CoachingViewModel.swift;
  ios/SmallTalkCoach/ProfileView.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, generic-simulator `xcodebuild build`,
  and final `xcodebuild build-for-testing` passed; `git diff --check` passed. iPhone 16 destination
  build and XCTest were attempted but CoreSimulatorService had no available runtime, so XCTest did not execute.
- **Open issues:** Run the compiled XCTest suite on a host with a working iPhone 16 simulator service.

## 2026-07-20 21:53 UTC — Fix optional profile reflections decoding
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Removed the default initializer from optional `ProfileResponse.reflections`,
  restoring synthesized `decodeIfPresent`; updated the two direct test constructions with `nil`.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and generic-simulator `xcodebuild build`
  passed; `git diff --check` passed. Named iPhone 16 build/XCTest could not run: CoreSimulatorService had no runtime.
- **Open issues:** Run the XCTest suite on a host with a working iPhone 16 simulator service.

## 2026-07-20 22:01 UTC — Add deterministic spaced-repetition review backend
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added repeatable review persistence, local-day review scheduling and priority,
  review submission reusing lesson grading, review-backed streak activity, and review Today targets.
  Reordered L02 choices so its correct answers use varied indices.
- **Files touched:** backend/app/store.py; backend/app/streak.py; backend/app/review.py;
  backend/app/main.py; backend/tests/test_review.py; content/lessons/l02-use-the-setting.json;
  backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  92 passed, 1 skipped, 1 warning; `compileall`, L02 JSON parsing, and `git diff --check` passed.
- **Open issues:** none

## 2026-07-20 22:09 UTC — Surface review mode and review-due lessons on iOS
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added review queue/API models and calls, review-mode lesson submission without
  reflections, Today review targets, and Home’s three-item review-due section; added focused XCTest coverage.
- **Files touched:** ios/SmallTalkCoach/Models.swift; ios/SmallTalkCoach/APIClient.swift;
  ios/SmallTalkCoach/LessonDetailView.swift; ios/SmallTalkCoach/LessonDetailViewModel.swift;
  ios/SmallTalkCoach/TodayCard.swift; ios/SmallTalkCoach/HomeView.swift;
  ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, generic-simulator `xcodebuild build-for-testing`,
  and `git diff --check` passed. iPhone 16 destination build/XCTest were blocked by CoreSimulatorService
  connection refusal and no available runtimes.
- **Open issues:** Run XCTest on a host with a working iPhone 16 simulator service.

## 2026-07-20 22:21 UTC — T-H onboarding + baseline (Flow A), backend + iOS
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added deterministic onboarding persistence/API emphasis routing and the one-time four-step iOS flow with optional reminders, non-blocking submission, and Today focus copy.
- **Files touched:** backend/app/store.py; backend/app/main.py; backend/tests/test_onboarding.py; backend/README.md; ios/SmallTalkCoach/{OnboardingView,Models,APIClient,TodayCard,HomeView,RootView}.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 97 passed, 1 skipped; `xcodegen generate` and generic simulator `xcodebuild build-for-testing` succeeded; `git diff --check` passed.
- **Open issues:** Named iPhone 16 build/XCTest could not execute because CoreSimulatorService had no available simulator runtime.

## 2026-07-21 08:29 UTC — Truth-sync docs and answer-index audit
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Synced the shipped T-D/T-E and streak-rule VISION annotations;
  added the accept-path sibling-doc sync requirement and a real-content answer-index audit.
  Reordered L01's exercise options so its correct answers use two positions.
- **Files touched:** VISION.md; .claude/skills/brain-worker-loop/SKILL.md;
  backend/tests/test_content.py; content/lessons/l01-first-hello.json; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`:
  98 passed, 1 skipped, 1 warning; standalone real-loader audit passed for 12 lessons; `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 08:40 UTC — T-I account-wide coaching-data deletion (code)
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added idempotent, ownership-scoped deletion of coaching reports/transcripts and reflections, preserving learning data. Added the iOS destructive confirmation, typed API response, state/pending-reflection clearing, history reload, and focused fake-backed tests.
- **Files touched:** backend/app/store.py; backend/app/main.py; backend/tests/test_deletion.py; backend/README.md; ios/SmallTalkCoach/{APIClient,CoachingView,CoachingViewModel,Models}.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 102 passed, 1 skipped, 1 warning. `xcodegen generate` and generic simulator `xcodebuild build-for-testing` succeeded; `git diff --check` passed. Named iPhone 16 XCTest was attempted but CoreSimulatorService had no available runtime.
- **Open issues:** XCTest execution and simulator launch require a working CoreSimulatorService.

## 2026-07-21 08:53 UTC — Fix onboarding cover presentation state
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Replaced RootView's computed no-op presentation binding with writable state
  re-armed on appearance; completion dismisses it and swipe dismissal is disabled. Added a shared,
  tested initial-presentation decision helper covering fresh and persisted-complete defaults states.
- **Files touched:** ios/SmallTalkCoach/RootView.swift; ios/SmallTalkCoach/OnboardingView.swift;
  ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and generic-simulator
  `xcodebuild build-for-testing` passed; `git diff --check` passed. Named iPhone 16 / iOS 18.2
  build and XCTest were attempted but CoreSimulatorService refused connections before execution.
- **Open issues:** Run XCTest and repeated fresh-install relaunch verification on a host with a working simulator service.

## 2026-07-21 — T-I privacy policy, Terms of Service, and App Store privacy mapping
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added plain-language privacy and terms documents for the current anonymous-device
  data model, retention/deletion controls, Anthropic sharing, and conversation-participant caution.
  Added an App Store privacy-label mapping and audited the actual pre-submit consent copy. The audit
  records the high-priority screenshot disclosure gap without changing app code.
- **Files touched:** docs/legal/PRIVACY_POLICY.md; docs/legal/TERMS_OF_SERVICE.md;
  docs/legal/APP_STORE_PRIVACY.md; backend/README.md; WORKER_LOG.md
- **Result / verification:** Reviewed `ios/SmallTalkCoach/CoachingView.swift` and relevant backend
  storage/coaching code; `backend/.venv/bin/python -m pytest backend/tests -q`: 102 passed, 1 skipped,
  1 warning in 3.25s; `git diff --check` passed before this append.
- **Open issues:** Before App Store submission, update screenshot-mode consent copy to explicitly say
  that the screenshot image and extracted conversation text are sent to Anthropic, then re-audit it.

## 2026-07-21 09:16 UTC — Make coaching consent disclosure mode-aware
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Extracted the three consent-disclosure lines into mode-aware copy. Text mode preserves
  the existing first sentence verbatim; screenshot mode explicitly names the screenshot image and Anthropic.
  Added regressions for the text wording, screenshot disclosure, and distinct non-empty mode copy.
- **Files touched:** ios/SmallTalkCoach/CoachingView.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and generic simulator `xcodebuild build-for-testing`
  succeeded. Named iPhone 16 build and XCTest could not run because CoreSimulatorService has no available runtimes;
  `git diff --check` passed.
- **Open issues:** Run XCTest and the live Source-picker disclosure check on a host with a working iPhone 16 simulator.

## 2026-07-21 09:32 UTC — T-J backend bearer auth and coaching rate limit
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added opt-in, constant-time bearer auth for every non-health route and health auth status.
  Added app-isolated per-user fixed-window diagnosis limiting with safe environment fallbacks and Retry-After.
- **Files touched:** backend/app/main.py; backend/app/coaching.py; backend/tests/test_auth.py;
  backend/tests/test_rate_limit.py; backend/tests/test_api.py; backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 112 passed, 1 skipped,
  1 warning; `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 12:39 UTC — T-J iOS bearer-token configuration and request header
- **Model:** gpt-5
- **Status:** partial
- **What was done:** Added persisted optional API-token override and injects its bearer value once in
  `sendData`, covering all endpoints. Added captured-request tests for absent, set, cleared, and two-route headers.
  Confirmed a 401 maps through `APIClientError` to the existing generic coaching error path without a crash.
- **Files touched:** ios/SmallTalkCoach/APIClient.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` passed; generic Simulator `xcodebuild build-for-testing`
  passed (app and test bundle compiled/linked); `git diff --check` passed before this append.
- **Open issues:** iPhone 16 XCTest could not execute because CoreSimulatorService refused connections and reported no runtimes.

## 2026-07-21 09:52 UTC — T-G2 deterministic runtime answer-option permutation
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added deterministic per-user, lesson, review-attempt choice permutation at lesson serving and both grading paths, without mutating startup-loaded curriculum content.
  Added pure and endpoint tests for determinism, variation, copied state, option-feedback pairing, and served-order grading.
- **Files touched:** backend/app/store.py; backend/app/main.py; backend/tests/test_content.py;
  backend/tests/test_api.py; backend/README.md; WORKER_LOG.md
- **Result / verification:** `backend/.venv/bin/python -m pytest backend/tests -q`: 117 passed, 1 skipped, 1 warning in 2.46s; `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 10:29 UTC — T-K StoreKit 2 paywall infrastructure
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added local StoreKit subscription configuration, verified purchase/restore/current-entitlement infrastructure, continuous transaction observation, and a founder-controlled default-off paywall gate for Units 2–4. Added StoreKitTest purchase/load/restore coverage plus pure cancellation and gating tests; cancellation uses the pure state mapping because deterministic StoreKitTest cancellation simulation is awkward.
- **Files touched:** ios/SmallTalkCoach/SmallTalkCoach.storekit; ios/project.yml; ios/SmallTalkCoach/{FeatureFlags,PurchaseManager,PaywallView,RootView,HomeView}.swift; ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and generic-simulator `xcodebuild build-for-testing` passed; generated app bundle contains `SmallTalkCoach.storekit`; `jq empty` and `git diff --check` passed. iPhone 16 `xcodebuild test` was attempted but CoreSimulatorService refused connections and no device set was available, so XCTest did not execute.
- **Open issues:** Run the full XCTest/StoreKitTest suite on a host with a working iPhone 16 simulator service.

## 2026-07-21 10:37 UTC — T-K StoreKit test-action configuration wiring
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added the local StoreKit configuration path to the explicit `SmallTalkCoach` scheme's Test action; the existing Run action is unchanged.
- **Files touched:** ios/project.yml; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` passed; `xcodegen dump --type json` confirms the resolved Test action contains `SmallTalkCoach/SmallTalkCoach.storekit`; `git diff --check` passed. iPhone 16 `xcodebuild test` could not begin because CoreSimulatorService refused connections and reported no runtimes.
- **Open issues:** With installed XcodeGen 2.45.4, the generated shared `.xcscheme` showed the StoreKit reference only under Launch despite the resolved Test spec retaining it; confirm TestAction emission and run the StoreKitTest suite on a host with a working simulator service.

## 2026-07-21 10:46 UTC — T-K StoreKit test-bundle resource wiring
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Removed the unsupported Test-action StoreKit setting and added the local StoreKit configuration as an explicit `SmallTalkCoachTests` resource.
- **Files touched:** ios/project.yml; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` passed. `xcodebuild build-for-testing -sdk iphonesimulator -derivedDataPath /private/tmp/... CODE_SIGNING_ALLOWED=NO` passed, and the built test bundle contains `SmallTalkCoach.storekit`. iPhone 16 `xcodebuild test` could not execute because CoreSimulatorService refused connections and reported no runtimes; `git diff --check` passed.
- **Open issues:** Run the full XCTest/StoreKitTest suite on a host with a working iPhone 16 simulator service.

## 2026-07-21 10:53 UTC — Document CLI StoreKitTest limitation with honest skips
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added documented `XCTSkip` calls as the first statement in exactly the
  three SKTestSession purchase/restore tests, preserving their existing assertions, plus the
  XPC/interactive-runner explanation in the test file and iOS README.
- **Files touched:** ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; ios/README.md; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and generic-simulator `xcodebuild
  build-for-testing` succeeded. Named iPhone 16 / iOS 18.2 `xcodebuild test` was attempted,
  but CoreSimulatorService refused the connection before XCTest execution; `git diff --check` passed before this append.
- **Open issues:** Run the three StoreKit purchase-flow tests manually through Xcode's Test navigator before a release; this sandbox cannot run the simulator suite.

## 2026-07-21 11:21 UTC — T-L free-draft grading with monthly cost ceiling
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added the Haiku-locked optional draft-grading adapter, strict response validation,
  in-memory UTC-month $5 budget guard, and lesson endpoint. Added the iOS feedback flow and focused tests;
  lesson completion submission remains independent of draft feedback.
- **Files touched:** backend/app/{draft_grading,main}.py; backend/tests/test_draft_grading.py;
  ios/SmallTalkCoach/{APIClient,Models,LessonDetailViewModel,LessonDetailView}.swift;
  ios/SmallTalkCoachTests/SmallTalkCoachTests.swift; WORKER_LOG.md
- **Result / verification:** `cd backend && source .venv/bin/activate && PYTHONPATH=.. pytest`: 128 passed,
  1 skipped, 1 warning. `cd ios && xcodegen generate` and generic-simulator `xcodebuild build-for-testing`
  passed; `git diff --check` passed.
- **Open issues:** iPhone 16 XCTest could not execute: CoreSimulatorService refused connections and no runtime
  was available. Privacy policy currently scopes Anthropic sharing to conversation text/screenshots, not practice drafts.

## 2026-07-21 11:33 UTC — Disclose free-draft grading in the privacy policy
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Added the separate user-initiated free-draft feedback disclosure, including the draft
  text and practice prompt sent to Anthropic and the non-persistence of draft feedback.
- **Files touched:** docs/legal/PRIVACY_POLICY.md; WORKER_LOG.md
- **Result / verification:** Reviewed `grade_lesson_draft` and its adapter to confirm it returns feedback
  without persistence; policy read end-to-end and `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 13:43 UTC — UI quick win #1: design tokens foundation
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added the AppTheme token namespace, generated-symbol asset catalog, app surface/card/button
  components, and light/dark SwiftUI previews. Cleared the stale AppIcon setting because this project has no AppIcon set.
- **Files touched:** ios/SmallTalkCoach/{AppTheme,AppSurface,CardStyle,PrimaryActionButton}.swift;
  ios/SmallTalkCoach/Assets.xcassets/; ios/project.yml; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` wired Assets.xcassets into Resources and generated symbols;
  all asset JSON validated with `jq`; production portions type-checked against generated symbols; backend tests: 128 passed,
  1 skipped. `git diff --check` passed. The iPhone 16 build could not start: CoreSimulatorService has no available runtimes.
- **Open issues:** Xcode Preview macro execution and full iOS build/test require a host with a working simulator service.

## 2026-07-21 14:05 UTC — UI quick win #1 round-2 card surface correction
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Replaced the standard/interactive foreground-label background with a 6% AppTheme brand-indigo surface tint; highlighted and warning variants are unchanged.
- **Files touched:** ios/SmallTalkCoach/CardStyle.swift; WORKER_LOG.md
- **Result / verification:** Asset-RGB/source-over math gives #EFEDF1 in light mode (default black contrast 18.03:1) and #1A1928 in dark mode (default white contrast 17.27:1). `cd ios && xcodegen generate` and `git diff --check` passed. Simulator-SDK `xcodebuild build` failed at asset compilation because CoreSimulatorService exposes no simulator runtimes.
- **Open issues:** Real iPhone 16 build and both-appearance screenshot verification require a host with a working simulator runtime.

## 2026-07-21 14:21 UTC — UI quick win #2: elevated Daily Mission card
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Applied the highlighted card and typography tokens to TodayCard; added full-width lesson/review CTAs with approximate durations, personalized-or-fallback purpose copy, and four state previews. Cleared only the Today List row's competing background/separator chrome.
- **Files touched:** ios/SmallTalkCoach/TodayCard.swift; ios/SmallTalkCoach/HomeView.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, `xcrun swiftc -parse SmallTalkCoach/TodayCard.swift`, and `git diff --check` passed. `xcodebuild build` and full `xcodebuild test` were attempted with workspace-local derived data but stopped in asset compilation: CoreSimulatorService reported no available iOS simulator runtimes; no XCTest cases executed.
- **Open issues:** Run the iPhone 16 build, full XCTest suite, and light/dark Home screenshot check on a host with a working simulator runtime. The `~3 min`/`~2 min` labels are intentionally type-based approximations; add a real per-lesson duration field only through a future content-model change if greater precision is needed.

## 2026-07-21 17:33 UTC — UI quick win #3: explicit Coach mode cards
- **Model:** gpt-5.6-terra
- **Status:** partial
- **Note:** this entry is brain-authored, not worker-self-reported — the worker process was killed mid-run (external stop, not a normal exit) while attempting its own build verification; it never reached its own logging step. Recorded here so the append-only log stays honest about provenance rather than silently backfilling as if the worker had written it.
- **What was done:** Diff reviewed directly by the brain and found complete: `CoachingReplyMode` enum (verbatim research copy) and `replyMode` state added to `CoachingViewModel`, correctly reset in `beginNewComposition()`; `CoachingComposeView` gates on `replyMode` — shows two `.cardStyle(.interactive)` mode-selection cards when unset, else the existing form with a "Change" affordance and mode-aware text/screenshot prompts. Three previews added (selection, both modes, one in dark). No backend or request-shape changes, matching spec.
- **Files touched:** ios/SmallTalkCoach/CoachingView.swift; ios/SmallTalkCoach/CoachingViewModel.swift
- **Result / verification:** Not run by the worker (killed before its build attempt completed — `CoreSimulatorService connection became invalid` mid-command, a harsher variant of the same sandbox simulator-access gap seen every prior cycle). Brain verifying independently now: full build, full test suite, and real light/dark screenshots on its own environment (confirmed healthy — simulator booted, all runtimes present — before proceeding).
- **Open issues:** None identified from the code review; pending the brain's own build/test/visual verification before accept/reject.

## 2026-07-21 17:44 UTC — UI quick win #3 verification follow-up (brain)
- **Model:** n/a — brain verification note, appended per append-only discipline rather than editing the entry above
- **Status:** done
- **What was done:** Completed the verification the previous entry deferred. Full build + `xcodebuild test`: 76 passed, 3 pre-existing skips, 0 failures — matches baseline exactly. Real simulator screenshots (diagnostic entry-point swap, reverted after): mode-selection screen (light) shows both cards correctly; "Review my reply" composer verified in both light and dark — mode label, "Change" link, and mode-aware placeholder copy all render exactly as specified, rest of the form (disclosure, consent, submit) untouched.
- **Files touched:** none beyond this log entry
- **Result / verification:** ACCEPTED as specified — zero rejections needed despite the unusual killed-worker-process provenance.
- **Open issues:** none

## 2026-07-21 14:48 UTC — UI quick win #4: reorder coaching report
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Moved the existing Takeaway and How to respond sections before interpretation, and moved the unchanged score section after strengths/improvements.
- **Files touched:** ios/SmallTalkCoach/CoachingView.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate` and `xcrun swiftc -parse SmallTalkCoach/CoachingView.swift` passed; `git diff --check` passed. iPhone 16 `xcodebuild build` and `xcodebuild test` were attempted but CoreSimulatorService refused connections and exposed no runtimes, so neither build nor XCTest execution completed.
- **Open issues:** Run the iPhone 16 build and full XCTest suite on a host with a working simulator service.

## 2026-07-21 15:07 UTC — UI quick win #5a: skeleton loading and coaching-history empty state
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added reusable animated/static Reduce-Motion-aware `SkeletonBlock` previews and replaced the five scoped loading states with shaped skeleton layouts. Replaced Coaching History’s generic empty state with a sample report card and an action that resets the composer then dismisses History.
- **Files touched:** ios/SmallTalkCoach/{SkeletonBlock,HomeView,CoachingView,ProfileView,LessonDetailView}.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, `xcrun swiftc -parse` of the five touched view files plus SkeletonBlock, and `git diff --check` passed. `xcodebuild build` exited 65 at asset compilation because CoreSimulatorService exposes no simulator runtimes; iPhone 16 `xcodebuild test` found no matching device, so no XCTest cases ran. SDK type-check was additionally blocked by the sandboxed SwiftUI Preview macro plugin.
- **Open issues:** Run the full iPhone 16 build/test suite and visually inspect both SkeletonBlock previews on a host with a functioning simulator service.

## 2026-07-21 15:19 UTC — Quick Win #5a round-2 SkeletonBlock compile fix
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Replaced the read-only preview environment key with the SDK-declared writable
  `_accessibilityReduceMotion` key; bounded the pulse peak opacity at `1.0`.
- **Files touched:** ios/SmallTalkCoach/SkeletonBlock.swift; WORKER_LOG.md
- **Result / verification:** Xcode 26.6 / iOS 26.5 SwiftUI interface confirms the writable key; an exact
  SwiftUI SDK type-check probe passed. `cd ios && xcodegen generate`, `swiftc -parse`, and `git diff --check` passed.
  `xcodebuild build` stopped at asset compilation because CoreSimulatorService has no runtimes; iPhone 16 tests could not start.
- **Open issues:** Run the full build/test suite and inspect both previews on a host with a working simulator runtime.

## 2026-07-21 15:22 UTC — Quick Win #5a round 3 (final): remove private preview override
- **Model:** gpt-5.6-terra
- **Status:** done
- **What was done:** Removed the Reduce Motion-only SkeletonBlock preview and its unsupported private
  `_accessibilityReduceMotion` environment override. Kept the primary preview and the production public
  `@Environment(\.accessibilityReduceMotion)` behavior unchanged.
- **Files touched:** ios/SmallTalkCoach/SkeletonBlock.swift; WORKER_LOG.md
- **Result / verification:** Confirmed no `_accessibilityReduceMotion` reference remains in SkeletonBlock;
  `git diff --check` passed.
- **Open issues:** none

## 2026-07-21 18:38 UTC — UI quick win #5b: local response copy confirmation
- **Model:** gpt-5.6-terra
- **Status:** partial
- **What was done:** Added an in-row teal copy control to each example response. It copies the exact text,
  provides native success haptics and a VoiceOver announcement, then shows a local Copied/checkmark state
  for 1.5 seconds with Reduce Motion-aware animation.
- **Files touched:** ios/SmallTalkCoach/CoachingView.swift; WORKER_LOG.md
- **Result / verification:** `cd ios && xcodegen generate`, `xcrun swiftc -parse`, an isolated iOS 17 SDK
  type-check of the exact haptic/task/accessibility APIs, and `git diff --check` passed. `xcodebuild build`
  reached asset compilation but failed because CoreSimulatorService exposes no iOS runtimes; iPhone 16 tests
  could not execute because no simulator destination is available.
- **Open issues:** Run the full iPhone 16 build/test and verify the real clipboard, haptic, and local confirmation on a host with a working simulator runtime.
