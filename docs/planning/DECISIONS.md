# Smalltalk Coach — Decision Log

Use this file to preserve important product decisions and prevent the same questions from being reopened without new evidence.

## Decision Statuses

- **Confirmed:** Supported strongly enough to guide current work.
- **Experiment:** A hypothesis being actively tested.
- **Rejected:** Considered and intentionally excluded.
- **Revisit:** Parked until a defined trigger or new evidence appears.

## Current Decisions

### 2026-07-17 — Learning Is the Primary Product

- **Status:** Experiment
- **Decision:** The guided learning path is the primary experience; AI coaching is a supporting utility.
- **Why:** The intended differentiation is long-term skill improvement rather than one-time AI-generated replies.
- **Evidence:** Founder vision only; user behavior has not yet validated it.
- **Consequence:** V1 must measure lesson engagement and coaching-to-lesson conversion, not only AI chat usage.
- **Revisit trigger:** Target users repeatedly seek direct answers but show little interest in learning or practice.

### 2026-07-17 — Coaching Must Build Independence

- **Status:** Confirmed
- **Decision:** The AI should explain, guide, and improve user drafts rather than always producing a final reply immediately.
- **Why:** The product should build transferable capability and avoid unnecessary user dependence.
- **Evidence:** Core product principle.
- **Consequence:** Coaching quality should be evaluated partly by whether users understand and reuse the skill.
- **Revisit trigger:** Accessibility, urgency, safety, or strong evidence shows that a direct-answer mode is required in specific contexts.

### 2026-07-17 — Start With a Narrow V1

- **Status:** Experiment
- **Decision:** Launch with one beginner path and a focused coaching loop rather than many audience-specific tracks.
- **Why:** A small team should validate demand, learning behavior, and retention before expanding content or AI architecture.
- **Evidence:** Early-stage product logic; target segment remains unknown.
- **Consequence:** New tracks, broad personalization, and complex multi-agent grading remain out of scope until the core loop is proven.
- **Revisit trigger:** One segment and core loop show strong activation, learning, and retention signals.

### 2026-07-17 — V1 Target Segment: Relocation Wedge

- **Status:** Experiment
- **Decision:** V1 lessons, marketing, and validation target early-career professionals and students who relocated for work or school within roughly the last 6 months ("Relocated Newcomers"). Positioning stays welcoming to all newcomers; the wedge is who content is written for. The broad life-transition population is the expansion market, not the v1 target.
- **Why:** Won a research head-to-head against the broad life-transition segment on 6 of 9 dimensions — curriculum coherence (one shared scenario world: office/campus), retention (curriculum extends into workplace communication after the transition ends), pain frequency (office/campus force daily interaction), willingness-to-pay framing (career-anchored), validation ease (homogeneous interviewees, concrete channels), and search-intent fit — losing only raw market size, which does not matter for a beachhead. Dating segment rejected: saturated (Rizz ~6–7.5M downloads, ~$190K/mo, dozens of clones) and violates the reply-generator non-goal. ESL segment rejected: category giants (ELSA, Speak, Praktika, TalkPal, Loora, SmallTalk2Me). The broad "general social improver" slot is already occupied by Gleam.
- **Evidence:** Gleam: Social Intelligence (7,800 App Store ratings, 4.8★, $12.99/mo or $69.99/yr) validates willingness to pay for gamified social-skills learning, while its critical reviews call the content too generic ("geared towards middle management types") — so the differentiation path is depth in one niche. The skill-teaching slot for newcomers is unowned (Meetup, Bumble BFF, PearUp, BeFriend do matching, not skill-building). Wedge size: 1,177,766 international students in the US in 2024-25 (+5%), OPT 294,253 (+21%), plus domestic new grads and relocators. Institutional precedent: Boston College's staffed Conversation Partners program (B2B2C signal). All web research — no user interviews yet.
- **Consequence:** The first lesson path and coaching scenarios are written for office/campus newcomer situations. Validation interviews recruit from the wedge (see `VALIDATION_PLAN.md`). Dating and ESL content are out of scope. The primary-payer sub-question (students vs professionals) is left to interview data.
- **Revisit trigger:** Interviews show no willingness-to-pay signal; wedge users demand replies-only help; recruitment channels fail to produce interviewees; or the US international-enrollment decline (fall 2025 new enrollment −17%) worsens and the student half becomes unreachable (then shift professionals-first).

### 2026-07-17 — Brain/Worker Orchestration for Build Phase

- **Status:** Confirmed
- **Decision:** Development runs as a brain/worker loop: Claude Fable 5 is the brain/orchestrator (thinks, plans, assigns, reviews); a worker model (Sonnet 5, Codex, or GPT 5.6) executes assigned tasks and reports output back; the brain reviews and loops until acceptance. Deliberately not a CLAUDE.md-only setup. Spec: `ORCHESTRATION.md`.
- **Why:** Founder decision on build tooling — separates judgment (planning and review) from execution throughput.
- **Evidence:** Founder decision; no empirical comparison run.
- **Consequence:** Before activating any loop on the app repo, check for existing scheduled loops (e.g., CronList) and the repo's `PROGRESS.md` coordination file — an independent loop has committed to the smalltalk-coach repo before. No app code is written until the validation step defines what to build.
- **Revisit trigger:** Worker output quality or cost makes the loop slower than direct execution, or coordination conflicts appear on the shared repo.

