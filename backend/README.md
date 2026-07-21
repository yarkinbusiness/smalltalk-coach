# Smalltalk Coach backend

Run the server from the repository root:

```sh
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Run the tests:

```sh
backend/.venv/bin/python -m pytest backend/tests -q
```

Authentication is opt-in for local development. Set `SMALLTALK_API_TOKEN` to
require `Authorization: Bearer <token>` on every route except `GET /health`;
when it is unset (the default), the API remains unauthenticated and must not
be exposed to untrusted clients. `SMALLTALK_COACHING_RATE_LIMIT` (default
`10`) and `SMALLTALK_COACHING_RATE_WINDOW_SECONDS` (default `60`) set the
per-user fixed-window limit for `POST /coaching/diagnoses`.

Endpoints include `GET /curriculum?user_id=...`, lesson reads, completions,
and review submissions, the coaching routes, `GET /users/{user_id}/streak?tz=<IANA timezone>`,
`GET /users/{user_id}/review-queue?tz=<IANA timezone>`, and
`GET /users/{user_id}/profile`, plus reflection creation and history at
`POST`/`GET /users/{user_id}/reflections`, and onboarding at
`POST`/`GET /users/{user_id}/onboarding`. `DELETE /users/{user_id}/coaching-data`
removes coaching reports (including transcripts) and reflections while keeping lesson progress.

Privacy Policy, Terms of Service, and App Store privacy mapping: [`docs/legal/`](../docs/legal/).
