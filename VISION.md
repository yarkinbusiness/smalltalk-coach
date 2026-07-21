# SmallTalkCoach — Vision & Roadmap

This is the durable product reference for *what SmallTalkCoach is building
and why*. `ARCHITECTURE.md` is the companion technical reference for the
implemented system. Detailed contracts remain in `docs/planning/`, with
`docs/planning/COACHING_PIPELINE_V1.md` defining the coaching loop.

**Current status (2026-07-21): v1 is implemented and v2 execution is active.**
The running v1 is a SwiftUI iOS app backed by FastAPI and SQLite. Its AI
Coaching flow accepts pasted conversation text or a chat screenshot, asks the
user to identify their own side when needed, requires consent before sending
content to Anthropic, uses Claude Haiku 4.5 for transcript extraction and
structured coaching, then deterministically routes the result to a lesson.
There is no CMA coordinator or worker fan-out in v1. See `PROGRESS.md` and
`DECISIONS.md` for the live build state and decisions; the current roadmap is
the `PROGRESS.md` v2 backlog.

## The actual vision, in one paragraph

Not a roleplay-practice app with a coach bolted on. A Duolingo-style daily
habit app for learning to approach and talk to people better, paired with
an AI coach that analyzes a user's **real** conversations (not just
in-app roleplay) and closes the loop: **diagnose the real conversation →
recommend the specific lesson that fixes the weak spot → the user
practices it → it stops happening in real life.** Repeated over time, the
accumulated real-conversation data builds a genuine per-user profile
("this person specifically struggles with follow-up questions"), so
coaching gets sharper the more someone uses it — not a one-off gimmick.

## The explicit differentiation (stated 2026-07-12, worth preserving verbatim in spirit)

Most "AI rizz"/dating-coach apps just read a screenshot and hand back a
copy-paste-able reply — a crutch with no skill transfer, and the user
learns nothing for next time. This app is meant to do both things
existing apps don't combine: **teach the underlying skill** (via lessons
routed from real diagnosis) **and** store the user's data over time so
coaching compounds, while still giving a personalized suggested reply as
one output, not the whole product. The suggested-reply feature is the
*entry point* into skill-building, not a replacement for it.

## The closed loop, concretely

```
Real conversation happens
        │
        ▼
User pastes text or imports a screenshot
        │
        ▼
User marks their own side when attribution is needed and gives consent
        │
        ▼
Claude Haiku 4.5 normalizes screenshot content into a clean transcript;
pasted text is normalized locally
        │
        ▼
Claude Haiku 4.5 returns one structured diagnosis. If the user has replied,
the diagnosis scores warmth/curiosity/reciprocity/flow; otherwise it teaches
the user how to construct a response without scoring the other person
        │
        ▼
Backend validates the result and deterministically selects the lesson that
addresses the focus or weakest dimension
        │
        ▼
User receives interpretation, response coaching, examples, a transferable
takeaway, a small practice action, and the recommended lesson
```

This is a **single-model, Haiku-only, no-CMA pipeline**. Pasted text needs one
bounded Haiku diagnosis call. A screenshot needs one bounded Haiku vision
extraction call followed by the same bounded Haiku diagnosis call. Lesson
routing, validation, persistence, streaks, reviews, and profile aggregation
remain deterministic backend responsibilities.

## Current v1 product decisions

- **Two top-level surfaces:** Home is the structured learning path and daily
  habit surface; AI Coaching analyzes real conversations and returns the user
  to a relevant lesson.
- **Two supported coaching inputs:** pasted text and one chat screenshot.
- **User-controlled attribution:** the user marks their side for screenshots;
  the system does not infer identity from names, avatars, gender, or tone.
- **Explicit consent:** coaching content is sent to Anthropic only after the
  user consents to third-party AI processing.
- **Haiku-only model lock:** v1 uses `claude-haiku-4-5`; no coordinator model,
  worker model, CMA agent, session, environment, or model-memory layer is
  required.
- **Teach the user to fish:** coaching interprets the incoming message, teaches
  response construction, gives short examples and a transferable takeaway,
  and does not score the other person.
