"""Regression tests for safe DOM rendering of untrusted UI content (Issue #9)."""
from pathlib import Path


def test_dynamic_ui_content_never_uses_inner_html():
    source = Path("app/ui/index.html").read_text(encoding="utf-8")
    assert ".innerHTML =" not in source
    assert "msg.textContent = String(text ?? '')" in source
    assert "welcome.textContent =" in source
    assert "empty.textContent =" in source


def test_course_cards_use_text_nodes_and_event_listeners():
    source = Path("app/ui/index.html").read_text(encoding="utf-8")
    assert "code.textContent = course.code || ''" in source
    assert "title.textContent = course.title || ''" in source
    assert "description.textContent = course.description || ''" in source
    assert "button.addEventListener('click', () => selectCourse(course.id))" in source
    assert "card.innerHTML =" not in source


def test_evidence_cards_render_untrusted_fields_as_text():
    source = Path("app/ui/index.html").read_text(encoding="utf-8")
    assert "tDiv.textContent = card.title || ''" in source
    assert "bDiv.textContent = card.content || ''" in source


def test_chat_message_content_is_not_interpreted_as_markup():
    source = Path("app/ui/index.html").read_text(encoding="utf-8")
    append_start = source.index("function appendMsg(text, sender)")
    append_end = source.index("function renderTutorResponse(res)", append_start)
    append_block = source[append_start:append_end]
    assert "msg.textContent = String(text ?? '')" in append_block
    assert "msg.innerHTML" not in append_block
    assert "msg.style.whiteSpace = 'pre-wrap'" in append_block
