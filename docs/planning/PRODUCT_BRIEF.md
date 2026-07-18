# Smalltalk Coach — Product Brief

## 1. Product Thesis

Smalltalk Coach helps people become better at starting, sustaining, and deepening real-world conversations.

The product is not primarily an AI reply generator. Its core value is a structured learning system that builds durable social skills over time. AI coaching supports that system by analyzing real situations, explaining what is happening, and directing the user to the most relevant lesson or practice.

**Core promise:** Get useful help in the moment, then learn the skill so you need less help next time.

## 2. User Problem

Many people want to connect more naturally but struggle with situations such as:

- Approaching someone new.
- Knowing what to say after the opening.
- Showing curiosity without sounding like an interviewer.
- Balancing speaking and listening.
- Reading tone, interest, warmth, or disengagement.
- Recovering from awkward moments.
- Moving from surface-level small talk to a meaningful conversation.

Existing AI reply tools often solve only the immediate message. They can create a short dopamine hit, but they do not build confidence, judgment, or transferable skills. This makes them easy to try and easy to abandon.

## 3. Product Goal

Create a subscription product users keep because they can see themselves becoming more socially capable over time.

The product should combine:

1. **A guided learning path** that teaches small-talk skills from basic to advanced.
2. **An AI coaching utility** that analyzes the user's real situations and connects them back to the learning path.

The learning path is the primary experience. AI coaching is the personalized bridge between real life and the curriculum.

## 4. Target Users

### Primary Persona — The Relocated Newcomer

*V1 target, locked 2026-07-17 as an Experiment — see `DECISIONS.md` ("V1 Target Segment: Relocation Wedge").*

- Early-career professional or student who moved to a new city or country for work or school within roughly the last 6 months.
- Forced into daily unfamiliar social situations at the office or on campus — the pain is frequent and unavoidable during the transition window.
- Wants two things at once: a real social circle and a strong start (colleagues, classmates, first impressions).
- Includes international students and new graduates; the primary payer (students vs professionals) is an open interview question.
- Positioning stays welcoming to all newcomers; this persona is who lessons and marketing are written for.

### Secondary Persona — The Situation-Specific User

- Arrives with a screenshot, written conversation, or description of a real interaction.
- Initially wants immediate help understanding what happened or what to do next.
- Can become a long-term user if the product reveals a repeatable skill gap and a clear path to improve it.

### Expansion Segments (not targeted in v1)

The general "Social Improver" (the broad social-confidence market, currently served shallowly by generic apps such as Gleam), other life transitions (post-breakup, post-isolation, retirement moves), professional networkers beyond the newcomer window, and non-native speakers as a distinct track. Dating-message generation remains a non-goal (see §11). Expansion happens only after the wedge validates per `VALIDATION_PLAN.md`.

## 5. Primary Experience — Guided Learning Path

The Home tab presents a fixed, progressive path similar to a language-learning course.

### Example Skill Progression

1. Starting a conversation.
2. Using the environment and context.
3. Asking open but natural questions.
4. Sharing enough about yourself.
5. Showing warmth and active listening.
6. Finding mutual topics.
7. Avoiding interview-mode conversation.
8. Handling silence and awkwardness.
9. Reading engagement and boundaries.
10. Deepening a conversation naturally.
11. Ending a conversation well.
12. Following up and building continuity.

### Lesson Structure

Each lesson should be short and active:

- One clear concept.
- A realistic example.
- A bad, better, and best response with explanation.
- A small decision or exercise.
- A short practice scenario.
- A completion check based on understanding, not only tapping through screens.

### Progression Principles

- Teach one behavior at a time.
- Revisit important skills through spaced repetition.
- Unlock later material through completion or demonstrated understanding.
- Show visible progress without turning the product into empty gamification.
- Reward real-world application, reflection, and improvement.

## 6. Secondary Experience — AI Coaching

The Coaching tab accepts:

- A screenshot of a conversation.
- Pasted text.
- A written description of an in-person interaction.
- A question about a social situation.

### Coaching Output

The AI should behave like a highly skilled small-talk coach and educator. It should:

