# UI Improvement Plan

**Status: proposed, not approved. Nothing in this document has been implemented.**

Source material: `docs/research/smalltalk-coach-research.pdf` ("SmallTalk
Coach UI/UX and Motion Research," HeyClicky Research, 21 Jul 2026) and its
companion `SMALLTALK_COACH_UI_UX_RESEARCH.md` / `SOURCE_NOTES.md`, both
pulled from the research tool's own project folder and copied into
`docs/research/` alongside the PDF for anyone who wants the full detail
this plan condenses. The research benchmarked 9 apps (Gleam, Skillsta,
CharmXP, Praktika, Speeko, Orai, Duolingo, Finch, Elevate) against public
App Store listings and official design guidance, and separately audited
this repo's actual SwiftUI source.

Every item below was cross-checked by me directly against the current
`ios/SmallTalkCoach/*.swift` source — not just copied from the research
doc. Where the research's claim and my own reading agree, I cite the exact
file/behavior. Where I found something the research didn't call out (or
found it already partially solved), I've noted that explicitly.

## The core verdict (from research, unchanged)

> Bring a real conversation → understand what happened → get one useful
> response strategy → practice the weak skill → improve the next real
> conversation.

The research's framing, which this plan accepts as-is: don't build a
smaller Duolingo or a prettier Gleam — this app's real-conversation loop is
already a sharper, more specific product than any of the 9 benchmarked
apps offer. The problem isn't the product loop, it's that the interface
doesn't yet look or feel like it knows that. Every recommendation below is
in service of making the *existing* loop feel like a calm, premium coach
instead of, in the research's words, "a capable internal tool."

I independently verified the research's most load-bearing technical claim
before trusting it: I grepped the entire `ios/SmallTalkCoach` source for
`withAnimation`, `.animation(`, `matchedGeometryEffect`, `@Namespace`, and
`accessibilityReduceMotion` — zero matches, anywhere. There is genuinely no
motion vocabulary and no Reduce Motion handling in the app today. Every
other screen-by-screen claim below was verified the same way, by reading
the actual file, not by trusting the summary.

---

## Quick wins (1-2 days)

Ordered so each item is buildable without waiting on a later one, except
where noted.

### 1. Design tokens foundation (`AppTheme`) — do this first

**New file**, e.g. `ios/SmallTalkCoach/AppTheme.swift`. Nothing like it
exists today — confirmed via a full file listing of `ios/SmallTalkCoach/`;
every current view reaches for raw system colors ad hoc (`CoachingView.swift`
alone uses `.blue`, `.teal`, `.orange`, `.pink`, `.purple`, `.red`, `.green`
directly and inconsistently across its `ReportCard`/`DimensionScoreRow`/
`ExampleResponseSuggestion` components).

- **Research rationale:** "No shared visual tokens, branded surface system,
  deliberate transition vocabulary... was found." Suggested palette: warm
  off-white background, confident indigo primary, coral/amber warmth
  accent, muted emerald success, four stable accessible skill colors (one
  per dimension: Warmth/Curiosity/Reciprocity/Flow). Suggested spacing:
  16-20 pt card padding, 12-16 pt vertical rhythm, 44×44 pt minimum tap
  targets.
- **Why first:** every other visual quick win below assumes this exists.
  Building the branded Today card or reordering the report before tokens
  exist means redoing the styling twice.
