"""Fake `anthropic.Anthropic` test double.

Mirrors exactly the surface area `app/*.py` actually calls (found via
`grep -rn "client\\.\\(beta\\|messages\\)\\." app/ scripts/`):

  - client.messages.stream(model=, max_tokens=, system=, messages=)
        -> context manager with `.text_stream`                         (partner.py)
  - client.messages.create(model=, max_tokens=, system=, messages=)
        -> object with `.content` (list of blocks with `.type`/`.text`)
                                                     (partner.py's generate_opening_line)
  - client.beta.sessions.create(agent=, environment_id=, resources=)
        -> object with `.id`                                           (coach.py)
  - client.beta.sessions.events.stream(session_id)
        -> context manager yielding fake event objects                 (coach.py)
  - client.beta.sessions.events.send(session_id, events=)               (coach.py)
  - client.beta.memory_stores.create(name=, description=)
        -> object with `.id`                                           (memory.py)
  - client.beta.memory_stores.memories.create(memory_store_id=, path=, content=)
                                                                         (memory.py)
  - client.beta.agents.create(**kwargs) -> object with `.id`/`.version`
  - client.beta.agents.update(id, **kwargs) -> object with `.id`/`.version`
  - client.beta.environments.create(name=, config=) -> object with `.id`
                                                                  (agents_setup.py)

Every call is recorded in a `*_calls` list so tests can assert on exactly
what was sent. Responses are configurable per test via the `queue_*()`
methods rather than one hardcoded canned response — queue either:
  - a plain value (list of str chunks / fake events / a result object), or
  - an Exception *instance* (raised when consumed, to simulate a failure), or
  - a zero-arg callable (called for its return value / to raise lazily).
If a queue is empty when consumed, a harmless default is produced so tests
that don't care about a given surface don't need to set it up.
"""

import itertools


# --- fakes for coach.py's session-event loop -------------------------------


class FakeEventContentBlock:
    def __init__(self, type: str, text: str | None = None):
        self.type = type
        self.text = text


class FakeEvent:
    def __init__(self, type: str, content=None):
        self.type = type
        self.content = content or []


def agent_message_event(text: str) -> FakeEvent:
    """An `agent.message` event with one text content block — matches what
    coach.py's loop reads: `event.type == "agent.message"`, then
    `block.text for block in event.content if block.type == "text"`."""
    return FakeEvent("agent.message", content=[FakeEventContentBlock("text", text)])


def idle_event() -> FakeEvent:
    return FakeEvent("session.status_idle")


# --- generic helpers --------------------------------------------------------


