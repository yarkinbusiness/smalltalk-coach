# Smalltalk Coach backend

Run the server from the repository root:

```sh
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Run the tests:

```sh
backend/.venv/bin/python -m pytest backend/tests -q
```

The v1 API has no authentication: callers supply a non-empty `user_id`. This
is a known hardening gap and must be replaced before exposing the service to
untrusted clients.

Endpoints include `GET /curriculum?user_id=...`, lesson reads, completions,
and review submissions, the coaching routes, `GET /users/{user_id}/streak?tz=<IANA timezone>`,
`GET /users/{user_id}/review-queue?tz=<IANA timezone>`, and
`GET /users/{user_id}/profile`, plus reflection creation and history at
`POST`/`GET /users/{user_id}/reflections`, and onboarding at
`POST`/`GET /users/{user_id}/onboarding`. `DELETE /users/{user_id}/coaching-data`
removes coaching reports (including transcripts) and reflections while keeping lesson progress.
