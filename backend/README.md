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

Endpoints include `GET /curriculum?user_id=...`, lesson reads and completions,
the coaching routes, and `GET /users/{user_id}/streak?tz=<IANA timezone>`.
