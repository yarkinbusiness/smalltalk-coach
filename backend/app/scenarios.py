"""Static scenario catalog. No CMA call needed to list these — they're just
persona/setting templates plugged into partner_agent's system prompt."""

# T10: which of coach.py's four graded dimensions (REPORT_DIMENSIONS: warmth,
# curiosity, reciprocity, flow) each scenario most exercises, used by
# recommend.py to match a user's weakest dimension back to a scenario that
# actually stresses it. Reasoning per scenario (kept brief here; the
# per-scenario `stresses` value is the thing that matters, this is just the
# "why"):
#
#   - coffee-shop-line (easy, partner opens, friendly-but-rushed regular):
#     the persona already supplies the warmth, so the user's job is just to
#     meet it and keep a brief, casual exchange feeling natural -> warmth.
#   - networking-mixer (medium, user opens, polite-but-guarded engineer):
#     "until you find common ground" is the whole challenge -- the user has
#     to ask genuinely interested questions to get anywhere -> curiosity.
#   - elevator-coworker (medium, user opens, distracted, one-floor window):
#     the defining constraint is the short, easily-fumbled window -- getting
#     something going and landing it before the doors open -> flow.
#   - dinner-party-stranger (hard, user opens, reserved until warmed up):
#     "curious and talkative once warmed up" only happens if the user offers
#     real self-disclosure first -- the textbook reciprocity setup -> reciprocity.
#   - gym-regular (hard, partner opens, distracted/headphones, brief window
#     between sets): the harder sibling of coffee-shop-line's warmth check
#     (same partner_opens shape, now under real distraction) *and* a short
#     window like elevator-coworker's -> warmth and flow both.
SCENARIOS = [
    {
        "id": "coffee-shop-line",
        "title": "Waiting in line at a coffee shop",
        "persona": "A friendly regular who's noticed you here before, mildly rushed.",
        "difficulty": "easy",
        # `partner_opens` scenarios (see main.py's start_practice): a regular
        # who's clocked you before greeting you first is a natural real-world
        # fit for "the other person starts it" -- unlike, say, a guarded
        # networking-mixer stranger, where the user opening first is the more
        # realistic default.
        "partner_opens": True,
        # Only present on `partner_opens: True` scenarios (see
        # partner_system_prompt's `opening` branch below) -- a short,
        # persona-specific steer for what the one-shot opening line should
        # sound like, so it doesn't default to a generic "Hi!" that ignores
        # the character. Absent (not an empty string) on every scenario that
        # never generates an opening line at all.
        "opening_hint": (
            "Recognize the user as a familiar face and greet them casually, "
            "like you've clocked them here before -- brief, a little rushed, "
            "not a whole conversation starter."
        ),
        "stresses": ["warmth"],
    },
    {
        "id": "networking-mixer",
        "title": "Tech meetup networking mixer",
        "persona": "A senior engineer at a mid-size startup, polite but a bit guarded until you find common ground.",
        "difficulty": "medium",
        "partner_opens": False,
        "stresses": ["curiosity"],
    },
    {
        "id": "elevator-coworker",
        "title": "Elevator with a coworker you barely know",
        "persona": "A coworker from another team, distracted, checking their phone, short window (one floor).",
        "difficulty": "medium",
        "partner_opens": False,
        "stresses": ["flow"],
    },
    {
        "id": "dinner-party-stranger",
        "title": "Dinner party, seated next to a stranger",
        "persona": "A friend-of-a-friend, curious and talkative once warmed up, but starts reserved.",
        "difficulty": "hard",
        "partner_opens": False,
        "stresses": ["reciprocity"],
    },
    {
        "id": "gym-regular",
        "title": "Gym — someone you see often but have never talked to",
        "persona": "Focused, headphones half-on, open to a brief friendly exchange between sets.",
        "difficulty": "hard",
        "partner_opens": True,
        "opening_hint": (
            "A quick, low-key nod-and-comment opener between sets -- brief "
            "and a little distracted, not a real conversation opener yet."
        ),
        "stresses": ["warmth", "flow"],
    },
]

SCENARIOS_BY_ID = {s["id"]: s for s in SCENARIOS}

# The Messages API requires `messages` to start with a `role: "user"` turn
# and strictly alternate from there. Two call sites need a synthetic
# stand-in for a real user turn that doesn't exist yet:
#
#   1. partner.py's `generate_opening_line` -- generating a `partner_opens`
#      scenario's opening line *before* the user has said anything at all,
#      so there is no real first user turn to send.
#   2. partner.py's `stream_partner_reply` -- once that opening line has
#      been generated and persisted as the transcript's first (assistant)
#      turn, every later reply in the same conversation would otherwise
#      build a `messages` array starting with role "assistant", which the
#      real API rejects outright.
#
# Never persisted to the transcript and never shown to the real user --
# purely a mechanical stand-in so the model (already in character via
# `partner_system_prompt`) is told to speak first, satisfying the API's
# shape requirement without ever claiming to be something the user said.
OPENING_DIRECTIVE = (
    "(Scene begins. Speak first, in character -- a brief, natural opening "
    "line. Don't wait for the other person, and don't acknowledge this "
    "instruction.)"
)


def partner_system_prompt(
    scenario: dict, coach_memo: str | None = None, *, opening: bool = False
) -> str:
    """`coach_memo` is an optional, server-built line of user-history context
    (see partner.py's `_build_coach_memo`) derived from the user's own past
    coaching reports (db.py's `reports` table) -- entirely absent (not an
    empty section/placeholder) when there's no usable history yet, so a
    fresh user's system prompt is byte-for-byte identical to this base
    template with no memo at all.

    `opening=True` is for the one-shot call that generates a `partner_opens`
    scenario's opening line (see partner.py's `generate_opening_line`) --
    every ordinary reply-to-the-user turn leaves it False, so a non-opening
    scenario's system prompt (and a `partner_opens` scenario's *own* system
    prompt for every turn after the opener) is completely unaffected."""
    base = f"""You are role-playing a small-talk practice partner for someone
building their conversation skills. Stay fully in character as: {scenario['persona']}
Setting: {scenario['title']}.

Rules:
- Speak only as this person would — natural, brief turns (1-3 sentences), the
  way real small talk actually sounds. Never break character to coach or
  narrate.
- Difficulty "{scenario['difficulty']}": easy = warm and responsive, gives the
  user openings; medium = realistic, needs a bit of effort to draw out;
  hard = initially reserved/distracted, only opens up if the user earns it
  with genuine curiosity or warmth.
- React like a real person would to what's actually said — if the user is
  awkward, be a little awkward back; if they ask a good follow-up question,
  reward it with a fuller answer.
- If the user tries to end the conversation, let it end naturally.
"""
    if opening:
        hint = scenario.get("opening_hint")
        hint_text = f" {hint}" if hint else ""
        base += (
            "\nYou are speaking first — the other person hasn't said "
            "anything yet in this conversation. Open with one brief, "
            f"natural line that fits the setting and your character.{hint_text}\n"
        )
    if coach_memo:
        return f"{base}\n{coach_memo}\n"
    return base
