"""Markdown template loading and per-account overrides for tool return prompts."""

from __future__ import annotations

import functools
import re
from pathlib import Path


_TEMPLATE_ROOT = Path(__file__).resolve().parent / "db"
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validate_segment(value: str, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} 不能为空")
    if not _SAFE_NAME_RE.match(text):
        raise ValueError(f"{label} 包含非法字符")
    return text


def _default_tool_return_dir(tool_name: str) -> Path:
    tool = _validate_segment(tool_name, "tool_name")
    return _TEMPLATE_ROOT / tool / "return"


def _default_template_path(tool_name: str, template_name: str) -> Path:
    template = _validate_segment(template_name, "template_name")
    return _default_tool_return_dir(tool_name) / f"{template}.md"


def _user_template_path(tool_name: str, account: str, template_name: str) -> Path:
    tool = _validate_segment(tool_name, "tool_name")
    user = _validate_segment(account, "account")
    template = _validate_segment(template_name, "template_name")
    return _TEMPLATE_ROOT / tool / "users" / user / "return" / f"{template}.md"


@functools.lru_cache(maxsize=None)
def _read_markdown(path_str: str) -> str:
    return Path(path_str).read_text(encoding="utf-8").strip()


def _clear_template_cache() -> None:
    _read_markdown.cache_clear()


def list_tool_return_templates(tool_name: str) -> list[str]:
    base_dir = _default_tool_return_dir(tool_name)
    if not base_dir.exists():
        return []
    return sorted(path.stem for path in base_dir.glob("*.md") if path.is_file())


def list_tools_with_return_templates() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not _TEMPLATE_ROOT.exists():
        return result

    for tool_dir in sorted(path for path in _TEMPLATE_ROOT.iterdir() if path.is_dir()):
        templates = list_tool_return_templates(tool_dir.name)
        if templates:
            result[tool_dir.name] = templates
    return result


def load_tool_return_markdown(
    tool_name: str,
    template_name: str = "prompt",
    *,
    account: str | None = None,
) -> str:
    if account:
        user_path = _user_template_path(tool_name, account, template_name)
        if user_path.exists():
            return _read_markdown(str(user_path))

    default_path = _default_template_path(tool_name, template_name)
    return _read_markdown(str(default_path))


def get_tool_return_markdown_detail(
    tool_name: str,
    template_name: str = "prompt",
    *,
    account: str | None = None,
) -> dict:
    default_path = _default_template_path(tool_name, template_name)
    if not default_path.exists():
        raise FileNotFoundError(f"未找到默认模板：{tool_name}/{template_name}")

    default_content = _read_markdown(str(default_path))
    has_override = False
    source = "default"
    effective_content = default_content

    if account:
        user_path = _user_template_path(tool_name, account, template_name)
        if user_path.exists():
            has_override = True
            source = "user"
            effective_content = _read_markdown(str(user_path))

    return {
        "tool_name": tool_name,
        "template_name": template_name,
        "default_content": default_content,
        "effective_content": effective_content,
        "has_override": has_override,
        "source": source,
    }


def save_user_tool_return_markdown(
    tool_name: str,
    template_name: str,
    account: str,
    content: str,
) -> Path:
    # Ensure the default template exists before allowing an override.
    _ = _default_template_path(tool_name, template_name).read_text(encoding="utf-8")
    target = _user_template_path(tool_name, account, template_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((content or "").strip() + "\n", encoding="utf-8")
    _clear_template_cache()
    return target


def reset_user_tool_return_markdown(tool_name: str, template_name: str, account: str) -> bool:
    target = _user_template_path(tool_name, account, template_name)
    if not target.exists():
        return False

    target.unlink()
    parent = target.parent
    while parent != _TEMPLATE_ROOT:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent
    _clear_template_cache()
    return True


def render_tool_return_markdown(
    tool_name: str,
    template_name: str = "prompt",
    replacements: dict[str, str] | None = None,
    *,
    account: str | None = None,
) -> str:
    text = load_tool_return_markdown(tool_name, template_name, account=account)
    for key, value in (replacements or {}).items():
        text = text.replace(f"[[{key}]]", str(value))
    return text
