# Smalltalk Coach — Lesson Content Model v1

## 1. Purpose, storage, and authoring approach

This is the technical lesson-content model the backend will serve for the
locked path in `LESSON_PATH_V1.md`. It encodes that path's six-part lesson
anatomy; it does not change the path, sequence, routing, or unlock rule.

**Storage:** each lesson is one static JSON file at
`content/lessons/<id>.json` from the repository root (for example,
`content/lessons/l01-first-hello.json`). Files are authored once, versioned
in git, and served as-is by the backend—never generated per user or request.

**Format:** JSON. It is standard-library parseable, needs no new dependency,
and is directly servable.

**Authoring approach:** a model may generate a draft under brain review, and
the founder may revise it. Generation happens once per lesson; the checked-in
JSON file is the artifact of record. Content teaches judgment and transferable
choices, not a perfect copy-paste reply, in line with the learning boundary in
`PRODUCT_BRIEF.md` §6.

## 2. Top-level lesson file schema

Each lesson file is one JSON object. The metadata mirrors
`LESSON_PATH_V1.md` §3; `unit` and `sequence` make the locked path position
explicit.

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | Required; start at `1`. |
| `id` | string | Required locked lesson id; equals filename without `.json`. |
| `title` | string | Required canonical title from the locked path. |
| `unit` | integer | Required, 1–4; equals the locked unit. |
| `sequence` | integer | Required, 1–12; equals the locked sequence. |
| `concept` | string | Required locked one-concept statement. |
| `skill_objective` | string | Required locked learner capability statement. |
| `dimensions` | string array | Required non-empty array drawn from `warmth`, `curiosity`, `reciprocity`, `flow`; equals the routing-table dimensions for this lesson. |
| `concept_intro`, `example`, `responses`, `exercise`, `practice`, `completion_check` | object | Required content blocks defined in §3. |

Worked top-level example (the block values are abbreviated below):

```json
{
  "schema_version": 1,
  "id": "l01-first-hello",
  "title": "First hello",
  "unit": 1,
  "sequence": 1,
  "concept": "Open with a simple greeting plus a small, shared-context cue instead of searching for an impressive line.",
  "skill_objective": "User can start a brief conversation with a new colleague or classmate using an observable cue from the moment.",
  "dimensions": ["warmth", "flow"],
  "concept_intro": { "text": "..." },
  "example": { "setting": "...", "dialogue": [{ "speaker": "You", "text": "..." }] },
  "responses": { "bad": { "text": "...", "explanation": "..." }, "better": { "text": "...", "explanation": "..." }, "best": { "text": "...", "explanation": "..." } },
  "exercise": { "prompt": "...", "options": [{ "text": "...", "feedback": "..." }], "correct_option_index": 0 },
  "practice": { "type": "Short roleplay", "scenario_setup": "...", "user_task": "..." },
  "completion_check": { "parts": [{ "kind": "choice", "question": "...", "options": [{ "text": "...", "feedback": "..." }], "correct_option_index": 0 }] }
}
```

## 3. Six content blocks

### `concept_intro`

Short, plain-language teaching text for the one concept.

| Field | Type | Rules |
| --- | --- | --- |
| `text` | string | Required, non-empty. |

Worked example:

```json
{ "text": "You do not need a clever opening. A warm hello plus one small thing you both can see gives the other person an easy place to respond." }
```

### `example`

A realistic office/campus situation: a required setting plus a short dialogue
or narration.

| Field | Type | Rules |
| --- | --- | --- |
| `setting` | string | Required, non-empty shared situation. |
| `dialogue` | object array | Required when `narration` is absent; every item has non-empty `speaker` and `text`. |
| `narration` | string | Required when `dialogue` is absent; non-empty. |

At least one of `dialogue` and `narration` is required; both are permitted.

Worked example:

```json
{
  "setting": "On a first morning at a new office, two people wait at the coffee machine before the team stand-up.",
  "dialogue": [
    { "speaker": "You", "text": "Hi, I am Maya. Does the coffee machine always take this long?" },
    { "speaker": "Colleague", "text": "Welcome, Maya. It is usually a little slow first thing." }
  ]
}
```

### `responses`

The required bad/better/best trio contrasts conversational effects; it is not
a set of scripts to memorize.

| Field | Type | Rules |
| --- | --- | --- |
| `bad`, `better`, `best` | object | All required; each has non-empty `text` and `explanation`. |

Worked example:

```json
{
  "bad": { "text": "I do not know anyone. What should I do around here?", "explanation": "It asks a new colleague to solve a broad personal problem before there is shared conversation." },
  "better": { "text": "Hi, I am Maya. I am new to the team.", "explanation": "It is warm and clear, but gives the other person little to pick up." },
  "best": { "text": "Hi, I am Maya. Is the coffee here worth the wait?", "explanation": "The shared, low-stakes moment offers an easy answer without asking for personal information." }
}
```

### `exercise`

A small deterministic decision exercise.

