"""Run once (and again any time a prompt in agents_setup.py changes):

    cd backend && python -m scripts.provision_agents

Creates/updates every CMA agent + the shared environment, and writes their
ids/versions to backend/.provisioned.json, which main.py reads at startup.
"""

from anthropic import Anthropic

from app.agents_setup import provision
from app.config import load_provisioned, save_provisioned


def main() -> None:
    try:
        state = load_provisioned()
    except RuntimeError:
        state = {}

    client = Anthropic()
    state = provision(client, state)
    save_provisioned(state)
    print("\nWrote backend/.provisioned.json:")
    print(state)


if __name__ == "__main__":
    main()