- **Scope:** semantic colors (including the 4 skill colors, tested in dark
  mode + Increased Contrast + Differentiate Without Color per the
  research's accessibility section), spacing/radius constants, named
  typography roles (display/title/cardTitle/body/helper/metric per
  research), and a first pass at the motion tokens from the Motion System
  section below (even if nothing animates yet — see item 6).

### 2. Branded Today header + elevated Daily Mission card

**Files:** `ios/SmallTalkCoach/HomeView.swift`, `ios/SmallTalkCoach/TodayCard.swift`.

Current state, verified by reading `TodayCard.swift` in full: it's a plain
`VStack` (streak line, target line, optional onboarding-emphasis line)
sitting inside `HomeView`'s `Section("Today")` — the only styling applied
is `.padding(.vertical, 4)`. It inherits the surrounding `List`'s default
row chrome and has no visual distinction from the "Your skills" or unit
rows around it.

- **Research rationale:** "Elevated Daily Mission card with duration,
  purpose, and one CTA" — and, more pointedly: "The first screenful must
  answer: What should I do, how long will it take, and why does it
  matter?" Today's card answers "what" (via the `NavigationLink` label)
  but has no duration estimate and no "why it matters" line beyond the
  conditional onboarding-emphasis text.
- **Concrete change:** wrap `TodayCard`'s content in a distinct elevated
  surface (using the new `CardStyle`/`AppSurface` tokens from item 1), add
  an expected-duration label per lesson (the content model likely doesn't
  carry this yet — flag as a possible content-schema gap during
  implementation, not something to guess at now), and make the primary
  action visually full-width per research's spacing guidance.

### 3. Explicit Coach mode cards: "Help me reply" / "Review my reply"

**File:** `ios/SmallTalkCoach/CoachingView.swift` (`CoachingComposeView`).

Current state, verified by reading the full compose form: the visible
`Picker(.segmented)` control selects **input source** (`CoachingCompositionMode`:
text vs. screenshot), not reply-mode. The actual mode distinction the
backend cares about (`stimulus_only` vs. `with_user_reply`, i.e. whether
the user includes their own reply) is conveyed only through placeholder
copy: *"Paste what THEY said for help replying. Add Me: lines to score
your reply."* A user has to already know the `Me:` convention.

- **Research rationale:** direct, specific finding — "The mode distinction
  is explained through helper text instead of a confident visual choice."
  Recommended replacement: "Start with two mode cards: Help me reply /
  Review my reply. Then offer source chips: Paste text, Import screenshot,
  Try an example."
- **Concrete change:** add an explicit mode selector (two cards) ahead of
  the existing text/screenshot picker, which becomes a secondary "how do
  you want to provide it" choice once a mode is picked. This doesn't
  change backend behavior — `main.py`'s `create_diagnosis` already infers
  mode from transcript content — it just makes an existing implicit choice
  visible and confident.

### 4. Reorder the coaching report: takeaway and next move before scores

**File:** `ios/SmallTalkCoach/CoachingView.swift` (`CoachingReportView`).

Current state, verified against the actual `List` section order in the
file: intro text → "What they're really saying" (interpretation) → "Your
reply, scored" (dimension scores, when shown) → "What's working"
(strengths) → "Try next" (improvements) → "How to respond" (guidance +
examples) → "Takeaway" → "Practice action" → "Recommended lesson." The key
takeaway is near the *end*, not the start.

- **Research rationale:** "Reveal the report as a narrative, not a
  dashboard: 1. Key takeaway... 2. Best next move... 5. Skill snapshot...
  Scores should be secondary. Never animate a score from zero as if the
  system has medical precision." This is close to a pure reorder of
  sections that already exist and already render conditionally
  (`CoachingReportDisplayModel.shouldShowScores` etc. already gate this
  correctly for `stimulus_only` vs `with_user_reply` mode) — the content
  logic is right, the presentation order is backwards.
- **Concrete change:** move `"Takeaway"` and the `"How to respond"`
  guidance/examples section to the top of the `List`, move `"Your reply,
  scored"` down near evidence/strengths. No backend or view-model change
  needed — this is section reordering inside one `List` in one file.

### 5. Skeleton loading states, richer empty states, copy toast, success haptics

**Files:** `HomeView.swift`, `CoachingView.swift` (`CoachingHistoryView`),
`ProfileView.swift`, `LessonDetailView.swift` — every one of these
currently uses bare `ProgressView("...")` and `ContentUnavailableView`
directly (verified in each file: `"Loading your learning path…"`,
`"Checking coaching…"`, `"Loading your skill profile…"`, `"Loading
history…"`, and the generic `ContentUnavailableView("No coaching reports
yet", ...)`).

- **Research rationale:** "Replace centered spinners with skeletons shaped
  like the final Today card, lesson rows, and report cards." For coaching
  history specifically: "show one sample report card and 'Analyze your
  first conversation.'" Also: "Copying a response produces a compact
  toast and light haptic."
- **A genuine gap the research assumes is already there and isn't:**
  `ExampleResponseSuggestion` in `CoachingReportView` renders response
  strategy examples as plain quoted text with **no copy-to-clipboard
  action at all** — there's nothing to attach a "copied" toast to yet.
  Adding the copy button is a prerequisite for this specific
  microinteraction, not just a styling pass.
- **Partial credit — don't over-claim this is all missing:** `ProfileView`'s
  empty state (`ProfileSummary.message`, "Bring a real conversation to
  Coaching to build your skill profile.") already has a concrete,
  non-generic CTA in its copy. The `ContentUnavailableView` *styling* is
  still generic, but the copy problem the research flags is already
  solved there — scope the empty-state work to `CoachingHistoryView` and
  loading states specifically, not a blanket rewrite.

### 6. Reduce Motion + XXL Dynamic Type scaffolding

**New file** (e.g. `MotionPolicy.swift`, per the research's component
plan) plus spot-checks across the views touched above.

- **Research rationale:** "Accessibility is part of the motion
  architecture, not a final audit." Read `accessibilityReduceMotion`
  centrally; replace travel/scale with opacity or immediate state changes.
- **Why this is a quick win despite depending on later motion work:**
  build the `@Environment(\.accessibilityReduceMotion)`-reading policy
  utility now, before there's much to gate, so every animation added in
  the deeper-redesign phase is required to go through it from day one
  rather than being retrofitted later.

### 7. Move the notification-permission prompt later in onboarding

**File:** `ios/SmallTalkCoach/OnboardingView.swift`.

Current state, verified: onboarding is already a 4-step flow (`goal` →
`context` → `baseline` → `reminder`), and the final `.reminder` step
embeds `ReminderSettingsControls`, which can trigger the real
`UNUserNotificationCenter` authorization prompt via
`ReminderSettingsViewModel.setEnabled` — before the user has completed a
single lesson or seen a single coaching report.

- **Research rationale:** "delay notification permission until value is
  clear" (paired with the paywall guidance: "Free onboarding and first
  lesson" comes before any permission or paywall ask).
- **Note on scope:** the research files this under the deeper "goal-based
  onboarding" item, but the onboarding *structure* is already goal-based
  and doesn't need rebuilding — only the notification-permission timing is
  wrong. That specific fix (drop or defer the `.reminder` step, prompt for
  it after first lesson completion instead) is small enough to belong
  here rather than in the deeper-redesign tier.

### 8. Empty-state copy pass for coaching history

**File:** `ios/SmallTalkCoach/CoachingView.swift` (`CoachingHistoryView`).

- **Research rationale:** "Coaching history: show one sample report card
  and 'Analyze your first conversation.'" Current empty state is a bare
  `ContentUnavailableView("No coaching reports yet", systemImage: "clock",
  description: Text("Your completed conversation analyses will appear
  here."))` — descriptive but passive, no CTA.

---

## Deeper redesigns (1-2 weeks)

### 1. Split navigation into Today / Learn / Coach

**Files:** `ios/SmallTalkCoach/RootView.swift` (currently exactly two
`tabItem`s: "Home" and "AI Coaching" in a plain `TabView` — verified),
`ios/SmallTalkCoach/HomeView.swift` (needs splitting), likely new
`TodayView.swift` and `LearnView.swift`.

- **Research rationale — this is the central structural recommendation:**
  "Move from two overloaded tabs to three focused destinations: Today
  (daily mission, streak/progress, due review, recent coaching follow-up),
  Learn (visual learning path, skill map, completed lessons, review
  access), Coach (real-conversation analysis, free-draft grading, and
  history). Keep Profile and Settings behind the top-right avatar. Every
  tab should have one job." Direct audit finding: "`RootView.swift`
  exposes only Home and AI Coaching, while Home combines Today, profile,
  reviews, and the entire curriculum in one long `List`" — confirmed
  exactly: `HomeView.body`'s `curriculumList` is one `List` with
  `Section("Today")`, `Section("Your skills")` (a `NavigationLink` row to
  the full `ProfileView`), a conditional `Section("Review due")`, and one
  `Section("Unit N")` per curriculum unit.
- **Non-obvious cross-reference worth flagging explicitly:** the
  research's "Coach" tab definition explicitly includes **free-draft
  grading** as one of its three jobs. Free-draft grading is this
  project's newest feature (shipped this session, backend
  `POST /lessons/{id}/draft-grading` plus `LessonDetailViewModel.gradeDraft`)
  — but its UI entry point lives inside `LessonDetailView`'s completion
  check, reached only through the *Learn* side of the app, not through
  Coaching at all. The feature itself doesn't need to change; this is a
  genuine IA mismatch between where it was built and where the research
  says it belongs. Worth a deliberate decision during implementation:
  either surface a link to a lesson's free-draft exercise from the new
  Coach tab, or accept that "free-draft grading" lives contextually inside
  a lesson (Learn) rather than inside Coach, and treat the research's
  grouping as aspirational rather than literal.
- **Profile relocation:** `ProfileView` and `ProfileSummaryRow` already
  exist and work — verified by reading `ProfileView.swift` in full — but
  are reachable *only* via a `NavigationLink` buried mid-`List` in
  `HomeView`. Moving Profile behind a top-right avatar is a new
  navigation affordance (doesn't exist anywhere in the app today), not a
  relocation of existing working code — the `ProfileView` content itself
  is reusable as-is.

### 2. Visual learning path (vertical path, node states)

**Files:** the new `LearnView.swift` from item 1, replacing `HomeView`'s
current `ForEach(curriculum.units) { Section(...) { ForEach(unit.lessons) {
...LessonRow/PremiumLessonRow... } } }` plain sectioned rendering.

- **Research rationale:** "Use a vertical path with alternating nodes, not
  a plain sectioned list. Node states: completed, current, review due,
  locked. Current node expands into a card with duration and CTA...
  Lock explanation should be specific: 'Complete 2 more lessons,' not just
  a lock icon." Component plan names this `LearningPathNode`.
- Current lock/unlock states are already computed correctly server-side
  and surfaced as plain text badges (`LessonRow`'s `badgeColor`/state
  text) — the *data* is right, only the visual representation needs to
  change from a list-with-badges to a path-with-nodes.

### 3. Step-based lesson flow with a persistent progress header

**File:** `ios/SmallTalkCoach/LessonDetailView.swift`.

Current state, verified by reading the full file (read in detail this
session for the free-draft-grading feature): a single `ScrollView` /
`VStack(spacing: 20)` renders every section at once — concept intro,
example, bad/better/best responses, quick exercise, practice, and the
completion check — with no step count, no pinned progress indicator, and
no per-step pacing.

- **Research rationale:** "Add a pinned progress header: Step 2 of 5...
  Break long lesson pages into paced steps rather than one large scroll...
  After a choice, animate the selected card into feedback and move focus
  to the explanation. Completion screen: learned skill, one real-world
  challenge, streak/progress update, next action." Component plan names
  `LessonProgressHeader` and `CompletionSummary`.
- This is the single largest individual-file redesign in this plan — it
  changes `LessonDetailView`'s fundamental content model from
  "show everything, scroll" to "reveal one step at a time." Recommend
  scoping this as its own worker cycle if/when this plan is approved,
  separate from the other deeper-redesign items.

### 4. Narrative report reveal (motion) + historical trend visualization

**Files:** `CoachingView.swift` (`CoachingReportView`, building on the
quick-win reorder from item 4 above by adding the actual reveal
sequencing/staggering) and `ProfileView.swift` (`dimensionContent`).

- **Research rationale:** "Report cards appear in a short 80-120 ms
  stagger, capped at 3-4 items... Use a short fill transition only after
  the textual interpretation appears." For trends: "one insight + one
  drill" result, "historical trend cards," component plan names
  `SkillMetricBar`.
- **Concrete current-state gap, verified:** `ProfileView.dimensionContent`
  renders dimension history as literal joined text — `Text("History: " +
  scores.map(String.init).joined(separator: " → "))`, i.e. a string like
  "History: 3 → 4 → 2". There is no chart, bar, or visual trend
  representation anywhere in the app today. This is a clean, well-scoped
  target for the `SkillMetricBar` component.

### 5. Sequence the paywall after value, not before

**Files:** `ios/SmallTalkCoach/PaywallView.swift`, `PurchaseManager.swift`,
`HomeView.swift` (`isPremiumGated`), `FeatureFlags.swift`.

Current state (all read in full this session, cycle 44): gating is a pure
unit-number cutoff — `LessonPaywallAccess.isGated(paywallEnabled:unit:isPremium:)`
gates Units 2-4 with no concept of "has this user seen a coaching result
yet." The paywall sheet presents the instant a gated lesson row is tapped.

- **Research rationale:** "Do not lead with the paywall. The user must
  experience the differentiating loop first... 1. Free onboarding and
  first lesson. 2. One example or limited real-conversation analysis. 3.
  Show the useful report and recommended lesson. 4. Paywall when the user
  asks for continued coaching, full history, or advanced practice."
- **Important boundary — this does not reopen a founder decision:** T-K's
  founder decision (`docs/planning/DECISIONS.md`, "T-K Paywall:
  Infrastructure Now, Pricing Deferred") already settled pricing and the
  flag-off-by-default posture; this item is about *trigger sequencing*
  once the flag is eventually turned on, not about pricing or whether to
  monetize. No new founder input is required to plan this; it would be
  required before actually flipping `FeatureFlags.paywallEnabled`.

### 6. Polished completion, streak, and milestone motion

**Files:** `TodayCard.swift` (streak flame/checkmark), `LessonDetailView.swift`
(lesson completion), the new `LearnView.swift` (unit completion).

- **Research rationale:** motion tokens table — `motionCelebrate` (≤1.2s,
  one-shot) for lesson/streak milestones; "Streak update uses a brief
  flame pulse; no full-screen celebration for ordinary daily completion.
  Major unit completion may use restrained confetti once." Depends on the
  token foundation from Quick Win #1 and the Reduce Motion scaffolding
  from Quick Win #6.

### 7. Preview/snapshot matrix for visual and accessibility states

Cross-cutting engineering practice, not a single screen: add `#Preview`
fixtures for loading, empty, locked, error, dark mode, reduced motion, and
XXL Dynamic Type as each component above gets rebuilt, per the research's
component-plan guidance ("Add previews for loading, empty, locked, error,
dark mode, reduced motion, and XXL Dynamic Type").

### 8. Five usability sessions with target users' own conversation examples

Not a code change. The research explicitly calls this out as part of the
"Deeper improvements" tier, and it's the only item in the whole report
that validates whether any of the above actually helps real users rather
than just looking better. Worth keeping on the backlog rather than
dropping it for being non-code.

---

## P2 — differentiated personality (explicitly deferred, do not start early)

- Lightweight coach identity/character — restrained, not the "avatar
  spectacle" the research explicitly warns against when discussing
  Praktika: "Avoid: High-cost avatar spectacle that distracts from real
  user conversations."
- Art-directed unit-completion transitions.
- Optional Lottie/Rive moments — research: "Consider later for a coach
  character, not for the first polish pass," and only "after profiling."
- Richer scenario previews / practice simulations. **Scope boundary:**
  this is about preview/context framing for existing coaching flows, not
  roleplay chat — actual conversational roleplay practice remains
  deferred per `docs/planning/COACHING_PIPELINE_V1.md` §7 and the Haiku-
  only budget lock; nothing here reopens that.

---

## Open-source dependencies: cross-checked against your own vetting rule

Your global rule (`~/.claude/CLAUDE.md`): "Check GitHub stars before
installing third-party skills/plugins: ≥1k fine, 100–1k read the source
first, <100 write in-house instead." Applying it to the research's own
reference table (star counts from `SOURCE_NOTES.md`, sampled 21 Jul 2026):

| Repository | Stars | Your policy | Research's own recommendation | Net |
|---|---:|---|---|---|
| EmergeTools/Pow | 4,337 | Fine | Best reference for state-change effects | Fine to adopt selectively |
| amosgyamfi/open-swiftui-animations | 5,549 | Fine | Inspiration catalog only | Don't install — reference only |
| markiv/SwiftUI-Shimmer | 1,684 | Fine | Good skeleton option | Fine to adopt |
| Juanpe/SkeletonView | 12,885 | Fine | UIKit-oriented; prefer native skeleton | Skip — build a small native `SkeletonBlock` instead |
| exyte/PopupView | 4,055 | Fine | Useful for toasts | Fine to adopt |
| exyte/AnimatedTabBar | 545 | **Read source first** | "Native `TabView` is safer" | **Converges: don't adopt.** Both your policy and the research land on native `TabView` for the 3-tab redesign |
| simibac/ConfettiSwiftUI | 2,436 | Fine | Unit milestones only | Fine, narrowly scoped |
| airbnb/lottie-ios | 26,800 | Fine | P2, after profiling | Deferred regardless of star count |
| rive-app/rive-ios | 804 | **Read source first** | "Later, after profiling" | **Converges: defer.** If picked up in P2, read the source first per policy before adding it |

Net effect: your own dependency policy independently confirms the
research's two most cautious recommendations (skip `AnimatedTabBar`, defer
`Rive`) without needing to relitigate them — both signals point the same
direction.

---

## Success metrics (from research, unchanged)

Track whether this improves behavior, not just visual preference:

- Onboarding completion; time to first completed lesson; time to first
  coaching report.
- Percentage of coaching reports that lead to the recommended lesson.
- Lesson completion and next-day return; weekly active learners
  completing 3+ meaningful actions.
- Coaching retry/abandonment rate.
- Paywall view-to-trial and trial-to-paid conversion, measured only after
  value exposure (once item 5 of the deeper redesigns ships).
- Accessibility-related support issues; crash/performance regressions.

**Flag for implementation time, not now:** most of this needs event
tracking that doesn't appear to exist in the backend today (no analytics/
event-logging module was found in `backend/app/` during this session's
work on other features). Instrumenting these metrics is itself a
prerequisite this plan doesn't currently account for — worth surfacing as
an explicit question when this plan is approved, not assumed away.

---

## What this plan does not include

Per the original request, this is analysis and prioritization only.
Nothing above has been implemented, no files have been changed, and no
worker cycle has been dispatched. The next step, if approved, is to work
through the quick-wins tier first via the established brain/worker loop,
one item at a time, in the order listed above.
