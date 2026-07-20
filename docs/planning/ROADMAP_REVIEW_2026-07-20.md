# Roadmap Strength Report — smalltalk-coach (2026-07-20)

## Context

The founder asked the brain to audit the current roadmap against VISION.md, PRODUCT_BRIEF.md, ARCHITECTURE.md, both DECISIONS.md logs, PROGRESS.md, and WORKER_LOG.md, rate each item, give a verdict, and — if the roadmap is weak or empty — research and propose new tasks. The founder approved this report and its proposed backlog on 2026-07-20 (record: root `DECISIONS.md` → "2026-07-20 — v2 Backlog Adopted After Roadmap Strength Review").

The operative roadmap at review time was **PROGRESS.md's "v1 build backlog"** (there is no standalone ROADMAP.md). VISION.md's Phase 2 list and PRODUCT_BRIEF §10's Must-Haves serve as the strategic reference the roadmap should be tracking.

---

# Section 1 — Roadmap Assessment

## 1.1 Completed items (all Strong — executed and verified)

| # | Item | Vision alignment | Architecture fit |
|---|------|------------------|------------------|
| 1 | Content model + L01 fixture (cycle 4) | Strong — learning path is the primary experience (BRIEF §3) | Static JSON + load-time validation; the recorded cost lever |
| 2 | Backend skeleton + curriculum serving (cycle 5) | Strong | FastAPI + sqlite, sequential unlock per LESSON_PATH_V1 |
| 3–4 | Full 12-lesson curriculum, Units 1–4 (cycles 6–9) | Strong — newcomer wedge content per the segment lock | Loader-validated against the manifest |
| 5 | Persistence/code hardening (cycle 10) | n/a (hygiene) | Strong |
| 6a–b | iOS scaffold + lesson detail/completion (cycles 11, 13) | Strong — full learning loop usable in-app | Two-tab SwiftUI shell per ARCHITECTURE v1 |
| 7 | Coaching pipeline: design, text path, iOS tab, screenshot path, response-oriented v2 (cycles 12, 14–15, 18–23) | Strong — the closed loop (real conversation → diagnosis → lesson → practice) is implemented end to end | Plain Messages API, Haiku-only lock, deterministic routing |

The execution quality of what's done is high: 51 backend tests + 25 iOS tests green, live-API verified in both coaching modes, mandatory simulator verification each cycle.

## 1.2 Open items

| Item | Rating | Assessment |
|------|--------|------------|
| Vision-quality eval on real consented screenshots | **Strong, blocked** | Guards the core loop's input quality (COACHING_PIPELINE_V1 §6). Founder-gated on providing screenshots — but the eval *harness* is not gated and doesn't exist yet. That prep work is missing from the backlog. |
| Test-key rotation before production | **Weak** | Real hygiene item, but recorded only as a milestone footnote — no owner, no trigger, not in the backlog proper. |
| Validation-failure reason logging + third retry attempt | **Weak** | Legitimate (cycle 21 saw scored-mode validation fail both attempts on Haiku with a 502 between successes), but buried in a cycle-log note rather than tracked as a task. |
| "Backlog (actionable now)" items 1–4 (recommend.py, agents_setup.py, coach.py, partner.py, ios/Core) | **Missing (stale/invalid)** | Every referenced file was deleted in the 2026-07-18 Full Restart. A future cycle reading this section as actionable would attempt work on nonexistent code. |
| "Once the human-gated items are cleared" items 6–8 (CMA provisioning, CMA coaching run) | **Missing (stale/invalid)** | Superseded twice over: COACHING_PIPELINE_V1 §7 defers the CMA upgrade entirely, and the Haiku-only lock removes the model tiering these items assume. |

## 1.3 Document-consistency findings (side observations, cheap to fix)

- **VISION.md is stale**: still says "implementation is paused for planning" and describes Phase 0 (CMA grading engine, 5 roleplay scenarios) as the built foundation. Both statements predate the Full Restart and the v1 rebuild. Per the project's own living-docs rule, this should be synced with a DECISIONS.md pointer.
- **ARCHITECTURE.md** describes the CMA coordinator/4-worker roster as the v1 design; the implemented v1 is deliberately no-CMA, single-call, Haiku-only (COACHING_PIPELINE_V1 §1 records the relationship, but ARCHITECTURE.md itself only carries the "removed, retained as reference" banner — a reader landing there first gets the wrong model of the running system).
- **PROGRESS.md** mixes live state, historical state, and stale backlog in one file with per-section disclaimers; the stale-backlog risk above is the concrete harm.