class _Result:
    """Attribute bag standing in for whatever the real SDK returns
    (agent/session/environment/memory-store objects) — just needs `.id`
    and sometimes `.version`."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _resolve(item):
    if isinstance(item, BaseException):
        raise item
    if callable(item):
        return item()
    return item


class FakeTextStream:
    """Iterable standing in for the real SDK's `.text_stream`.

    A chunk that is itself an Exception *instance* raises at that point in
    the iteration instead of being yielded as text -- this is what lets a
    test simulate a stream that fails *partway through* (some real delta
    chunks already produced before the failure), which `_resolve`'s
    whole-item check (raise immediately if the whole queued item is an
    Exception) can't express on its own: that only covers "fails before the
    first chunk". e.g. `queue_message_stream(["Hi", RuntimeError("boom")])`
    yields "Hi" then raises RuntimeError on the next iteration step, mid
    text_stream iteration, matching how `partner.py`'s
    `yield from stream.text_stream` would see a real mid-stream API error.
    """

    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __iter__(self):
        for chunk in self._chunks:
            if isinstance(chunk, BaseException):
                raise chunk
            yield chunk


class FakeMessagesStreamContext:
    def __init__(self, chunks):
        self.text_stream = FakeTextStream(chunks)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeContentBlock:
    """Stands in for the real SDK's text content block on a
    `client.messages.create(...)` response -- just needs `.type`/`.text`,
    matching how `partner.py`'s `generate_opening_line` reads it (`block.text
    for block in response.content if block.type == "text"`)."""

    def __init__(self, type: str, text: str | None = None):
        self.type = type
        self.text = text


class FakeMessage:
    """Stands in for the real SDK's non-streamed `Message` return value from
    `client.messages.create(...)` -- just needs `.content` (a list of
    text-block-like objects)."""

    def __init__(self, text: str):
        self.content = [FakeContentBlock("text", text)]


class FakeEventStreamContext:
    def __init__(self, events):
        self._events = events

    def __enter__(self):
        # `with client.beta.sessions.events.stream(session.id) as stream:`
        # then `for event in stream:` — an iterator satisfies both.
        return iter(self._events)

    def __exit__(self, exc_type, exc, tb):
        return False


# --- `client.messages.*` ----------------------------------------------------


class _FakeMessages:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake

    def stream(self, *, model, max_tokens, system, messages):
        self._fake.messages_stream_calls.append(
            {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}
        )
        if self._fake.message_stream_queue:
            item = self._fake.message_stream_queue.pop(0)
        else:
            item = ["ok"]
        chunks = _resolve(item)
        return FakeMessagesStreamContext(chunks)

    def create(self, *, model, max_tokens, system, messages):
        self._fake.messages_create_calls.append(
            {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}
        )
        if self._fake.message_create_queue:
            item = self._fake.message_create_queue.pop(0)
        else:
            item = "ok"
        text = _resolve(item)
        return FakeMessage(text)


# --- `client.beta.sessions.*` ----------------------------------------------


class _FakeSessionsEvents:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake

    def stream(self, session_id):
        self._fake.sessions_events_stream_calls.append({"session_id": session_id})
        if self._fake.session_events_queue:
            item = self._fake.session_events_queue.pop(0)
        else:
            item = [idle_event()]
        events = _resolve(item)
        return FakeEventStreamContext(events)

    def send(self, session_id, events):
        self._fake.sessions_events_send_calls.append({"session_id": session_id, "events": events})


class _FakeSessions:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake
        self.events = _FakeSessionsEvents(fake)

    def create(self, *, agent, environment_id, resources):
        self._fake.sessions_create_calls.append(
            {"agent": agent, "environment_id": environment_id, "resources": resources}
        )
        if self._fake.session_create_queue:
            item = self._fake.session_create_queue.pop(0)
            return _resolve(item)
        return _Result(id=f"session-{next(self._fake._session_counter)}")


# --- `client.beta.memory_stores.*` -----------------------------------------


class _FakeMemoryStoresMemories:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake

    def create(self, *, memory_store_id, path, content):
        self._fake.memories_create_calls.append(
            {"memory_store_id": memory_store_id, "path": path, "content": content}
        )
        return _Result(id=f"memory-{next(self._fake._memory_counter)}")


class _FakeMemoryStores:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake
        self.memories = _FakeMemoryStoresMemories(fake)

    def create(self, *, name, description):
        self._fake.memory_stores_create_calls.append({"name": name, "description": description})
        if self._fake.memory_store_create_queue:
            item = self._fake.memory_store_create_queue.pop(0)
            return _resolve(item)
        return _Result(id=f"store-{next(self._fake._store_counter)}")


# --- `client.beta.agents.*` / `client.beta.environments.*` -----------------


class _FakeAgents:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake

    def create(self, **kwargs):
        self._fake.agents_create_calls.append(kwargs)
        if self._fake.agent_create_queue:
            item = self._fake.agent_create_queue.pop(0)
            return _resolve(item)
        return _Result(id=f"agent-{next(self._fake._agent_counter)}", version=1)

    def update(self, id, **kwargs):
        self._fake.agents_update_calls.append({"id": id, **kwargs})
        if self._fake.agent_update_queue:
            item = self._fake.agent_update_queue.pop(0)
            return _resolve(item)
        return _Result(id=id, version=2)


class _FakeEnvironments:
    def __init__(self, fake: "FakeAnthropic"):
        self._fake = fake

    def create(self, *, name, config):
        self._fake.environments_create_calls.append({"name": name, "config": config})
        if self._fake.environment_create_queue:
            item = self._fake.environment_create_queue.pop(0)
            return _resolve(item)
        return _Result(id=f"env-{next(self._fake._env_counter)}")


class _FakeBeta:
    def __init__(self, fake: "FakeAnthropic"):
        self.sessions = _FakeSessions(fake)
        self.memory_stores = _FakeMemoryStores(fake)
        self.agents = _FakeAgents(fake)
        self.environments = _FakeEnvironments(fake)


class FakeAnthropic:
    """Drop-in double for `anthropic.Anthropic` covering only the methods
    this app calls. Configure per-test via the `queue_*()` methods; every
    call is logged in the matching `*_calls` list for assertions."""

    def __init__(self):
        # Response queues (pop-from-front). Empty queue -> harmless default.
        self.message_stream_queue: list = []
        self.message_create_queue: list = []
        self.session_events_queue: list = []
        self.session_create_queue: list = []
        self.memory_store_create_queue: list = []
        self.agent_create_queue: list = []
        self.agent_update_queue: list = []
        self.environment_create_queue: list = []

        # Call logs.
        self.messages_stream_calls: list[dict] = []
        self.messages_create_calls: list[dict] = []
        self.sessions_create_calls: list[dict] = []
        self.sessions_events_stream_calls: list[dict] = []
        self.sessions_events_send_calls: list[dict] = []
        self.memory_stores_create_calls: list[dict] = []
        self.memories_create_calls: list[dict] = []
        self.agents_create_calls: list[dict] = []
        self.agents_update_calls: list[dict] = []
        self.environments_create_calls: list[dict] = []

        self._session_counter = itertools.count(1)
        self._store_counter = itertools.count(1)
        self._agent_counter = itertools.count(1)
        self._env_counter = itertools.count(1)
        self._memory_counter = itertools.count(1)

        self.messages = _FakeMessages(self)
        self.beta = _FakeBeta(self)

    # -- configuration helpers --

    def queue_message_stream(self, chunks_or_exc) -> None:
        """Next `messages.stream(...)` call yields these chunks (a list of
        str) from `.text_stream`, or raises if given an Exception."""
        self.message_stream_queue.append(chunks_or_exc)

    def queue_message_create(self, text_or_exc) -> None:
        """Next `messages.create(...)` call returns a fake `Message` whose
        `.content` is a single text block with this text, or raises if given
        an Exception instance."""
        self.message_create_queue.append(text_or_exc)

    def queue_session_events(self, events_or_exc) -> None:
        """Next `sessions.events.stream(...)` call yields these events (a
        list of FakeEvent), or raises if given an Exception."""
        self.session_events_queue.append(events_or_exc)

    def queue_session_create(self, result_or_exc) -> None:
        self.session_create_queue.append(result_or_exc)

    def queue_memory_store_create(self, result_or_exc) -> None:
        self.memory_store_create_queue.append(result_or_exc)

    def queue_agent_create(self, result_or_exc) -> None:
        self.agent_create_queue.append(result_or_exc)

    def queue_agent_update(self, result_or_exc) -> None:
        self.agent_update_queue.append(result_or_exc)

    def queue_environment_create(self, result_or_exc) -> None:
        self.environment_create_queue.append(result_or_exc)
