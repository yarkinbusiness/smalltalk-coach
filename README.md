# SmallTalkCoach

Practice small talk against a role-played AI partner, then get a coaching
report on the conversation. See [ARCHITECTURE.md](ARCHITECTURE.md) for the
full design and why it uses Claude Managed Agents (CMA) the way it does.

"SmallTalkCoach" is a placeholder name/bundle id (`com.yarkinyavuz.smalltalkcoach`)
— rename freely, it's not load-bearing anywhere.

## What's here

```
backend/   FastAPI service — scenario catalog, live chat relay, CMA coach
           coordinator, per-user memory store, sqlite for local session state
ios/       SwiftUI app — project.yml (xcodegen spec) + Swift sources
```

## Requirements you'll need to provide

- An Anthropic API key **with Claude Managed Agents (CMA) beta access**
  (`managed-agents-2026-04-01`). Without CMA access, agent/session/environment
  creation calls in `backend/scripts/provision_agents.py` will fail — the live
  chat path (`partner.py`) only needs a normal Messages API key, but the
  coaching-report path needs CMA specifically.
- **Xcode** (the full app from the App Store, not just Command Line Tools) to
  build/run the iOS target. This was scaffolded in an environment that only
  had Command Line Tools installed, so the iOS app has been syntax-checked
  (`swiftc -parse`) and the project file generated/validated with `xcodegen`,
  but never actually compiled or run in Simulator — see "What's been verified"
  below before assuming it builds clean on the first try.

## Backend setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Put your real key in ~/.env (chmod 600), never in this repo:
#   ANTHROPIC_API_KEY=sk-ant-...

python -m scripts.provision_agents   # creates/updates every CMA agent + environment,
                                      # writes backend/.provisioned.json
uvicorn app.main:app --reload --port 8000
```

Re-run `provision_agents.py` any time you edit a prompt in
`backend/app/agents_setup.py` — it's idempotent and only creates a new agent
version when the prompt text actually changed.

## iOS setup

```bash
brew install xcodegen   # already done in this session
cd ios
xcodegen generate        # regenerate any time project.yml or the file list changes
open SmallTalkCoach.xcodeproj
```

In Xcode: pick a simulator, hit Run. The app talks to `http://localhost:8000`
by default (`ios/SmallTalkCoach/Networking/APIClient.swift`), which the
Simulator can reach directly with no config.

**Testing on a physical device**: plain HTTP only works unmodified against
`localhost`/loopback under App Transport Security. Point `APIConfig.baseURL`
at your Mac's LAN IP and you'll need either an ATS exception in
`Info.plist`-equivalent build settings or to put the backend behind HTTPS
(e.g. a local Caddy/ngrok tunnel) — not wired up yet, deliberately left out of
this MVP scaffold.

## What's been verified vs. not, in this environment

Verified:
- Every CMA SDK method the backend calls (`client.beta.agents.*`,
  `client.beta.sessions.*`, `client.beta.environments.*`,
  `client.beta.memory_stores.*`) exists on the installed `anthropic` SDK
  (0.116.0) — checked with `hasattr`, not assumed from docs alone.
- The backend installs cleanly in a venv and boots: `GET /scenarios` and
  scenario-validation on `POST /practice/sessions` were hit directly with
  FastAPI's `TestClient` against a fake `.provisioned.json` and a dummy API
  key (no real network calls, no cost).
- Every backend `.py` file byte-compiles (`py_compile`).
- Every iOS `.swift` file parses (`swiftc -parse` — syntax only, no type
  checking against the SwiftUI/Foundation SDKs, since that requires Xcode).
- `xcodegen generate` produces a project file without error.

Not verified (needs a real CMA-enabled API key and/or Xcode):
- An actual end-to-end coaching-report run against live CMA (agent creation,
  the coordinator fanning out to its 4 workers, memory_store read/write).
- The iOS app actually compiling, running in Simulator, or a screenshot of
  any screen — this needs Xcode installed, which this machine doesn't have.
- The SSE relay (`/practice/sessions/{id}/message`) against a real streaming
  Messages API response.

Next real steps, in order: get a CMA-enabled key into `~/.env`, run
`provision_agents.py` and watch it succeed against the real API, then install
Xcode and do a first Simulator run of the chat flow end to end.