## 1.4 Overall verdict

**The roadmap is too empty to keep executing.** Every actionable item is done; the only open items are founder-gated, informal footnotes, or stale. Meanwhile, the product docs define substantial v1 scope with no roadmap representation at all:

- PRODUCT_BRIEF §10 Must-Haves unbuilt: **basic progress tracking surface** (only lock-states exist), **clear privacy explanation + deletion controls** (per-report delete exists; no policy, no account-wide deletion, no App Store disclosure), **subscription/paywall experiment** (nothing).
- BRIEF §9 flows unbuilt: **Flow A** (onboarding/baseline — the app boots straight into the curriculum with an anonymous UUID), **Flow D** ("How did it go?" reflection).
- VISION.md Phase 2 items unbuilt: **daily habit loop** (streak, today-surface, notifications), **longitudinal profile** (reports persist but nothing aggregates them; each diagnosis is amnesiac), and spaced repetition (BRIEF §5: "revisit important skills through spaced repetition" — `recommendation_kind: review` exists in routing but nothing schedules review).

Verdict: **generate new tasks** (Section 2), refresh PROGRESS.md, retire the stale sections.

---

# Section 2 — Proposed New Tasks (prioritized)

**Research inputs** (fresh, 2026-07-20): Gleam — the direct competitor per the segment-lock research — ships bite-sized lessons, quizzes, streaks **with earned streak freezes**, goals, and lesson review; its top complaint is aggressive paywalls, which argues for a generous free tier. Duolingo retention research: 7-day streak → 3.6× course completion, streak power comes from loss aversion, personalized *achievable* daily goals sustain streaks, freeze/recovery mechanics prevent snap-quit churn. Newcomer/international-student sources confirm the wedge's pain is situational and recurring (slang, low-context culture, office/campus daily forced interaction) — supporting situation-tagged content and reflection after real interactions.

**Constraints every task below respects:** Haiku-only model lock (new features are deterministic/no-API-call unless stated), no CMA (deferred per COACHING_PIPELINE_V1 §7), FastAPI + sqlite + static JSON content + SwiftUI two-tab shell, brain/worker loop protocol with mandatory simulator verification. No task duplicates PROGRESS.md/WORKER_LOG.md work.

## P0 — hygiene and unblocking (do first, small)

