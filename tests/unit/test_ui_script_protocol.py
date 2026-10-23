"""Bridge UI-script protocol regression tests (v4.0.1 async bridge).

These guard the JavaScript side of the async bridge protocol in
``app/ui/app.js`` by content assertions, the same technique used by
``tests/security/test_html_injection.py``. On Windows CI/PySide6 runtime we
cannot drive a real WebView2 channel in unit tests, so the protocol contract
is locked by asserting the exact handling code exists.

Two classes of live-app bug are pinned here:

1. *Promise-shaped slot returns* — QWebChannel resolves ``@Slot(result=str)``
   invocations as Promises whose resolved value is the raw JSON **string**
   returned by the Python slot. The original fix matched object acks only, so
   a promise-resolved string fell through to the offline fallback and stacked
   a fake "runtime connection required" message over the real answer
   (double render). ``processAck`` must normalize every shape first.
2. *Honest bridge errors* — while the bridge is connected, a malformed ack
   must surface the error envelope, never the standalone fallback message
   (that message may only appear when no bridge exists at all).
"""
from __future__ import annotations

from pathlib import Path

APP_JS = Path("app/ui/app.js").read_text(encoding="utf-8")


def _section(start_marker: str, end_marker: str) -> str:
    start = APP_JS.find(start_marker)
    end = APP_JS.find(end_marker, start + len(start_marker))
    assert start != -1 and end != -1, f"section markers not found: {start_marker}"
    return APP_JS[start:end]


def test_send_query_handles_promise_shaped_ack():
    """QWebChannel resolves result-bearing slots as Promises; the resolution
    value must be normalized (it is a JSON string, not an object)."""
    assert "typeof ack.then === 'function'" in APP_JS
    assert "ack.then(processAck)" in APP_JS
    blocker = _section("const normalizeAck = (raw) => {", "const genericFailure = () =>")
    assert "typeof raw === 'string'" in blocker
    assert "JSON.parse(raw)" in blocker
    # processAck must normalize through normalizeAck before branching.
    process_ack = _section("const processAck = (rawAck) => {", "let ack = null;")
    assert "const ack = normalizeAck(rawAck);" in process_ack
    # Promise rejection must surface the friendly error envelope, never the
    # offline fallback reply.
    catch_branch = APP_JS.split("ack.then(processAck)", 1)[1].split("} else {", 1)[0]
    assert "renderChatError(" in catch_branch
    assert "simulateResponse" not in catch_branch


def test_queued_ack_parks_turn_until_signal():
    """A queued acknowledgment keeps the 'thinking' state until responseReady
    delivers the completed turn — except when the signal already arrived
    (fast-turn race): then re-entering 'thinking' would stick forever."""
    start = APP_JS.find("const processAck =")
    end = APP_JS.find("let ack = null;", start)
    process_ack = APP_JS[start:end]
    assert "ack.queued === true" in process_ack
    assert "if (!turnDelivered)" in process_ack
    assert "turnPending = true;" in process_ack
    assert "setThinking(true)" in process_ack


def test_turn_delivered_guard_wired_by_signal_handler():
    """handleResponseReady must mark a delivery so processAck cannot re-park."""
    handler = _section("function handleResponseReady", "function handleCurriculumIngested")
    assert "turnDelivered = true;" in handler
    assert "turnPending = false;" in handler
    assert "setThinking(false)" in handler
    # Success renders the tutor response; failure renders the error envelope.
    assert "renderTutorResponse(res)" in handler
    assert "renderChatError(res)" in handler


def test_turn_pending_guards_duplicate_submission():
    """sendMessage must refuse a second send while a turn is in flight."""
    assert "if (!text || turnPending) return;" in APP_JS


def test_signal_delivery_wired():
    """The async result paths must be wired to the bridge signals."""
    assert "responseReady.connect(handleResponseReady)" in APP_JS
    assert "curriculumIngested.connect(handleCurriculumIngested)" in APP_JS


def test_fallback_only_reachable_without_bridge():
    """The standalone fallback message is reserved for the no-runtime case:
    while the bridge is connected, malformed acks surface renderChatError and
    processAck must NEVER schedule the fallback (double-render fix)."""
    assert "function simulateResponse(" in APP_JS  # offline fallback survives
    process_ack = _section("const processAck = (rawAck) => {", "let ack = null;")
    assert "renderChatError(" in process_ack
    assert "simulateResponse" not in process_ack
    # Synchronous section between the bridge call and the promise handling
    # must not reach the fallback either (the original sync fall-through bug).
    call_index = APP_JS.find("ack = window.bridge.sendQuery(")
    promise_index = APP_JS.find("typeof ack.then === 'function'")
    assert call_index != -1 and promise_index != -1
    sync_section = APP_JS[call_index:promise_index]
    assert "simulateResponse" not in sync_section
    # The only remaining simulateResponse(text) call site is the no-bridge else.
    no_bridge_branch = APP_JS[APP_JS.find("} else {\n    // Fallback for standalone"):]
    assert "simulateResponse(text)" in no_bridge_branch