| Field | Type | Rules |
| --- | --- | --- |
| `prompt` | string | Required, non-empty. |
| `options` | object array | Required, two to four items; each has non-empty `text` and `feedback`. |
| `correct_option_index` | integer | Required zero-based in-range index into `options`. |

Worked example:

```json
{
  "prompt": "Which detail is a shared-context cue while you wait for coffee?",
  "options": [
    { "text": "The machine has a long line.", "feedback": "Correct: everyone waiting can observe it." },
    { "text": "You look tired.", "feedback": "This makes a personal assumption." }
  ],
  "correct_option_index": 0
}
```

### `practice`

A bounded practice scenario.

| Field | Type | Rules |
| --- | --- | --- |
| `type` | string | Required; matches the lesson's practice-scenario type in `LESSON_PATH_V1.md` §3. |
| `scenario_setup` | string | Required, non-empty. |
| `user_task` | string | Required, non-empty. |

Worked example:

```json
{
  "type": "Short roleplay",
  "scenario_setup": "You are at the coffee machine before your first team stand-up.",
  "user_task": "Write a greeting and add one small cue from this shared moment. Use your own words."
}
```

### `completion_check`

One or more parts that assess understanding. Every lesson must include at
least one deterministic `choice` part, so v1 can gate the next lesson
without model grading. An optional `free_draft` part asks the learner to
apply the idea, but its grading is explicitly deferred.

| Field | Type | Rules |
| --- | --- | --- |
| `parts` | object array | Required, non-empty, and contains at least one `choice` part. |
| `parts[].kind` | string | Required: `choice` or `free_draft`. |
| `parts[].question` | string | Required, non-empty for `choice`. |
| `parts[].options` | object array | Required for `choice`; two to four items, each with non-empty `text` and `feedback`. |
| `parts[].correct_option_index` | integer | Required for `choice`; zero-based in-range index. |
| `parts[].prompt` | string | Required, non-empty for `free_draft`. |
| `parts[].good_answer_demonstrates` | string | Required for `free_draft`; states intended evidence of understanding. |
| `parts[].grading` | string | Required for `free_draft`; exactly `deferred-v1`. |

Worked example:

```json
{
  "parts": [
    {
      "kind": "choice",
      "question": "Which opening uses a shared-context cue?",
      "options": [
        { "text": "Hi—this coffee machine is taking its time today.", "feedback": "Correct: its pace is observable to both people." },
        { "text": "Hi—why are you standing by yourself?", "feedback": "This makes the other person's situation personal." }
      ],
      "correct_option_index": 0
    },
    {
      "kind": "free_draft",
      "prompt": "Draft an opening for a shared waiting moment, then name the cue you used.",
      "good_answer_demonstrates": "A greeting plus an observable shared detail, with room for the other person to respond.",
      "grading": "deferred-v1"
    }
  ]
}
```

## 4. Validation rules on load

The backend will enforce these rules when loading lesson files:

1. The file parses as a JSON object and has every required top-level field and
   all six content blocks.
2. `schema_version` is the supported version (v1 is `1`), strings required
   by this model are non-empty, and unit/sequence are within their stated
   ranges.
3. The `id` matches the filename stem, exists in `LESSON_PATH_V1.md` §3,
   and its title, unit, sequence, concept, and skill objective exactly match
   that locked metadata.
4. `dimensions` has no duplicates, uses only the four allowed values, and
   exactly matches the routing-table rows in `LESSON_PATH_V1.md` §5 that
   contain the lesson id.
5. Every block meets §3's required fields and cardinality. `responses`
   contains exactly `bad`, `better`, and `best`.
6. Each exercise option and deterministic completion-check option includes
   feedback; every `correct_option_index` is an in-range integer.
7. `completion_check.parts` contains a valid `choice` part. Each
   `free_draft`, when present, has its prompt,
   `good_answer_demonstrates`, and exactly `"grading": "deferred-v1"`.

## Path manifest

`content/lesson_path.json` is the machine-readable locked path that the
backend loads before authored lesson files. It is a JSON object with:

- `schema_version`: supported manifest version (`1`).
- `lessons`: exactly twelve ordered lesson objects. Each has `id`, `title`,
  `unit`, `sequence`, `concept`, `skill_objective`, `dimensions`, and
  `practice_type`. `practice_type` is a non-empty string and must equal the
  authored lesson file's `practice.type`.
- `routing`: an object keyed by the four dimensions (`warmth`, `curiosity`,
  `reciprocity`, and `flow`), where every value is a non-empty lesson-id list.

The manifest is the source of truth for locked lesson metadata, lesson order,
routing membership, and practice type; each authored lesson file must agree
with it.

## 5. Deliberately out of scope

This schema marks free-draft grading as `deferred-v1`; it does not define
grading mechanics or passing thresholds beyond that marker. It also does not
define spaced-repetition scheduling, streaks, or authoring-pipeline tooling.
See `ARCHITECTURE.md`'s **“Deferred — not yet specified”** list for the
deferred design work.
