# SmallTalk Coach — Coaching Pipeline V1

## 1. Purpose and relationship to `ARCHITECTURE.md`

**Purpose:** This is the backend implementation contract for the AI Coaching
tab's screenshot/text → diagnosis → lesson-recommendation loop: inputs,
records, API responses, model boundaries, and test requirements.

The loop remains the one in `ARCHITECTURE.md`: coaching explains a real
interaction, identifies a skill gap, and terminates in a Home-tab lesson. It
is a supporting utility for structured learning, not a standalone reply
generator.

### V1 simplification

`ARCHITECTURE.md` describes a CMA coordinator with four specialist workers.
V1 deliberately uses **plain Anthropic Messages API calls only**: one bounded
vision-extraction call for an image, then one bounded structured diagnosis
call. It provisions no CMA agents, sessions, environments, or memory stores.
The founder's standard test key must be sufficient; CMA beta access is not
assumed.

This follows the architecture document's pattern discipline: use a mechanism
only where its machinery earns its cost. For a short, tool-free,
request-scoped job, CMA coordinator/session machinery and sandbox lifecycle do
not earn that cost before the core loop is validated.

**Upgrade path:** Keep the API and JSON shapes below. CMA can later replace the
single diagnosis call with the same warmth/curiosity/reciprocity/flow fan-out
and synthesis. Normalization, validation, deterministic routing, storage, and
response assembly stay in the backend, so clients and lesson ids do not change.
### Scope and boundaries

- Coaching accepts pasted conversation text or one chat screenshot.
- `content/lesson_path.json` is the authoritative routing table; existing
  SQLite lesson-completion data provides progress.
- V1 has no longitudinal profile, model memory, or streak logic.
- Model ids are **not pinned** here; implementation selects current ids from
  current API documentation.

## 2. Pipeline stages and data contracts

### 2.1 Stage 1 — input normalization

The request has exactly one source: `text` or `screenshot`. Text receives no
model call: trim it, reject empty content, parse supplied speaker labels, and
otherwise produce one `unknown` speaker turn. A screenshot makes one
vision-extraction Messages API call and becomes the same transcript shape.
Diagnosis receives only this transcript, never raw image bytes.

```json
{
  "schema_version": 1,
  "source_kind": "text",
  "user_speaker_id": "user",
  "turns": [
    { "index": 0, "speaker_id": "user", "speaker": "user", "text": "I just moved here last week.", "source": "pasted" },
    { "index": 1, "speaker_id": "other", "speaker": "other", "text": "How are you finding it?", "source": "pasted" }
  ]
}
```

Transcript invariants:

- `schema_version` is `1`; `source_kind` is `text` or `screenshot`; `turns`
  is non-empty, ordered, has contiguous zero-based `index` values, and has
  non-empty trimmed text.
- `speaker` is `user`, `other`, or `unknown`; `speaker_id` is a stable local
  label. If attribution is unknown, `user_speaker_id` is `null` and the
  backend does not guess.
- Turn `source` is `pasted` or `vision`. Vision may add `unreadable_regions`
  containing visible-region descriptions only, never reconstructed text.

For screenshots, `user_message_side` is `left`, `right`, or `unknown`. It is a
user assertion for mapping bubbles to `user`/`other`. When unknown, attribution
remains unknown; names, avatars, gender, and tone must not be used to infer it.
### 2.2 Stage 2 — one structured diagnosis call

Submit the validated transcript to one mid-tier Claude Messages API call.
“Mid-tier Claude” is the candidate class recorded in `ARCHITECTURE.md`, not a
model id. Validate returned JSON before storage or routing; malformed output is
an upstream failure, never a partial report.

Per the product decision **“2026-07-19 — Coaching Is Response-Oriented (Teach
the User to Fish)”**, the contract has two modes: `stimulus_only` when no
user-attributed turn exists, and `with_user_reply` when one does.

