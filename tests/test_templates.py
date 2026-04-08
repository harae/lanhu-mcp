"""Tests for markdown-based tool return templates."""

from pathlib import Path

import lanhu_mcp_templates as templates


def test_load_tool_return_markdown():
    text = templates.load_tool_return_markdown("lanhu_get_ai_analyze_page_result", "stage2_developer")
    assert "元认知验证（开发视角）" in text


def test_render_tool_return_markdown_replaces_placeholder():
    text = templates.render_tool_return_markdown(
        "lanhu_get_pages",
        "ai_instruction",
        {"MODE_OPTIONS_PLACEHOLDER": "开发视角 / 测试视角"},
    )
    assert "开发视角 / 测试视角" in text
    assert "[[MODE_OPTIONS_PLACEHOLDER]]" not in text


def test_list_tool_return_templates_for_multi_template_tool():
    names = templates.list_tool_return_templates("lanhu_get_ai_analyze_page_result")
    assert "stage2_developer" in names
    assert "stage4_explorer" in names


def test_list_tool_return_templates_for_design_summary_fragments():
    names = templates.list_tool_return_templates("lanhu_get_ai_analyze_design_result")
    assert "summary_header" in names
    assert "summary_success_design" in names
    assert "summary_fallback_design" in names
    assert "summary_failures" in names


def test_user_override_has_priority_and_reset(tmp_path: Path, monkeypatch):
    db_root = tmp_path / "db"
    default_dir = db_root / "demo_tool" / "return"
    default_dir.mkdir(parents=True, exist_ok=True)
    (default_dir / "prompt.md").write_text("default content", encoding="utf-8")

    monkeypatch.setattr(templates, "_TEMPLATE_ROOT", db_root)
    templates._clear_template_cache()

    default_text = templates.load_tool_return_markdown("demo_tool", "prompt", account="alice")
    assert default_text == "default content"

    saved_path = templates.save_user_tool_return_markdown("demo_tool", "prompt", "alice", "user content")
    assert saved_path == db_root / "demo_tool" / "users" / "alice" / "return" / "prompt.md"

    user_text = templates.load_tool_return_markdown("demo_tool", "prompt", account="alice")
    assert user_text == "user content"

    detail = templates.get_tool_return_markdown_detail("demo_tool", "prompt", account="alice")
    assert detail["has_override"] is True
    assert detail["source"] == "user"

    assert templates.reset_user_tool_return_markdown("demo_tool", "prompt", "alice") is True
    reverted = templates.load_tool_return_markdown("demo_tool", "prompt", account="alice")
    assert reverted == "default content"

    detail = templates.get_tool_return_markdown_detail("demo_tool", "prompt", account="alice")
    assert detail["has_override"] is False
    assert detail["source"] == "default"