### T-A. Retire stale roadmap sections + sync stale docs
- **Rationale:** Prevents a future cycle acting on deleted Phase 0 files; fixes VISION.md's factually false "paused for planning / Phase 0 is built" state per the project's own living-docs rule. Docs-only.
- **Acceptance:** PROGRESS.md stale sections marked historical with a pointer to the refreshed backlog; VISION.md status header updated (restart + v1 rebuild acknowledged, Phase 2 list annotated with what's now built); ARCHITECTURE.md banner extended to point readers at COACHING_PIPELINE_V1 as the implemented design; DECISIONS.md entry recording the sync.

### T-B. Vision-eval harness (the non-gated half of the founder-gated item)
- **Rationale:** The eval itself needs founder screenshots, but the harness doesn't. Building it now converts the founder gate from "blocks a work stream" to "drop files in a folder, run one command."
- **Acceptance:** A script (test-utility, not app code) that takes a directory of image + expected-transcript pairs, runs the existing `vision.py` extraction, and scores readable-turn recall, text fidelity, ordering, and attribution against the §6 thresholds; per-image and aggregate report; runs against 1–2 synthetic screenshots in CI-mode with mocks; documented consent/anonymization checklist for the founder's real set.

### T-C. Diagnosis retry hardening (cycle-21 note, promoted to a task)
- **Rationale:** Scored-mode validation intermittently exhausts both attempts on Haiku; a silent 502 between successes is currently invisible.
- **Acceptance:** Code-only (no content) failure-reason logging per attempt; retry count configurable, default 3; regression test simulating two failures + one success; error taxonomy unchanged.

## P1 — close the retention loop (the vision's actual differentiator)

### T-D. Daily habit loop v1: streak + "Today" surface + local notifications
- **Rationale:** VISION.md Phase 2 item 2 and the entire "Duolingo-style daily habit" framing — currently 0% built. Competitor parity demands it (Gleam has streaks/freezes). Local-first design fits the architecture: completion dates already persist server-side; streak computation is deterministic; `UNUserNotificationCenter` local notifications avoid the APNs server dependency VISION flagged. Resolves VISION's open streak-rule question per its own recorded leaning: **any lesson/review completion or coaching submission counts as the day's activity** (lesson activity as the base signal).
- **Acceptance:** Streak count + earned streak-freeze (1 per completed unit, cap 2) computed from activity dates, timezone-safe day boundary, survives reinstall via backend (activity is already persisted per user); Home tab "Today" card showing next lesson or review; one daily local notification at a user-chosen time, off by default, opt-in during onboarding; unit tests for boundary cases (DST, freeze consumption); no new API calls.

### T-E. Skill profile v1: deterministic longitudinal aggregation
- **Rationale:** VISION.md Phase 2 item 6 ("coaching compounds") is the stated moat, and today each diagnosis is amnesiac. A deterministic first version — aggregate persisted reports' dimension scores/focus_dimensions and lesson completions into a per-dimension profile — starts the compounding loop with zero model cost, and produces the compact "recurring pattern" summary a later cycle can inject into the diagnosis prompt.
- **Acceptance:** `GET /users/{id}/profile` returning per-dimension trend (score history where scored, focus-dimension frequency where not), recurring-weakness flag ("reciprocity flagged in 3 of last 5 reports"), lessons completed/recommended-but-not-taken; iOS profile surface (fold into Home per ARCHITECTURE's "progress folds into Home"); empty/1-report states handled; deterministic — no API calls; tests for aggregation edge cases.

### T-F. Reflection loop ("How did it go?") — BRIEF Flow D
- **Rationale:** The bridge between app and real life that nothing currently captures. After a lesson's practice action or a coaching report, the user records how the real interaction went. Structured self-report (went well / partly / avoided it + optional note) keeps it deterministic and free; entries feed T-E's profile.
- **Acceptance:** Backend reflection records tied to lesson or report id; iOS prompt surfaces on next app open after a practice action was shown (not push-dependent); reflection outcomes appear in the profile; skippable, never blocks; tests.

### T-G. Review / spaced-repetition pass
- **Rationale:** BRIEF §5 progression principle with zero implementation; routing already emits `recommendation_kind: review` but nothing schedules review. Duolingo/Gleam evidence says review + achievable daily goals is what makes a streak worth keeping. Deterministic reuse of existing lesson completion checks — no content authoring, no API calls.
- **Acceptance:** Review queue: completed lessons become due on a simple fixed-interval schedule (e.g. 3/7/21 days), weakest profile dimension prioritized; "Today" card offers review when nothing new is unlocked or path is complete (the path is finishable in days — review is what the Day-13 user does); completing review counts as streak activity; option-order shuffling for reused checks (also clears the recorded L02 nit); tests.

## P2 — activation and v1 Must-Haves

### T-H. Onboarding + baseline (BRIEF Flow A)
- **Rationale:** Activation metrics (§13) start at onboarding; the app currently opens cold into the curriculum. A 2–3 screen flow (goal pick from newcomer situations, office/campus context, 4-question self-assessment mapped to the four dimensions) personalizes the start deterministically and is where notification opt-in (T-D) lives.
- **Acceptance:** First-launch-only flow; results persisted server-side; starting emphasis reflected on Home ("since interview-mode is your worry, L04 will matter most" style copy); skippable; no API calls; tests.

### T-I. Privacy disclosure + deletion completeness
- **Rationale:** BRIEF §10 Must-Have and §12 safety principles; screenshots contain *another person's* identity and words routed to a third-party AI. App Store review (Nov 2025 rule) requires explicit disclosure before sharing personal data with third-party AI, and the vision-consent flow only covers in-app consent, not the policy/label layer. Doing this pre-TestFlight is far cheaper than at rejection time.
- **Acceptance:** Privacy policy + ToS drafted for what the app actually collects (the `privacy-policy-starter` skill covers this); account-wide coaching-data deletion endpoint + iOS control (per-report delete exists; account-wide is currently a §7 deferral); Privacy Nutrition Label mapping documented; disclosure copy audited against the November 2025 third-party-AI rule (`app-store-readiness` skill); DECISIONS.md entry for the retention/deletion policy (closes an Open Decision).

### T-J. Backend auth + deploy readiness
- **Rationale:** The backend is an open relay to the Anthropic key for anyone who can reach it — fine on localhost, untenable the moment it's deployed for TestFlight. (Phase 0 flagged the same gap; that code is deleted, so this is not duplicate work.)
- **Acceptance:** Shared-secret bearer token required on all non-health endpoints, configured via env, never in code; iOS reads base URL + token from a build config; rate limiting on coaching endpoints (they spend API budget); test-key rotation executed and documented as part of this task (absorbs the loose milestone footnote); tests for 401/429 paths.

## P3 — founder-input-needed (schedule the decision, not just the work)

### T-K. Paywall experiment scaffolding — **founder gate: pricing + free-tier boundary**
- **Rationale:** BRIEF §10 Must-Have ("simple subscription/paywall experiment") and §8's early-pricing principle; competitor anchor exists (Gleam $12.99/mo / $69.99/yr, top complaint = paywall aggression → be generous: full Unit 1 + N coaching sessions free). StoreKit 2 with local StoreKit-config testing needs no App Store Connect setup to start (`ios-monetization-setup` skill).
- **Acceptance:** Entitlement check gating units 2–4 and coaching beyond N free sessions behind one feature flag (default off until founder sets price); purchase/restore flows pass StoreKit local tests; no external payment links (3.1.1); founder decision recorded in DECISIONS.md before the flag ships on.

### T-L. Free-draft grading decision — **founder gate: cost/quality trade**
- **Rationale:** `free_draft` checks are deferred-v1 ungraded; grading drafts is the highest-leverage use of the response-oriented pipeline (BRIEF Flow C: "user drafts → AI improves and explains"), but each grade is an API call under a strict budget. Present the founder a costed option (Haiku-only, ~$0.001–0.003/draft) rather than deciding unilaterally.
- **Acceptance:** A one-page costed proposal (docs-only) with per-user monthly cost at realistic usage, reusing the existing diagnosis adapter; decision recorded; implementation only after founder approval.

## Explicitly not proposed
- CMA upgrade, talk-with-the-coach, roleplay/practice chat, voice — all deferred by COACHING_PIPELINE_V1 §7 / BRIEF §10 "later," and roleplay chat would burn API budget against the Haiku lock for a demoted feature.
- Server-side push (APNs) — local notifications deliver the habit loop without the Apple Developer + server dependency.
- New content tracks — BRIEF §11 non-goal until the wedge validates.

## Suggested execution order
T-A → T-B → T-C (one small cycle each), then T-D → T-E → T-F → T-G (the retention loop, one cycle each), then T-H → T-I → T-J, with T-K/T-L scheduled as founder decisions in parallel. Every cycle stays under the existing loop protocol (worker spec, brain review, simulator verification, auto-push).

---

**Sources (2026-07-20 research):** [Gleam App Store listing](https://apps.apple.com/us/app/gleam-social-intelligence/id6745815058) · [Gleam on Product Hunt](https://www.producthunt.com/products/gleam-2) · [Gleam feature overview (MWM)](https://mwm.ai/apps/gleam-social-intelligence/6745815058) · [Duolingo streak mechanics analysis](https://duolingo.deconstructoroffun.com/mechanics/streaks) · [Duolingo on streaks & habit research](https://blog.duolingo.com/how-duolingo-streak-builds-habit/) · [Duolingo gamification case study](https://trophy.so/blog/duolingo-gamification-case-study) · [Small talk as an international student (Interstride)](https://interstride.com/blog/Leveraging-the-power-of-small-talk-as-an-international-student-in-the-US/) · [International student challenges (Clay Center)](https://www.mghclaycenter.org/parenting-concerns/young-adults/international-college-students/)
