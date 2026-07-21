# SmallTalk Coach Privacy Policy

**Effective date: 2026-07-21**

SmallTalk Coach is made available by **Yarkin Yavuz** (the data controller).
Questions about this policy or your data can be sent to
[yarkin.business@gmail.com](mailto:yarkin.business@gmail.com).

## What we collect

We do not use accounts. Instead, the app creates an anonymous device-generated
UUID so that the server can keep a device's records together. We do not ask for
or collect your name or email address.

### Stored on our server

Our server stores the following data in a SQLite database, associated with that
anonymous UUID:

- Lesson and review completions, including timestamps.
- Onboarding choices: your goal, office or campus context, and four 1–5
  self-ratings.
- Coaching submissions and results. For pasted text, this includes the
  conversation transcript. For a screenshot, it includes the transcript
  extracted from the screenshot. In both cases, it includes the AI coaching
  diagnosis report.
- Reflections: an outcome (`went_well`, `partly`, or `avoided`) and an optional
  note of up to 500 characters.

Reflection notes are not sent to an AI model, are not logged, and are not used
in profile aggregates.

### Stored on your device

The app keeps its anonymous device-generated UUID on the device. It also uses
UserDefaults for your reminder preference and time, whether onboarding is
complete, and a pending-reflection marker. These items stay on the device.

## What we do not collect

We do not collect your name, email address, contacts, or location. We do not
use advertising identifiers, advertising, tracking or analytics SDKs, and we
do not sell data.

## How AI coaching works

Coaching is optional. Before each coaching submission, you must turn on the
in-app consent toggle.

When you submit conversation text, we send it to **Anthropic**, our
third-party AI provider, to produce a coaching diagnosis. When you submit a
screenshot, we send the screenshot to Anthropic to extract a transcript and
produce the coaching diagnosis. This is the only third-party sharing described
in this policy; we do not share data with other third parties.

We do not store the raw screenshot image bytes on our server. They are deleted
immediately after transcript extraction. We do store the extracted transcript
and the resulting coaching diagnosis report.

## Other people in your conversations

A conversation you submit will often include another person's words and may
include their name or other identifying details. Please get that person's okay
before sharing the conversation, or crop or redact identifying details first.
SmallTalk Coach cannot verify that you have that person's permission.

## Retention and deletion

Your data is **kept until the user deletes it**. There is no automatic expiry
in v1.

You can delete an individual coaching report from History. That removes the
report and its stored transcript. You can also use the in-app **Delete all
coaching data** control. It deletes all coaching reports (including stored
transcripts and diagnoses) and reflections. It keeps lesson progress and
streaks.

To exercise any data rights, including a deletion request, email
[yarkin.business@gmail.com](mailto:yarkin.business@gmail.com).

## Security

Data is transmitted over HTTPS and stored on the app's server. No system can
promise perfect security, so please share only content you are comfortable
providing.

## Children

SmallTalk Coach is not directed to children under 13.

## Changes to this policy

If this policy changes, we will update this page and its effective date.

## Contact

The data controller is **Yarkin Yavuz**. Contact:
[yarkin.business@gmail.com](mailto:yarkin.business@gmail.com).
