# SmallTalkCoach — Vision & Roadmap

This file exists because the product vision got substantially clarified on
2026-07-12, after Phase 0 (below) was already built. It's the durable
record of *what this app is actually supposed to become*, so that neither
this conversation nor any other session/loop working on this repo loses
the thread. `ARCHITECTURE.md` stays the technical reference (how the
backend/CMA/iOS pieces fit together); this file is the product reference
(what we're building and why).

**Status as of this writing: implementation is paused for planning.**
Nothing described in "Phase 2" below has been started. Do not assume any
of it exists just because it's written here.

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
User screenshots it, imports into the app
        │
        ▼
Vision-capable model reads the screenshot → clean transcript
        │
        ▼
Same 4-dimension grading engine already built (warmth/curiosity/
reciprocity/flow) diagnoses it — same engine that grades roleplay today
        │
        ▼
Output is now TWO things, not one:
  1. A coaching report (as today)
  2. A lesson recommendation ("this is your reciprocity dimension
     again → go do the reciprocity lesson") + an optional suggested
     reply for the actual message
        │
        ▼
User does the recommended lesson/roleplay drill (existing practice mode)
        │
        ▼
Diagnosis feeds a long-term per-user profile → next diagnosis is sharper,
next recommendation is more targeted
```

## Decisions made in the 2026-07-12 planning discussion

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

Roughly in dependency order, not yet scoped into T-numbered tasks or
started:

1. **Lesson/curriculum content system.** Actual taught material per skill
   (e.g. "asking better follow-up questions," "graceful exits"), not just
   "practice a scenario and get graded." Needs: a content model (what is
   a lesson — text, structured steps, a paired roleplay drill?), and
   likely maps each lesson to one or more of the 4 existing dimensions so
   recommendations can route into it.
2. **Daily habit loop.** Streak model + persistence, notification
   scheduling (needs APNs/push setup — a real new technical + Apple
   Developer requirement), a "today's lesson" home surface.
3. **Screenshot import pipeline.** Upload/share UI on iOS, backend
   endpoint, vision-model call to extract a clean transcript, the privacy
   disclosure noted above.
4. **Grading engine extended into a lesson router.** The coordinator's
   output needs a second output alongside the coaching report: which
   lesson (if any) this diagnosis should route the user into. This is
   new coordinator-prompt/response-shape work, not just a new endpoint —
   it changes what "the report" means.
5. **Suggested-reply generation.** Draft an actual response to the real
   message, explicitly framed in the product as a bridge into the lesson
   system, not a standalone copy-paste feature.
6. **Longitudinal personal profile.** A persistent record of a user's
   real-world patterns over time that makes later diagnoses sharper —
   distinct from (may build on top of) the existing local `reports`
   table and/or the CMA memory_store already used for the coordinator's
   cross-session context.
7. **Cost-tiered model routing for all of the above** — wire in whichever
   cheap model gets chosen (DeepSeek or Haiku) for steps 4/5/6, keep
   vision-capable model only for step 3's extraction.

## Open questions — not yet decided, need answers before Phase 2 implementation starts

- **Streak mechanics, exact rule.** Does completing a daily lesson/drill
  alone keep the streak alive, or does submitting a real-conversation
  screenshot for review also count? (User's framing leaned toward lesson
  activity as the base engagement signal, with the real differentiator
  being the compounding diagnosis loop rather than the streak rule itself
  — but the exact rule wasn't pinned down.)
- **DeepSeek vs. Haiku 4.5** for the downstream cheap-reasoning steps —
  not decided; worth a real cost/quality comparison once Phase 2 scoping
  starts.
- **Lesson content authorship** — hand-written by a person, generated
  once by a model and reviewed, or some mix? Affects both quality and the
  "generate once, reuse forever" cost assumption above.
- **How much of Phase 0's practice-mode UI needs to change** once lessons
  exist alongside plain roleplay scenarios — e.g. does the scenario
  picker become a lesson picker, or do lessons and free-practice scenarios
  coexist as distinct sections?