1. Clarify the user's goal and context when necessary.
2. Explain what may be happening in the interaction.
3. Identify what the user did well.
4. Identify one or two high-impact improvements.
5. Give examples when useful, without taking over the interaction.
6. Recommend the most relevant lesson in the learning path.
7. Suggest one small practice action for the next real interaction.

### Learning Boundary

The AI must not default to writing the perfect response for the user.

When the user asks, “What should I reply?”, the coach should normally:

- Briefly explain the conversational goal.
- Offer two or three possible directions or frameworks.
- Ask the user to draft a response when practical.
- Improve the user's draft and explain why.
- Provide a direct example only when urgency, safety, accessibility, or user frustration makes it appropriate.

The product should optimize for **capability transfer**, not dependency.

## 7. Core Product Loops

### Learning Loop

Learn a concept → practice it → apply it in real life → reflect → strengthen or unlock the next skill.

### Coaching-to-Learning Loop

Submit a real situation → receive diagnosis → identify a skill gap → open the recommended lesson → practice → apply the skill in the next interaction.

### Progress Loop

Complete lessons → demonstrate skills across scenarios → see a personal skill profile improve → receive more relevant practice and coaching.

Every coaching session should end with a clear next step. When relevant, that next step should point to one specific lesson rather than vaguely telling the user to “practice more.”

## 8. Retention and Subscription Rationale

Users should keep the subscription because the product creates compounding value:

- A curriculum gives them unfinished progress and a reason to return.
- Real-life coaching makes the curriculum personally relevant.
- A skill profile shows strengths, recurring mistakes, and improvement over time.
- Practice creates confidence only after repetition, not one session.
- New real-life situations continuously create new coaching needs.
- The product becomes more useful as it learns the user's goals, patterns, and completed lessons.

Retention must come from visible personal growth, not artificial streak pressure alone.

### Early Subscription Hypothesis

- Free access should demonstrate the learning method and one useful coaching moment.
- Paid access can unlock the full path, deeper coaching history, personalized practice, and progress insights.
- Pricing should be tested early with real users; willingness to pay is a product signal, not a final-stage detail.

## 9. Key User Flows

### Flow A — New User Starts Learning

Onboarding → chooses a social goal → completes a short baseline assessment → receives a starting point → completes first lesson → practices a scenario → sees next lesson.

### Flow B — User Brings a Screenshot

Upload screenshot → confirm context and privacy → AI analyzes interaction → user receives diagnosis and improvement focus → app recommends a lesson → user opens lesson → completes targeted practice.

### Flow C — User Asks for a Reply

Paste interaction → AI identifies the intended outcome → gives response directions → user drafts → AI improves and explains → app links the issue to a reusable skill.

### Flow D — User Returns After Real Life

Select “How did it go?” → record a short reflection → AI identifies evidence of improvement or a repeated gap → update skill profile → recommend next lesson or practice.

## 10. V1 Scope

### Must Have

- Two-tab structure: Home and Coaching.
- One coherent beginner learning path.
- Short interactive lessons and practice scenarios.
- Screenshot and text-based coaching.
- Coaching output that recommends a relevant lesson.
- Basic progress tracking.
- Clear privacy explanation and deletion controls for sensitive conversations.
- Simple subscription/paywall experiment.

### Nice to Have Later

- Voice-based roleplay.
- Daily optional practice.
- Advanced personalized curriculum.
- Detailed longitudinal skill analytics.
- Community or peer practice.
- Multiple social contexts such as dating, networking, and workplace tracks.

## 11. Non-Goals

- Becoming a dating-message generator.
- Sending messages on the user's behalf.
- Maximizing the number of AI chats without evidence of learning.
- Replacing therapy or diagnosing mental-health conditions.
- Teaching manipulation, coercion, or deceptive social tactics.
- Launching with a large set of shallow content tracks.
- Building a complicated multi-agent system before the core learning loop is validated.

## 12. Safety and Trust Principles

- Treat screenshots and conversations as sensitive personal data.
- Obtain clear consent before storing content or using it for personalization.
- Make deletion easy and understandable.
- Avoid declaring another person's intent as fact; distinguish observation from inference.
- Respect rejection, boundaries, and disengagement.
- Do not coach harassment, pressure, impersonation, or manipulation.
- Escalate crisis, abuse, or self-harm content to appropriate safety guidance rather than social coaching.