- **Deterministic lesson routing:** the backend, not the model, chooses the
  lesson from the curriculum routing table.
- **Real implementation baseline:** FastAPI + SQLite on port 8000 with
  `GET /health`, and a SwiftUI app verified on the iPhone 16 simulator running
  iOS 18.2.

# Historical — 2026-07-12 planning assumptions (superseded)

The remaining sections preserve the original five-scenario/CMA-era product
planning for decision history. They do **not** describe the implemented v1.
Where annotations exist, they record how those assumptions were resolved.

## Original decisions discussed on 2026-07-12

- **Real-conversation input: screenshot only**, for the first version.
  - Rejected: live audio recording of real conversations — real legal
    exposure (two-party-consent recording laws in many jurisdictions),
    plus needs on-device speech-to-text. Not worth the risk for v1.
  - Rejected (for now): raw text paste — technically simpler but messier
    input (timestamps/read-receipts mixed in) and more user friction than
    a screenshot. Screenshot chosen as the single first-version path
    rather than building both at once.
  - Privacy note carried forward: a screenshot of a real thread usually
    shows the *other person's* name/photo in the header — this is
    another real person's identity + words going through a third-party AI
    (Anthropic). Needs the same "we send data to a third-party AI"
    disclosure the practice mode already needs, extended to cover this.
- **Model routing for cost**: split the pipeline by which step actually
  needs vision quality.
  - The screenshot → transcript step needs real vision accuracy (a wrong
    transcript poisons everything downstream) — stays on a model with
    *confirmed, documented API vision support*. Claude is the proven
    choice here since the rest of the app already runs on it.
  - Everything downstream is bounded text reasoning (diagnosis, lesson
    routing, suggested-reply drafting) — same shape as the existing 4
    graders, and exactly where a cheap model earns its keep.
  - **DeepSeek V4 (Pro/Flash) does NOT currently have confirmed vision
    support via its public API**, despite DeepSeek shipping a real
    "Vision (Beta)" mode in their own consumer chat product
    (chat.deepseek.com) — confirmed by cross-checking DeepSeek's own API
    docs (no image content type documented) and a third-party report of
    empirically testing plausible vision-model names against the API (all
    rejected). This is a consumer-chat-product feature, not (yet) a
    developer-API one. Re-check this periodically — it's recent, active
    development (beta shipped ~April 2026) — but don't architect around
    it changing on any particular timeline.
  - Candidates for the cheap downstream steps: DeepSeek (once confirmed
    text-only via API, which it is) or Haiku 4.5 (same-vendor, simpler,
    still cheap). Not yet decided between these two — open question below.
  - Lesson *content* itself (the actual teaching material) should be
    authored/generated once and reused across users, not regenerated per
    user per day — the single biggest available cost lever, independent
    of which model ends up used anywhere else.

## What's already built — Phase 0, the foundation

*Historical: this describes the pre-restart Phase 0 build, removed
2026-07-18 (tag `phase0-archive`); the T1–T18 task ids are obsolete.*

Everything tracked as T1-T14 (plus T6b and two security/UX follow-up
fixes) in this session's task list is done, independently reviewed, and
pushed to `github.com/yarkinbusiness/smalltalk-coach`. In the frame of
this vision, that work is:

- **The grading engine** (`coach_coordinator` + 4 workers, warmth/
  curiosity/reciprocity/flow) — this is Phase 0's most important reusable
  piece. It doesn't care whether a transcript came from roleplay or a
  real screenshot; it's the analytical backbone for both.
- **The practice/rehearsal mode** (5 roleplay scenarios, partner-opens,
  scenario recommendations) — not the whole app as originally scaffolded,
  but a legitimate ongoing feature: low-stakes rehearsal before trying a
  skill for real, and (per this vision) the thing a daily streak actually
  gets anchored on, since real conversations don't happen on a schedule
  but a daily drill can.
- **Progress tracking/trend charts, onboarding, session history/replay** —
  general-purpose infrastructure, reusable regardless of input source.

Still blocked/deferred regardless of this vision work: T15 (live partner
smoke test, needs any Anthropic key), T16 (live CMA round-trip, needs
CMA-beta key), T17 (first Xcode build, needs Xcode installed), T18
(launch hardening — sequenced last on purpose either way).