### 2026-07-18 — Worker Model Locked to Codex (GPT 5.6)

- **Status:** Confirmed
- **Decision:** The brain/worker split is fixed and final: brain/orchestrator = Claude Fable 5 only — plans, delegates, reviews, and accepts work, never implements directly. All workers = Codex (GPT 5.6) only — CLI slugs `gpt-5.6-terra` (default) or `gpt-5.6-luna`. This supersedes the per-task worker choice ("Sonnet 5, Codex, or GPT 5.6") in "2026-07-17 — Brain/Worker Orchestration for Build Phase"; that entry's loop protocol and guards stand unchanged.
- **Why:** Founder decision on build tooling, stated as final and not open to change; a fixed split removes per-task model debate.
- **Evidence:** Founder instruction 2026-07-18. Empirical checks: Codex CLI 0.144.5 installed (ChatGPT-account auth already present in `~/.codex`); raw slug `gpt-5.6` is rejected with a 400 under ChatGPT-account Codex — the valid GPT 5.6 slugs are `gpt-5.6-terra` ("balanced agentic coding") and `gpt-5.6-luna` ("fast and affordable"); a `gpt-5.6-terra` smoke task and a full wrapper-script run both passed.
- **Consequence:** Harness built 2026-07-18 in the app repo at `.claude/skills/brain-worker-loop/` (SKILL.md loop protocol + `worker.sh`, which enforces the GPT 5.6-only rule and refuses other models). The two older scheduled-task skills (Fable-5 + Sonnet-5 workers) are marked superseded in place; the app repo's `PROGRESS.md` carries the coordination note. The loop stays dormant until `VALIDATION_PLAN.md` thresholds are met.
- **Revisit trigger:** Same as the orchestration entry (worker quality/cost makes the loop slower than direct execution), or Codex/GPT 5.6 access is lost.

### 2026-07-18 — Full Restart of the App Repo (Phase 0 Removed)

- **Status:** Confirmed
- **Decision:** The smalltalk-coach app repo drops the Phase 0 implementation (`backend/` + `ios/`, 65 files) from `master` and becomes planning-first: brain/worker loop harness + planning/coordination docs only. The pre-cleanup tree is archived at tag `phase0-archive` (pushed to origin; rollback is one command). v1 will be re-derived from `VISION.md`/`ARCHITECTURE.md` (kept as design references) after `VALIDATION_PLAN.md` thresholds are met — not built directly on the old tree.
- **Why:** Founder decision: a clean-slate repo with no legacy code implying the old app is active, after the brain review explicitly surfaced that this reverses the earlier "Phase 0 is the v1 foundation / not wasted" framing.
- **Evidence:** Founder approval 2026-07-18 following the brain's cleanup audit (KEEP 11 / DELETE 65 / REVIEW 0; no file under `backend/`/`ios/` touched after 2026-07-12).
- **Consequence:** App-repo `DECISIONS.md` carries the executing entry ("Full Restart: Phase 0 Implementation Removed"); README rewritten to the planning-first state; ARCHITECTURE.md and PROGRESS.md annotated so nothing implies the old implementation is present. The build scope gate (no app code until validation) is unchanged.
- **Revisit trigger:** Validation passes and the rebuild would genuinely reuse Phase 0 components — restore selectively from `phase0-archive`.

### 2026-07-18 — Validation Interviews Deferred; Build Gate Waived (Founder)

- **Status:** Confirmed (founder decision)
- **Decision:** The wedge validation interviews (`VALIDATION_PLAN.md`) and
  their decision thresholds (≥8/15 at-least-weekly pain, ≥5/15 concrete
  willingness-to-pay signal) are consciously skipped as a precondition for
  build work. `VALIDATION_PLAN.md` is retained as reference material
  (deferred, not deleted). The roadmap proceeds directly to v1 lesson-path
  definition. App code remains gated on the v1 lesson path being defined
  **and** an explicit founder go-ahead — this waiver alone does not start
  app coding.
- **Why:** Founder instruction 2026-07-18: skip the interview kit and the
  interview gate, proceed on the roadmap.
- **Evidence:** Founder instruction only. No new user evidence; the segment
  lock ("2026-07-17 — V1 Target Segment: Relocation Wedge") remains an
  Experiment supported by web research, now without a scheduled interview
  test.
- **Consequence:** Every interview-dependent unknown (primary payer within
  the wedge, peak-pain relocation moment, pricing, lesson-length tolerance)
  must be carried as an explicitly labeled assumption with a revisit
  trigger in v1 planning docs, starting with `LESSON_PATH_V1.md`. The Open
  Decisions item "the first 5–10 lessons in the beginner path" is being
  resolved by design judgment, not interview data.
- **Revisit trigger:** Founder reinstates interviews; or early real-user
  signals (waitlist behavior, store reviews, usage, refunds) contradict the
  wedge, payer, or pricing assumptions.