```json
{
  "schema_version": 1,
  "mode": "with_user_reply",
  "incoming_interpretation": {
    "tone": "Warm and interested",
    "intent": "The other person is inviting the user to share their experience",
    "response_goals": "Answer with one concrete detail and create an easy next thread"
  },
  "response_coaching": {
    "guidance": "Acknowledge the question, give one specific detail, then invite a related exchange.",
    "example_responses": ["It has been a fun adjustment so far — I found a great coffee shop nearby. Have you lived here long?"]
  },
  "transferable_takeaway": "Concrete details plus one related question keep early conversations easy to continue.",
  "focus_dimension": "reciprocity",
  "dimensions": {
    "warmth": { "score": 3, "observations": [{ "kind": "observation", "text": "The user gives a concrete opening detail.", "turn_indices": [0], "quotes": ["I just moved here last week."] }] },
    "curiosity": { "score": 3, "observations": [] },
    "reciprocity": { "score": 2, "observations": [] },
    "flow": { "score": 3, "observations": [] }
  },
  "strengths": [{ "text": "You gave a concrete detail that gives the other person something to respond to.", "turn_indices": [0], "quotes": ["I just moved here last week."] }],
  "improvements": [{ "dimension": "reciprocity", "priority": 1, "kind": "suggestion", "text": "After answering, add one related question to return space to them.", "turn_indices": [0], "quotes": ["I just moved here last week."] }],
  "small_practice_action": "In your next short chat, answer with one detail and ask one related follow-up.",
  "safety": { "status": "clear", "category": null }
}
```

Schema rules:

- Every payload has non-empty `incoming_interpretation` (`tone`, `intent`, and
  `response_goals`), `response_coaching` (`guidance` plus one or two short
  `example_responses`), `transferable_takeaway`, and a four-dimension
  `focus_dimension`.
- In `stimulus_only`, `dimensions` is `null`, `focus_dimension` is a free
  coaching focus, and `improvements` may be empty. The output interprets the
  most recent other-party message and teaches how to build the reply; it never
  scores the stimulus.
- In `with_user_reply`, `dimensions` is exactly `warmth`, `curiosity`,
  `reciprocity`, and `flow`; each integer `score` is 1 (strongest need) through
  5 (strongest evidence). `focus_dimension` must be the weakest score, using
  the fixed `warmth`, `curiosity`, `reciprocity`, `flow` tie-breaker.
- In `with_user_reply`, every dimension observation, strength, and improvement
  can cite only user-attributed turn indices. Present transcript `quotes` are
  verbatim substrings of their referenced turns; an empty `quotes` array is
  permitted for claims about missing behavior.
- `kind` is `observation`, `inference`, or `suggestion`. Inference language is
  conditional; scores never claim another person's private intent.
- Return zero to three strengths and one or two uniquely prioritized
  improvements when scoring a user reply. Under root `DECISIONS.md`
  “2026-07-19 — Coaching Models Locked to Haiku 4.5 Only,” the backend
  tolerates model over-returns: it keeps the top two improvements by priority
  (then renumbers them) and the first three strengths. The practice action is
  one safe transferable action, not a message to send.
- Do not return lesson ids, lesson titles, routes, completion state, or a
  direct-answer field. `safety.status` is `clear` or `escalate`; escalation
  categories are `crisis`, `self_harm`, `abuse`, or `other`.
### 2.3 Stage 3 — deterministic weakest-dimension routing

The backend, never the model, reads the user's completed lesson ids and the
loaded manifest `routing` map.

1. For `with_user_reply`, choose the lowest validated dimension score. For
   `stimulus_only`, use the validated model-provided `focus_dimension` and
   label the selection reason `focus_dimension`, per **“2026-07-19 — Coaching
   Is Response-Oriented (Teach the User to Fish)”**.
2. In the scored path, break a score tie with this fixed order: `warmth`, `curiosity`,
   `reciprocity`, `flow`. The result is stable across retries and independent
   of model prose ordering.
3. Choose the first uncompleted id in `routing[weakest_dimension]`. The
   manifest row order is the curriculum's “earliest” order.
4. If that user completed every id in the row, choose its first id as a
  targeted review; completion is not permanent mastery.
Load title, concept, and objective by id from the manifest. A missing routing
row or lesson is a configuration error: fail closed, never fall back to model
selection.

```json
{
  "weakest_dimension": "reciprocity",
  "selection_reason": "lowest_score",
  "lesson": {
    "id": "l04-answer-and-return",
    "title": "Answer, then return",
    "concept": "Give a brief answer with one useful detail, then return a related question so the exchange has two active participants.",
    "skill_objective": "User can respond to a casual question without either stopping at one word or taking over the conversation.",
    "recommendation_kind": "new"
  }
}
```

### 2.4 Stage 4 — response assembly and persistence

Combine validated diagnosis, deterministic route, and manifest metadata. After
a successful non-escalation diagnosis, store the normalized transcript and
assembled report locally in SQLite. Never store raw image bytes, filenames,
EXIF data, or image URLs.

The report record is `id`, `user_id`, `created_at`, `source_kind`,
`transcript_json`, `diagnosis_json`, `weakest_dimension`, `lesson_id`, and
`practice_action`. It renders/deletes one report; it is not a v1 skill profile.
## 3. API surface and failure behavior

### `POST /coaching/diagnoses`