## What's missing — Phase 2, the actual new work

Roughly in dependency order; the 2026-07-20 annotations identify what has
since shipped and what remains in the v2 backlog:

1. **Lesson/curriculum content system.** Actual taught material per skill
   (e.g. "asking better follow-up questions," "graceful exits"), not just
   "practice a scenario and get graded." Needs: a content model (what is
   a lesson — text, structured steps, a paired roleplay drill?), and
   likely maps each lesson to one or more of the 4 existing dimensions so
   recommendations can route into it. **[BUILT 2026-07-18 — static-JSON
   model per CONTENT_MODEL_V1.md; 12 lessons authored and served]**
2. **Daily habit loop.** Streak model + persistence, notification
   scheduling (needs APNs/push setup — a real new technical + Apple
   Developer requirement), a "today's lesson" home surface. **[NOT BUILT
   — v2 backlog T-D; local notifications chosen over APNs]**
3. **Screenshot import pipeline.** Upload/share UI on iOS, backend
   endpoint, vision-model call to extract a clean transcript, the privacy
   disclosure noted above. **[BUILT 2026-07-19 — COACHING_PIPELINE_V1
   path; Haiku-only vision extraction; per-submission consent in-app;
   real-screenshot quality eval still founder-gated]**
4. **Grading engine extended into a lesson router.** The coordinator's
   output needs a second output alongside the coaching report: which
   lesson (if any) this diagnosis should route the user into. This is
   new coordinator-prompt/response-shape work, not just a new endpoint —
   it changes what "the report" means. **[BUILT 2026-07-18/19 in
   simplified form — one structured diagnosis call + deterministic
   routing, not the CMA coordinator sketched here]**
5. **Suggested-reply generation.** Draft an actual response to the real
   message, explicitly framed in the product as a bridge into the lesson
   system, not a standalone copy-paste feature. **[BUILT 2026-07-19 —
   response-oriented coaching v2: interpretation, reply coaching, 1–2
   short examples, transferable takeaway]**
6. **Longitudinal personal profile.** A persistent record of a user's
   real-world patterns over time that makes later diagnoses sharper —
   distinct from (may build on top of) the existing local `reports`
   table and/or the CMA memory_store already used for the coordinator's
   cross-session context. **[NOT BUILT — v2 backlog T-E]**
7. **Cost-tiered model routing for all of the above** — wire in whichever
   cheap model gets chosen (DeepSeek or Haiku) for steps 4/5/6, keep
   vision-capable model only for step 3's extraction. **[SUPERSEDED —
   2026-07-19 Haiku-only lock: every backend call is
   `claude-haiku-4-5`]**

## Open questions — original planning framing; current states annotated below

- **Streak mechanics, exact rule.** Does completing a daily lesson/drill
  alone keep the streak alive, or does submitting a real-conversation
  screenshot for review also count? (User's framing leaned toward lesson
  activity as the base engagement signal, with the real differentiator
  being the compounding diagnosis loop rather than the streak rule itself
  — but the exact rule wasn't pinned down.) **[Being resolved by v2 task
  T-D: lesson/review completion or coaching submission all count as daily
  activity.]**
- **DeepSeek vs. Haiku 4.5** for the downstream cheap-reasoning steps —
  not decided; worth a real cost/quality comparison once Phase 2 scoping
  starts. **[Resolved by the 2026-07-19 Haiku-only lock.]**
- **Lesson content authorship** — hand-written by a person, generated
  once by a model and reviewed, or some mix? Affects both quality and the
  "generate once, reuse forever" cost assumption above. **[Resolved in
  practice: model-authored, brain-reviewed, against CONTENT_MODEL_V1
  (cycles 4–9).]**
- **How much of Phase 0's practice-mode UI needs to change** once lessons
  exist alongside plain roleplay scenarios — e.g. does the scenario
  picker become a lesson picker, or do lessons and free-practice scenarios
  coexist as distinct sections? **[Moot: the Phase 0 practice UI was
  removed in the Full Restart; roleplay/practice chat is deferred
  (COACHING_PIPELINE_V1 §7).]**