### 2026-07-18 — Build Start Approved (Founder Delegation)

- **Status:** Confirmed
- **Decision:** The v1 build begins. The scope gate's remaining condition
  (explicit founder approval of build start) is met: the founder authorized
  build start if the brain's expert judgment selected it, and it did (see
  root `DECISIONS.md` → "2026-07-18 — Build Start Approved;
  Content-Model-First Sequencing" for the engineering rationale). Build
  order is learning-path-first, per the product thesis: (1) lesson content
  model + one authored sample lesson, (2) backend curriculum-serving
  foundation, (3) remaining lesson content, (4) coaching/diagnosis surface,
  (5) iOS app when the Xcode gate clears.
- **Why:** Founder instruction 2026-07-18 delegating the go/no-go to the
  brain; the learning path is the primary experience, so it is built and
  made real first.
- **Evidence:** Founder instruction; `LESSON_PATH_V1.md` accepted the same
  day, closing the "first 5–10 lessons" open decision.
- **Consequence:** The product is now in build phase under the brain/worker
  loop's existing safety rules; interview-dependent assumptions in
  `LESSON_PATH_V1.md` §6 remain unvalidated and carry into the build.
- **Revisit trigger:** Founder redirects; or early build reveals the lesson
  path/content model needs restructuring before more code lands.

### 2026-07-19 — Coaching Is Response-Oriented (Teach the User to Fish)

- **Status:** Confirmed (founder decision)
- **Decision:** The coaching pipeline treats submitted text as the OTHER
  party's message (the stimulus) unless the user explicitly marks turns
  as their own (`Me:` labels in text; declared side in screenshots). Two
  modes: **stimulus_only** (no user turns) — no dimension scores at all;
  output = interpretation of the incoming message (tone, intent, what a
  good response must accomplish) + coaching on constructing the reply
  (structure/tone/include/avoid) + 1–2 short example responses + a
  transferable takeaway; **with_user_reply** (user turns present) —
  dimension scores apply ONLY to the user's turns, never the other
  party's words, plus the same interpretation/coaching/takeaway
  orientation (coaching the next reply when the conversation ends on the
  other party's turn). Every coaching output ends with a generalizable
  takeaway. Lesson routing uses the weakest scored dimension when scores
  exist, else a model-named `focus_dimension` validated against the four
  dimensions. This applies globally to any incoming message type, not
  one scenario.
- **Why:** Founder correction 2026-07-19: the pipeline scored incoming
  messages as if the user had said them — backwards. Product purpose is
  capability transfer for responding well in real situations
  (PRODUCT_BRIEF §6 Flow C, now made the pipeline's core orientation).
- **Consequence:** Diagnosis contract/schema v2 (COACHING_PIPELINE_V1
  §2.2 amended), transcript stimulus-default for unlabeled text,
  rewritten diagnosis prompt with explicit role binding, routing
  fallback, iOS report rendering for the new fields. Example responses
  are founder-mandated teaching artifacts — kept short and paired with
  the takeaway, consistent with §6's "examples when useful" boundary.
- **Revisit trigger:** User feedback shows demand for scoring their side
  of full conversations differently, or the takeaway/examples encourage
  copy-paste dependency (then rebalance with the Learning Boundary).

## Decision Template

### YYYY-MM-DD — Short Decision Name

- **Status:** Confirmed / Experiment / Rejected / Revisit
- **Decision:**
- **Why:**
- **Evidence:**
- **Consequence:**
- **Revisit trigger:**

## Evidence Log

Record evidence separately from opinions.

| Date | Source | Observation | Supports or challenges | Confidence |
|---|---|---|---|---|
| 2026-07-17 | Founder vision | Users should improve over time rather than only receive replies. | Supports learning-first thesis | Low until user-tested |
| 2026-07-17 | App Store research | Gleam (broad "Duolingo for social skills"): 7,800 ratings, 4.8★, $12.99/mo or $69.99/yr; critical reviews call content too generic. | Validates WTP for gamified social learning; supports niche-depth wedge strategy | Medium (store data, not interviews) |
| 2026-07-17 | App Store research | Rizz ~6–7.5M downloads, ~$190K/mo at $7/wk; dozens of AI dating-reply clones. | Supports rejecting dating segment (saturation + reply-generator trap) | Medium |
| 2026-07-17 | IIE Open Doors / NAFSA | 1,177,766 intl students in US 2024-25 (+5%); OPT +21% to 294,253; fall 2025 new enrollment −17%. | Supports wedge market size; flags US intl-student headwind | High (official data) |
| 2026-07-17 | WHO 2025 report | 1 in 6 people worldwide affected by loneliness. | Supports pain breadth behind the transition segment | High |

## Open Decisions

- ~~Initial target user and use case~~ — resolved 2026-07-17 (Relocation Wedge, see entry above).
- Primary payer within the wedge: students vs early-career professionals (decided by interview data).
- The first 5–10 lessons in the beginner path.
- The smallest coaching output that creates learning value.
- The exact boundary between direct reply help and guided learning.
- What progress signal users will believe and value.
- Free experience, paid trigger, trial structure, and starting price test.
- Screenshot storage, deletion, and personalization policy.
