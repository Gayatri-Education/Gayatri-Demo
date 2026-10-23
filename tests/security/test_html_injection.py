"""Security tests verifying that user input, RAG cards, and document content

cannot execute or inject malicious HTML/JavaScript (Issue #9 fix verification).
"""
from __future__ import annotations

import re
from pathlib import Path


def escape_html(text: str) -> str:
    """Python reference equivalent to index.html escapeHTML function."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def format_markdown_safe(text: str) -> str:
    """Python reference equivalent to index.html formatMarkdown function."""
    if not text:
        return ""
    safe = escape_html(text)
    safe = re.sub(r"^### (.*$)", r'<h4 style="margin: 8px 0 4px 0; color: #38bdf8; font-size: 14px;">\1</h4>', safe, flags=re.MULTILINE)
    safe = re.sub(r"^## (.*$)", r'<h3 style="margin: 10px 0 4px 0; color: #38bdf8; font-size: 15px;">\1</h3>', safe, flags=re.MULTILINE)
    safe = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*(.*?)\*", r"<em>\1</em>", safe)
    safe = safe.replace("\n", "<br>")
    return safe


def test_script_tags_are_escaped():
    payload = "<script>alert('xss')</script>"
    rendered = format_markdown_safe(payload)
    assert "<script>" not in rendered
    assert "</script>" not in rendered
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in rendered


def test_img_onerror_is_escaped():
    payload = '<img src=x onerror="alert(document.cookie)">'
    rendered = format_markdown_safe(payload)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
    assert "&quot;" in rendered


def test_svg_onload_is_escaped():
    payload = '<svg onload=alert("pwned")>'
    rendered = format_markdown_safe(payload)
    assert "<svg" not in rendered
    assert "&lt;svg" in rendered


def test_javascript_protocol_is_escaped():
    payload = '<a href="javascript:alert(1)">Click Here</a>'
    rendered = format_markdown_safe(payload)
    assert "<a href=" not in rendered
    assert "&lt;a href=" in rendered


def test_nested_markdown_with_xss_payload():
    payload = "**<script>alert('nested')</script>**"
    rendered = format_markdown_safe(payload)
    # Markdown bold formatting is preserved
    assert rendered.startswith("<strong>")
    assert rendered.endswith("</strong>")
    # But the inner script tag is completely escaped
    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(&#39;nested&#39;)&lt;/script&gt;" in rendered


def test_evidence_card_dom_rendering_in_ui_script():
    # JS was extracted from index.html into app.js (single-file refactor, v4.0.1)
    app_js = Path("app/ui/app.js").read_text(encoding="utf-8")
    # Ensure innerHTML is NOT used for evidence card title/content
    assert "cDiv.innerHTML = `" not in app_js
    # Ensure textContent is used for card rendering
    assert "tDiv.textContent = card.title" in app_js
    assert "bDiv.textContent = card.content" in app_js


def test_escape_html_present_in_ui_script():
    # JS was extracted from index.html into app.js (single-file refactor, v4.0.1)
    app_js = Path("app/ui/app.js").read_text(encoding="utf-8")
    assert "function escapeHTML(" in app_js
    assert "escapeHTML(text)" in app_js or "escapeHTML(str)" in app_js


def test_index_html_links_extracted_ui_assets():
    """Guards the v4.0.1 UI refactor: index.html must reference the extracted
    styles.css / app.js and no longer embed inline <style> or <script> logic."""
    index_html = Path("app/ui/index.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="styles.css">' in index_html
    assert '<script src="app.js">' in index_html
    # No inline style or application-script blocks remain in the markup
    assert "<style>" not in index_html
    assert "function escapeHTML(" not in index_html
    # The Qt WebChannel transport script may remain (library include, not app logic)
    assert '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>' in index_html