As with the current curriculum endpoints, require caller-supplied `user_id`.
`consent_to_process` must be `true` before third-party AI receives content.

```json
{
  "user_id": "8df3d0cb-5e4b-4b9d-a8f2-b1c04f1d68f2",
  "consent_to_process": true,
  "source": { "kind": "text", "text": "Me: I just moved here last week.\nThem: How are you finding it?" }
}
```

Screenshot `source`:

```json
{
  "kind": "screenshot",
  "media_type": "image/png",
  "image_base64": "<base64 image bytes>",
  "user_message_side": "right"
}
```

Accept only PNG, JPEG, and WebP and enforce a documented size limit before
decode. An image without usable chat content is rejected, not coached from
decoration or avatars.

**Text is synchronous:** a valid request returns `201 Created` with the final
report. It has only one bounded diagnosis call, so this is the fast path for a
pasted exchange.

**Screenshots are asynchronous:** a valid request returns `202 Accepted` and
a polling resource because decode, vision, and diagnosis have variable combined
latency. Raw bytes live only in process memory while the job runs, and are
discarded after vision normalization, on failure, and on process restart. V1
has no durable image queue; a restart fails the job and requires re-upload.

```json
{ "job_id": "cj_01J...", "status": "processing", "poll_url": "/coaching/diagnoses/jobs/cj_01J..." }
```

### `GET /coaching/diagnoses/jobs/{job_id}`

Require `user_id` as a query parameter. Return `200` plus
`{ "status": "processing" }` while work remains, or `200` plus the final
report when complete. Unknown/not-owned jobs return `404`.

### Final report response

```json
{
  "id": "cr_01J...",
  "status": "completed",
  "transcript": { "schema_version": 1, "source_kind": "text", "turns": [] },
  "diagnosis": { "schema_version": 1, "dimensions": {}, "strengths": [], "improvements": [] },
  "recommendation": { "weakest_dimension": "reciprocity", "selection_reason": "lowest_score", "lesson": { "id": "l04-answer-and-return", "title": "Answer, then return", "recommendation_kind": "new" } },
  "practice_action": "In your next short chat, answer with one detail and ask one related follow-up."
}
```

The full response uses the complete transcript, diagnosis, and lesson shapes
in §2; the client deep-links by lesson `id` to the existing lesson endpoint.

### `DELETE /coaching/reports/{report_id}`

Require `user_id`; delete that user's report and transcript in one SQLite
transaction. Return `204` on success and `404` when absent/not owned. V1 UI
must expose this near the report. Account-wide deletion is deferred.

### Error taxonomy

| Status | Code | When | Client behavior |
| --- | --- | --- | --- |
| 400 | `consent_required` / `invalid_request` | Missing consent or invalid/conflicting source fields | Explain what is needed; do not process. |
| 413 / 415 | `image_too_large` / `unsupported_image_type` | Image exceeds limit or type is rejected | Ask for a smaller PNG/JPEG/WebP image. |
| 422 | `bad_image` | Bytes cannot decode or are not one usable chat screenshot | Ask for a clearer original screenshot. |
| 422 | `unreadable_transcript` | Empty/too-short text or insufficient reliable extraction | Ask to paste or re-upload; never invent turns. |
| 422 | `coaching_refused` | Policy/model cannot safely provide social coaching | Return a brief boundary, not raw provider detail. |
| 502 / 503 | `ai_unavailable` | Timeout, upstream failure, or invalid schema after bounded retry | Store no partial report; invite retry. |
| 200 | `safety_guidance` status | Crisis, self-harm, or abuse detected | Return immediate safety guidance, not a diagnosis/lesson. |

Never return raw provider errors, prompts, API keys, base64 images, or another
user's report in an error response or log.

## 4. Prompt design outlines

Prompts are versioned in application source at implementation time; final
prose and model ids are intentionally not fixed here.

### Vision-extraction prompt requirements

- Transcribe visible chat only into the transcript schema; do not coach,
  summarize, infer emotion, or recommend a reply.
- Preserve readable wording, punctuation, emoji, order, and visible
  bubble/speaker attribution. Mark unreadable material; never repair it from
  context.
- Use only the caller-declared left/right side for user mapping. Do not derive
  identity from avatars, contact names, gender, or assumptions.
- Ignore chrome, notifications, ads, and profile imagery; retain timestamps
  only when necessary for visible message order. Return JSON only.

Per `ARCHITECTURE.md`, **Claude Haiku 4.5 leads but is unvalidated on real chat
screenshots.** Candidates considered were Kimi K2.5/K2.6/K2.7, GLM-5.2,
Claude Haiku 4.5, and GPT-5.6 Luna. DeepSeek V4 Pro/Flash is ruled out because
its public developer API lacked vision support. This document pins no model id.

