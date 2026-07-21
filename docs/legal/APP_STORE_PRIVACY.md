# App Store Privacy Mapping

**Prepared: 2026-07-21**

This is a working mapping for App Store Connect. It describes the current app
and its Anthropic coaching provider; update it if the app's practices change.

## Privacy Nutrition Label mapping

**Data Used to Track You: none.** The app has no ads, no analytics or tracking
SDKs, does not sell data, and does not combine its data with third-party data
for advertising or advertising measurement.

| Apple category | App Store Connect selection | What is collected | Purpose | Linked to user? |
| --- | --- | --- | --- | --- |
| User Content | Other User Content | User-submitted conversation text or screenshot content, extracted transcripts, AI coaching reports, and optional reflection notes | App Functionality; Product Personalization | Yes — linked to the app's persistent anonymous device-generated UUID |
| Usage Data | Product Interaction | Lesson and review completions and timestamps; onboarding goal, context, and four self-ratings | App Functionality; Product Personalization | Yes — linked to the app's persistent anonymous device-generated UUID |
| Identifiers | User ID | The anonymous device-generated UUID used to associate a device with its records | App Functionality | Yes — it is the link used for that device's records |

**Linked-data note.** Do not select “not linked to identity” merely because
there is no account, name, or email address. Apple defines linked data to
include data linked via a person's device. This app persistently associates the
listed records with its anonymous device-generated UUID, so this conservative
mapping marks them as linked. The UUID is not used for tracking.

| Apple categories not collected | Mapping |
| --- | --- |
| Contact Info | Not collected: name, email address, phone number, physical address, or other contact information. |
| Health & Fitness; Financial Info | Not collected. |
| Location; Contacts | Not collected. |
| Sensitive Info | Not intentionally collected as a category. A person may choose to include sensitive information in generic conversation content; that content is covered by Other User Content. |
| Browsing History; Search History; Purchases | Not collected. |
| Advertising Data; Other Usage Data | Not collected. |
| Diagnostics | Not collected. |
| Tracking identifiers / Data Used to Track You | None. The anonymous UUID is an app-functionality User ID, not an advertising identifier and not used to track users. |
| Audio Data; Gameplay Content; Customer Support; Surroundings; Body; Other Data Types | Not collected. |

## Third-party-AI disclosure audit (Apple guideline update, November 2025)

Apple's November 2025 clarification to App Review Guideline 5.1.2(i) requires
a clear disclosure of where personal data is shared with third parties,
including third-party AI, and explicit permission before sharing it.

### Current in-app copy

`ios/SmallTalkCoach/CoachingView.swift` currently shows this copy before the
submission button:

> “Your conversation text is sent to Anthropic, a third-party AI, for analysis.”
>
> “It may include another person’s words or identity. A successful analysis is stored on your own SmallTalk Coach backend, and you can delete it from History at any time.”
>
> “Only paste what you’re comfortable sharing.”
>
> Toggle: “I understand and consent”

The button is disabled unless the toggle is on. The backend also rejects a
coaching submission without `consent_to_process: true`.

### Assessment

For pasted-text coaching, the current copy meets the central elements of the
requirement: it appears before submission, names Anthropic, says that
conversation text is sent for analysis, and requires an affirmative consent
toggle.

### Follow-up — screenshot disclosure gap — RESOLVED 2026-07-21 (cycle 40)

Screenshot-mode consent copy now explicitly names Anthropic and states that
the screenshot image itself (not just extracted text) is sent for transcript
extraction and coaching analysis, shown before the consent toggle. Text-mode
copy is unchanged. Implementation: `CoachingDisclosureCopy.lines(for:)` in
`ios/SmallTalkCoach/CoachingView.swift`, keyed on the same composition-mode
state that already drives the input picker. Regression-tested (text-mode
copy asserted byte-identical; screenshot-mode copy asserted to contain both
"Anthropic" and an image reference).