## 13. Success Metrics

### Activation

- Percentage completing the first lesson.
- Percentage completing one practice scenario.
- Percentage receiving a useful coaching result.
- Percentage moving from coaching into a recommended lesson.

### Learning and Value

- Lesson completion and comprehension rate.
- Improvement between repeated practice attempts.
- Percentage of users reporting successful real-world application.
- Reduction in repeated errors for the same skill.

### Retention

- Week 1 and Week 4 retained users.
- Lessons or practices completed per active week.
- Percentage returning after a real-world interaction.
- Coaching-to-lesson conversion rate.
- Paid monthly retention and cancellation reasons.

### Business

- Free-to-paid conversion.
- Trial-to-paid conversion.
- Monthly subscription retention.
- AI cost per active paid user.
- Gross margin after model and media-processing costs.

Avoid using raw message count as the primary success metric. High usage can mean engagement, confusion, or dependency; it does not prove skill improvement.

## 14. Lightweight Product Scorecard

Score each major feature or product decision from 1 to 5.

| Criterion | Key Question |
|---|---|
| User pain | Does this solve a frequent and meaningful problem? |
| Learning impact | Does it improve a transferable skill? |
| Retention potential | Does it create a natural reason to return? |
| Differentiation | Is it meaningfully better than an AI reply generator? |
| Simplicity | Can users understand and use it quickly? |
| V1 feasibility | Can a small team build and test it soon? |
| Willingness to pay | Is the outcome valuable enough to support a subscription? |
| Trust and safety | Can it be delivered without unacceptable privacy or behavior risk? |

### Decision Rule

- Prioritize ideas that score highly on user pain, learning impact, and retention.
- Reject or redesign ideas that create dependency without skill transfer.
- Defer features that increase technical complexity before proving user demand.
- Treat a low willingness-to-pay score as a discovery problem to investigate, not something to hide with more features.

## 15. Critical Assumptions to Validate

1. Users want to improve small-talk skills, not only receive immediate replies.
2. A meaningful subset will complete structured lessons repeatedly.
3. Screenshot coaching can convert urgent intent into curriculum engagement.
4. Users will trust the product with sensitive social content.
5. Users can perceive improvement within the first one or two weeks.
6. The product can create enough recurring value to justify a subscription.
7. One narrow initial audience has a stronger need than the general population.

## 16. Open Discovery Questions

### Audience

- Initial segment resolved 2026-07-17: Relocated Newcomers (see `DECISIONS.md`). Remaining sub-questions:
- Within the wedge, who is the primary payer — students or early-career professionals?
- Which relocation moment has peak pain: arrival week, first month, or the first workplace/campus social event?
- In which situations does the Relocated Newcomer most fear “not knowing what to say”?

### Behavior

- What do users do today when a conversation goes badly?
- Will they practice before a situation, reflect afterward, or only seek help during it?
- What makes users abandon existing coaching or self-improvement apps?

### Learning

- What is the smallest lesson that creates an observable improvement?
- How should the product assess real understanding without feeling like school?
- Which skill categories best predict better conversations?

### Coaching

- How much direct reply assistance is useful before it reduces learning?
- What context does the AI need to avoid shallow or incorrect advice?
- How should it communicate uncertainty about another person's intent?

### Business

- What first paid outcome is compelling enough to purchase?
- Should payment center on curriculum access, personalized coaching, or both?
- What price range signals serious value while remaining accessible to the target user?

## 17. Recommended Next Validation Steps

1. Interview 10–15 Relocated Newcomers per `VALIDATION_PLAN.md`, including a willingness-to-pay probe.
2. Collect specific recent conversation problems, not general opinions about confidence.
3. Test a manual prototype: one short lesson, one screenshot analysis, and one lesson recommendation.
4. Observe whether users complete the recommended lesson without being pushed.
5. Ask for payment or a real preorder signal before building a broad curriculum.
6. Confirm the segment lock and choose the v1 lesson path based on behavior, not enthusiasm alone.

