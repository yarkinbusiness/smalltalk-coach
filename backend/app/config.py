import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")
load_dotenv()  # allow a backend-local .env to override for dev convenience

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY not set. Add it to ~/.env (chmod 600) as "
        "ANTHROPIC_API_KEY=sk-ant-..."
    )

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROVISIONED_PATH = BACKEND_DIR / ".provisioned.json"
DB_PATH = BACKEND_DIR / "smalltalk_coach.sqlite3"

PARTNER_MODEL = os.environ.get("SMALLTALK_PARTNER_MODEL", "claude-sonnet-5")

# coach_coordinator is the "brain" — frontier model, does the actual
# synthesis judgment. The 4 graders are cheap/fast workers scoped to one
# narrow grading dimension each. Same cost-tiering principle as CMA's
# "Plan big, execute small" pattern (frontier coordinator, cheap workers),
# just without a web_search/web_fetch step — see ARCHITECTURE.md.
COORDINATOR_MODEL = os.environ.get("SMALLTALK_COORDINATOR_MODEL", "claude-fable-5")
WORKER_MODEL = os.environ.get("SMALLTALK_WORKER_MODEL", "claude-sonnet-5")


def load_provisioned() -> dict:
    """IDs written by scripts/provision_agents.py: environment + every agent's id/version."""
    if not PROVISIONED_PATH.exists():
        raise RuntimeError(
            f"{PROVISIONED_PATH} not found. Run "
            "`python -m scripts.provision_agents` once before starting the server."
        )
    return json.loads(PROVISIONED_PATH.read_text())


def save_provisioned(data: dict) -> None:
    PROVISIONED_PATH.write_text(json.dumps(data, indent=2))