### Diagnosis prompt requirements

- Be a small-talk coach/educator, not a dating-message generator, therapist,
  intent detector, or agent that sends messages.
- Receive only normalized transcript and minimal context, never image bytes or
  a lesson manifest; do not select a lesson id.
- Return only the required JSON. Score all four dimensions, quote exact turns,
  and make claims only supported by the input.
- Separate observation from inference; frame interpretations conditionally and
  never state another person's intent, interest, consent, or emotion as fact.
- Identify zero to three strengths and one or two high-impact, non-manipulative
  improvements. Respect disengagement and never advise pressure, harassment,
  impersonation, or deception.
- Enforce the Learning Boundary: do not produce a ready-to-send perfect reply
  by default. Use goals, directions/frameworks, or improvement of the user's
  draft. Direct examples are exceptional (urgency, safety, accessibility, or
  user frustration) and remain explanatory, not copy-paste end states.
- Return one transferable practice action. Set `safety` to `escalate` for
  crisis, abuse, or self-harm rather than attempting social coaching.

## 5. Safety, privacy, and key handling

Before submission, clearly disclose that transcripts/screenshots go to a
third-party AI provider for analysis and may contain another person's identity
and words. Name the purpose, say raw images are not stored server-side, link
to deletion, and require `consent_to_process` on every submission (or a later,
revocable saved preference).

V1 stores successful normalized transcripts and reports locally in SQLite so a
user can revisit/delete a report. It does not persist raw image bytes. Logs
contain report/job ids and error codes only, never transcripts, report prose,
names, images, or provider payloads. `DELETE /coaching/reports/{report_id}`
deletes the transcript and report.

For crisis, self-harm, or abuse, stop diagnosis and routing. Return immediate
safety guidance and encourage appropriate local emergency, crisis, or abuse
support. Do not diagnose mental health, speculate about danger, or offer
confrontation/pressure tactics. The same refusal boundary covers harassment,
coercion, manipulation, and impersonation.

`ANTHROPIC_API_KEY` is read from process environment only. Its value is never
in specs, source, git, fixtures, logs, errors, or generated artifacts. Unit
tests mock the API client; only §6's opt-in smoke test may make a live call.

## 6. Testing and validation strategy

All normal tests mock Anthropic and run without an API key or network access.

- **Normalization:** speaker labels/unlabeled text, whitespace, invalid source,
  side mapping, image type/decode failures, insufficient extraction, and raw
  image disposal. Assert diagnosis receives transcript, never bytes.
- **Diagnosis adapter:** valid payload plus missing dimensions, invalid scores,
  bad quotes/indexes, too many improvements, lesson-id output, ready-to-send
  default output, malformed JSON, refusal, and upstream failures.
- **Routing:** every manifest row; lowest score, every tie under fixed order,
  earliest incomplete selection, completed-row review fallback, and broken
  manifests failing closed. Model mocks never determine the lesson id.
- **Endpoint/storage:** text `201`, screenshot `202`/polling, ownership,
  deletion, consent failure, no report on error, no raw image in SQLite, and
  every taxonomy response.
- **Safety:** escalation suppresses report persistence/routing; coercion and
  harassment never produce tactics; observation/inference language differs.

Provide one `live_smoke` test, skipped by default. It runs only when a clearly
named opt-in environment flag **and** `ANTHROPIC_API_KEY` exist; it uses a
non-sensitive synthetic pasted transcript, checks schema-valid Messages output,
prints neither input nor credentials, and stores no report/image.

Before pinning the vision model, run an empirical quality evaluation on
consented representative real chat screenshots: small bubbles, avatars,
contrast variation, emoji, and both message sides. Record a pass threshold for
readable-turn recall, fidelity, order, and attribution; manually inspect
failures. Haiku 4.5 cannot be pinned from candidate status or synthetic smoke
results alone.

## 7. Deliberately deferred

- Longitudinal profile, cross-report trend analysis, and model memory.
- CMA coordinator/four-worker upgrade, provisioning, versioning, sessions,
  environments, and memory stores.
- Streaks, reminders, notification cadence, and coaching-to-streak rules.
- iOS Coaching-tab specifics: picker, transcript confirmation/editing, polling
  presentation, disclosure layout, report display, and lesson deep links.
- Talk-with-the-coach, daily roleplay, reply-specific modes, account-wide
  coaching deletion, retention windows, and authentication beyond current
  caller-supplied `user_id`.
