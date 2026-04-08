"""Independent web/admin extensions for lanhu_mcp_server."""

from __future__ import annotations

import functools
import json
import os
import threading
from pathlib import Path
from typing import Callable

import httpx
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from lanhu_mcp_templates import (
    get_tool_return_markdown_detail,
    list_tool_return_templates,
    list_tools_with_return_templates,
    reset_user_tool_return_markdown,
    save_user_tool_return_markdown,
)


class AccountCookieStore:
    """账号 Cookie 存储，支持按账号读取蓝湖 Cookie。"""

    def __init__(self, file_path: Path, default_cookie: str, default_dds_cookie: str):
        self.file_path = file_path
        self.default_cookie = default_cookie
        self.default_dds_cookie = default_dds_cookie
        self._lock = threading.Lock()

    def _load(self) -> dict:
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return {"accounts": {}}

    def _save(self, data: dict) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.file_path.with_suffix(".json.tmp")
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.file_path)

    def get_account_config(self, account: str | None) -> dict:
        if not account:
            return {}

        with self._lock:
            data = self._load()
        accounts = data.get("accounts", {})
        config = accounts.get(account, {})
        return config if isinstance(config, dict) else {}

    def get_cookies(self, account: str | None) -> tuple[str, str]:
        config = self.get_account_config(account)
        account_cookie = config.get("cookie") or config.get("lanhu_cookie")
        account_dds_cookie = config.get("dds_cookie")

        lanhu_cookie = account_cookie or self.default_cookie
        dds_cookie = account_dds_cookie or account_cookie or self.default_dds_cookie
        return lanhu_cookie, dds_cookie

    def upsert_account(
        self,
        username: str,
        cookie: str,
        dds_cookie: str | None = None,
    ) -> None:
        name = (username or "").strip()
        ck = (cookie or "").strip()
        if not name:
            raise ValueError("账号名不能为空")
        if not ck:
            raise ValueError("Cookie 不能为空")

        dds = (dds_cookie or "").strip()
        with self._lock:
            data = self._load()
            accounts = data.setdefault("accounts", {})
            entry: dict = {"cookie": ck}
            if dds:
                entry["dds_cookie"] = dds
            accounts[name] = entry
            self._save(data)


def ensure_account_cookie_file(file_path: Path) -> None:
    if file_path.exists():
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps({"accounts": {}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _validate_account_key(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise ValueError("账号名不能为空")
    if any(c in n for c in ("/", "\\", "\x00")):
        raise ValueError("账号名包含非法字符")
    return n


def _lanhu_browser_headers(cookie: str) -> dict[str, str]:
    return {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://lanhuapp.com/",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        ),
        "Cookie": cookie,
    }


async def _lanhu_get_json(client: httpx.AsyncClient, url: str) -> httpx.Response:
    response = await client.get(url)
    if response.status_code == 405:
        return await client.post(url, json={})
    if response.status_code == 200:
        try:
            probe = response.json()
        except json.JSONDecodeError:
            return response
        if isinstance(probe, dict) and "code" not in probe:
            msg = str(probe.get("message", ""))
            if "method" in msg.lower() and "not allowed" in msg.lower():
                return await client.post(url, json={})
    return response


async def verify_lanhu_cookie_with_api(
    cookie: str,
    *,
    base_url: str,
    timeout: float,
    default_cookie: str,
) -> dict:
    ck = (cookie or "").strip()
    if not ck or ck == default_cookie:
        return {"ok": False, "message": "Cookie 为空或为占位符", "code": None}

    headers = _lanhu_browser_headers(ck)
    url_global = f"{base_url}/api/epm/global_conf"
    url_perm = f"{base_url}/api/admin/permission/info"
    timeout = min(timeout, 20.0)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            trust_env=True,
        ) as client:
            response = await _lanhu_get_json(client, url_global)
            text_g = response.text or ""
            if response.status_code != 200:
                return {
                    "ok": False,
                    "message": f"蓝湖 global_conf 返回 HTTP {response.status_code}",
                    "code": None,
                    "detail": (text_g[:400] + ("…" if len(text_g) > 400 else "")) if text_g else "",
                }
            try:
                global_data = response.json()
            except json.JSONDecodeError:
                return {
                    "ok": False,
                    "message": "global_conf 返回非 JSON",
                    "code": None,
                    "detail": (text_g[:300] + ("…" if len(text_g) > 300 else "")) if text_g else "",
                }
            gc = global_data.get("code")
            if gc not in ("00000", 0, "0"):
                return {
                    "ok": False,
                    "message": global_data.get("msg") or "global_conf 业务失败",
                    "code": gc,
                }
            response = await _lanhu_get_json(client, url_perm)
    except httpx.ConnectError as e:
        return {
            "ok": False,
            "message": "无法连接蓝湖（DNS/网络/防火墙）。请在运行本服务的机器上确认能打开 https://lanhuapp.com",
            "code": None,
            "detail": str(e),
        }
    except httpx.TimeoutException:
        return {
            "ok": False,
            "message": "连接蓝湖超时。可尝试增大环境变量 HTTP_TIMEOUT，或检查网络/代理",
            "code": None,
        }
    except httpx.RequestError as e:
        return {
            "ok": False,
            "message": "请求蓝湖时发生网络错误",
            "code": None,
            "detail": str(e),
        }

    text = response.text or ""
    if response.status_code != 200:
        return {
            "ok": False,
            "message": f"permission/info 返回 HTTP {response.status_code}",
            "code": None,
            "detail": (text[:400] + ("…" if len(text) > 400 else "")) if text else "",
        }
    try:
        data = response.json()
    except json.JSONDecodeError:
        return {
            "ok": False,
            "message": "permission/info 返回非 JSON（可能被代理/WAF 拦截）",
            "code": None,
            "detail": (text[:300] + ("…" if len(text) > 300 else "")) if text else "",
        }

    code = data.get("code")
    msg = data.get("msg") or ""
    if code == "00005" or code == 5:
        return {"ok": False, "message": msg or "未登录或 Cookie 无效", "code": code}
    if code == "00000" or code == 0 or code == "0":
        return {"ok": True, "message": "Cookie 可用（global_conf 与 permission/info 均正常）", "code": code}
    if "login" in str(msg).lower() or "登录" in str(msg):
        return {"ok": False, "message": msg, "code": code}
    return {
        "ok": True,
        "message": msg or f"接口返回 code={code}，未识别为未登录，通常表示 Cookie 有效",
        "code": code,
    }


TOOL_DEBUG_CATALOG = [
    {
        "name": "lanhu_resolve_invite_link",
        "group": "文档入口",
        "summary": "把蓝湖邀请链接解析为可直接使用的项目 URL。",
        "input_hint": "输入 invite_url。",
        "output_hint": "输出解析后的 resolved_url 与项目参数。",
        "example_args": {"invite_url": "https://lanhuapp.com/link/#/invite?sid=example"},
    },
    {
        "name": "lanhu_get_pages",
        "group": "需求文档",
        "summary": "读取 PRD / Axure 原型的页面列表。",
        "input_hint": "输入带 docId 的原型 URL。",
        "output_hint": "输出页面列表、文档信息、推荐分析模式。",
        "example_args": {"url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id"},
    },
    {
        "name": "lanhu_get_ai_analyze_page_result",
        "group": "需求文档",
        "summary": "对指定原型页面做文本或全量分析。",
        "input_hint": "输入 url、page_names；可选 mode 和 analysis_mode。",
        "output_hint": "输出页面文本、截图路径、结构化分析内容。",
        "example_args": {
            "url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id",
            "page_names": "all",
            "mode": "text_only",
            "analysis_mode": "developer",
        },
    },
    {
        "name": "lanhu_get_designs",
        "group": "设计稿",
        "summary": "读取设计项目中的设计稿列表。",
        "input_hint": "输入不带 docId 的设计项目 URL。",
        "output_hint": "输出设计稿列表、画板尺寸、设计数量。",
        "example_args": {"url": "https://lanhuapp.com/web/#/item/project/stage?tid=team_id&pid=project_id"},
    },
    {
        "name": "lanhu_get_ai_analyze_design_result",
        "group": "设计稿",
        "summary": "分析设计稿并返回图片、HTML/CSS 参考。",
        "input_hint": "输入设计项目 url 和 design_names。",
        "output_hint": "输出截图、设计标注、HTML/CSS 结构参考。",
        "example_args": {"url": "https://lanhuapp.com/web/#/item/project/stage?tid=team_id&pid=project_id", "design_names": "all"},
    },
    {
        "name": "lanhu_get_design_slices",
        "group": "设计稿",
        "summary": "提取设计稿里的切图与素材下载信息。",
        "input_hint": "输入设计项目 url 和单个 design_name。",
        "output_hint": "输出切图列表、下载地址、图层元数据。",
        "example_args": {
            "url": "https://lanhuapp.com/web/#/item/project/stage?tid=team_id&pid=project_id",
            "design_name": "首页设计",
            "include_metadata": True,
        },
    },
    {
        "name": "lanhu_say",
        "group": "协作留言",
        "summary": "在项目下发布留言、问题或知识沉淀。",
        "input_hint": "输入 url、summary、content；可选 mentions、message_type。",
        "output_hint": "输出保存后的消息 ID 与文档元数据。",
        "example_args": {
            "url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id",
            "summary": "退款规则确认",
            "content": "测试环境退款链路已跑通，待确认超时取消规则。",
            "message_type": "knowledge",
        },
    },
    {
        "name": "lanhu_say_list",
        "group": "协作留言",
        "summary": "按项目或全局查看留言列表。",
        "input_hint": "可输入 url 或 all；可选 filter_type、search_regex、limit。",
        "output_hint": "输出消息分组、@我统计、筛选结果。",
        "example_args": {"url": "all", "filter_type": "knowledge", "limit": 10},
    },
    {
        "name": "lanhu_say_detail",
        "group": "协作留言",
        "summary": "按消息 ID 查看完整内容。",
        "input_hint": "输入 message_ids，以及 url 或 project_id。",
        "output_hint": "输出消息详情正文。",
        "example_args": {"message_ids": [1], "project_id": "project_id"},
    },
    {
        "name": "lanhu_say_edit",
        "group": "协作留言",
        "summary": "编辑已有留言。",
        "input_hint": "输入 url、message_id 和要更新的字段。",
        "output_hint": "输出更新后的消息内容。",
        "example_args": {
            "url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id",
            "message_id": 1,
            "summary": "退款规则确认（已更新）",
        },
    },
    {
        "name": "lanhu_say_delete",
        "group": "协作留言",
        "summary": "删除指定留言。",
        "input_hint": "输入 url 和 message_id。",
        "output_hint": "输出删除结果。",
        "example_args": {
            "url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id",
            "message_id": 1,
        },
    },
    {
        "name": "lanhu_get_members",
        "group": "协作留言",
        "summary": "查看访问过该项目的协作者列表。",
        "input_hint": "输入项目 URL。",
        "output_hint": "输出成员名、角色、首次和最近访问时间。",
        "example_args": {"url": "https://lanhuapp.com/web/#/item/project/product?tid=team_id&pid=project_id&docId=document_id"},
    },
]


def _serialize_debug_result(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _serialize_debug_result(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_debug_result(v) for v in value]
    image_path = getattr(value, "path", None)
    if image_path is not None:
        return {"__type": value.__class__.__name__, "path": str(image_path)}
    return {"__type": value.__class__.__name__, "repr": repr(value)}


def register_extension_routes(
    *,
    mcp,
    project_root: Path,
    account_cookie_file: Path,
    base_url: str,
    http_timeout: float,
    default_cookie: str,
    default_dds_cookie: str,
    tool_resolver: Callable[[str], object],
) -> None:
    account_config_html_file = project_root / "static" / "account-config.html"
    tool_return_editor_html_file = project_root / "static" / "tool-return-editor.html"
    tool_debug_names = {item["name"] for item in TOOL_DEBUG_CATALOG}

    @functools.lru_cache(maxsize=1)
    def read_account_config_html() -> str:
        return account_config_html_file.read_text(encoding="utf-8")

    @functools.lru_cache(maxsize=1)
    def read_tool_return_editor_html() -> str:
        return tool_return_editor_html_file.read_text(encoding="utf-8")

    def account_store() -> AccountCookieStore:
        return AccountCookieStore(
            file_path=account_cookie_file,
            default_cookie=default_cookie,
            default_dds_cookie=default_dds_cookie,
        )

    def require_authorized_account(account: str) -> None:
        validated = _validate_account_key(account)
        cfg = account_store().get_account_config(validated)
        cookie = (cfg.get("cookie") or cfg.get("lanhu_cookie") or "").strip()
        if not cookie:
            raise PermissionError(f"账号「{validated}」未配置可用 Cookie")

    def tool_return_catalog() -> list[dict]:
        tools = list_tools_with_return_templates()
        return [
            {
                "tool_name": tool_name,
                "templates": templates,
                "template_count": len(templates),
            }
            for tool_name, templates in sorted(tools.items())
        ]

    @mcp.custom_route("/account-config", methods=["GET"])
    async def _account_config_page(_request: Request) -> HTMLResponse:
        try:
            html = read_account_config_html()
        except FileNotFoundError:
            return HTMLResponse(f"<pre>缺少配置页文件：{account_config_html_file}</pre>", status_code=500)
        except OSError as e:
            return HTMLResponse(f"<pre>读取配置页失败：{e}</pre>", status_code=500)
        return HTMLResponse(html)

    @mcp.custom_route("/tool-return-editor", methods=["GET"])
    async def _tool_return_editor_page(request: Request) -> HTMLResponse:
        account = request.query_params.get("account", "")
        tool_name = request.query_params.get("tool", "")
        try:
            require_authorized_account(account)
            if not tool_name:
                raise ValueError("缺少 tool 参数")
            templates = list_tool_return_templates(tool_name)
            if not templates:
                raise FileNotFoundError(f"工具「{tool_name}」没有可编辑的 return markdown")
            html = read_tool_return_editor_html()
        except ValueError as e:
            return HTMLResponse(f"<pre>{e}</pre>", status_code=400)
        except PermissionError as e:
            return HTMLResponse(f"<pre>{e}</pre>", status_code=403)
        except FileNotFoundError as e:
            return HTMLResponse(f"<pre>{e}</pre>", status_code=404)
        except OSError as e:
            return HTMLResponse(f"<pre>读取编辑页失败：{e}</pre>", status_code=500)
        return HTMLResponse(html)

    @mcp.custom_route("/api/account-cookie", methods=["GET"])
    async def _account_config_get(request: Request) -> JSONResponse:
        try:
            account = _validate_account_key(request.query_params.get("account") or "")
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        cfg = account_store().get_account_config(account)
        cookie = cfg.get("cookie") or cfg.get("lanhu_cookie") or ""
        dds = cfg.get("dds_cookie") or ""
        if not cookie and not dds:
            return JSONResponse({"detail": f"账号「{account}」暂无保存的 Cookie"}, status_code=404)
        return JSONResponse({"username": account, "cookie": cookie, "dds_cookie": dds or None})

    @mcp.custom_route("/api/account-cookie", methods=["POST"])
    async def _account_config_post(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"detail": "请求体须为 JSON"}, status_code=400)
        try:
            username = _validate_account_key(str(body.get("username", "")))
            cookie = str(body.get("cookie", "")).strip()
            dds_raw = body.get("dds_cookie")
            dds = str(dds_raw).strip() if dds_raw is not None else ""
            if not cookie:
                return JSONResponse({"detail": "Cookie 不能为空"}, status_code=400)
            account_store().upsert_account(username, cookie, dds_cookie=dds or None)
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        except Exception as e:
            return JSONResponse({"detail": str(e)}, status_code=500)
        return JSONResponse({"ok": True, "message": f"已保存账号「{username}」"})

    @mcp.custom_route("/api/account-cookie/test", methods=["POST"])
    async def _account_config_test(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"detail": "请求体须为 JSON"}, status_code=400)
        cookie = str(body.get("cookie", ""))
        result = await verify_lanhu_cookie_with_api(
            cookie,
            base_url=base_url,
            timeout=http_timeout,
            default_cookie=default_cookie,
        )
        return JSONResponse(result)

    @mcp.custom_route("/api/tool-return/list", methods=["GET"])
    async def _tool_return_list(request: Request) -> JSONResponse:
        try:
            account = _validate_account_key(request.query_params.get("account") or "")
            require_authorized_account(account)
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        except PermissionError as e:
            return JSONResponse({"detail": str(e)}, status_code=403)
        return JSONResponse({"ok": True, "account": account, "tools": tool_return_catalog()})

    @mcp.custom_route("/api/tool-return/template", methods=["GET"])
    async def _tool_return_template_get(request: Request) -> JSONResponse:
        try:
            account = _validate_account_key(request.query_params.get("account") or "")
            tool_name = str(request.query_params.get("tool") or "").strip()
            template_name = str(request.query_params.get("template") or "").strip()
            require_authorized_account(account)
            detail = get_tool_return_markdown_detail(tool_name, template_name, account=account)
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        except PermissionError as e:
            return JSONResponse({"detail": str(e)}, status_code=403)
        except FileNotFoundError as e:
            return JSONResponse({"detail": str(e)}, status_code=404)
        return JSONResponse({"ok": True, "account": account, **detail})

    @mcp.custom_route("/api/tool-return/template", methods=["POST"])
    async def _tool_return_template_post(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"detail": "请求体须为 JSON"}, status_code=400)
        try:
            account = _validate_account_key(str(body.get("account", "")))
            tool_name = str(body.get("tool", "")).strip()
            template_name = str(body.get("template", "")).strip()
            content = str(body.get("content", ""))
            require_authorized_account(account)
            path = save_user_tool_return_markdown(tool_name, template_name, account, content)
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        except PermissionError as e:
            return JSONResponse({"detail": str(e)}, status_code=403)
        except FileNotFoundError as e:
            return JSONResponse({"detail": str(e)}, status_code=404)
        return JSONResponse(
            {
                "ok": True,
                "message": "已保存用户覆盖模板",
                "account": account,
                "tool_name": tool_name,
                "template_name": template_name,
                "path": str(path),
            }
        )

    @mcp.custom_route("/api/tool-return/template/reset", methods=["POST"])
    async def _tool_return_template_reset(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"detail": "请求体须为 JSON"}, status_code=400)
        try:
            account = _validate_account_key(str(body.get("account", "")))
            tool_name = str(body.get("tool", "")).strip()
            template_name = str(body.get("template", "")).strip()
            require_authorized_account(account)
            deleted = reset_user_tool_return_markdown(tool_name, template_name, account)
        except ValueError as e:
            return JSONResponse({"detail": str(e)}, status_code=400)
        except PermissionError as e:
            return JSONResponse({"detail": str(e)}, status_code=403)
        return JSONResponse(
            {
                "ok": True,
                "message": "已恢复默认模板" if deleted else "当前没有用户覆盖模板，仍使用默认模板",
                "account": account,
                "tool_name": tool_name,
                "template_name": template_name,
                "deleted": deleted,
            }
        )

    @mcp.custom_route("/api/tool-debug/list", methods=["GET"])
    async def _tool_debug_list(_request: Request) -> JSONResponse:
        return JSONResponse({"ok": True, "tools": TOOL_DEBUG_CATALOG})

    @mcp.custom_route("/api/tool-debug/call", methods=["POST"])
    async def _tool_debug_call(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"detail": "请求体须为 JSON"}, status_code=400)

        tool_name = str(body.get("tool_name", "")).strip()
        args = body.get("args", {})
        if not tool_name:
            return JSONResponse({"detail": "tool_name 不能为空"}, status_code=400)
        if not isinstance(args, dict):
            return JSONResponse({"detail": "args 必须是 JSON 对象"}, status_code=400)
        if tool_name not in tool_debug_names:
            return JSONResponse({"detail": f"未知工具：{tool_name}"}, status_code=404)

        tool_func = tool_resolver(tool_name)
        if tool_func is None:
            return JSONResponse({"detail": f"工具尚未注册：{tool_name}"}, status_code=500)

        try:
            result = await tool_func(ctx=object(), **args)
        except TypeError as e:
            return JSONResponse({"detail": f"参数错误：{e}"}, status_code=400)
        except Exception as e:
            return JSONResponse({"ok": False, "tool_name": tool_name, "error": str(e)}, status_code=500)

        return JSONResponse(
            {
                "ok": True,
                "tool_name": tool_name,
                "args": args,
                "result": _serialize_debug_result(result),
            }
        )


def build_http_middleware_from_env() -> list[Middleware]:
    http_middleware: list[Middleware] = []
    if os.getenv("LANHU_CONFIG_CORS", "1").strip().lower() in ("0", "false", "no", "off"):
        return http_middleware

    origins = os.getenv("LANHU_CONFIG_CORS_ORIGINS", "*").strip()
    allow = [item.strip() for item in origins.split(",") if item.strip()]
    if not allow:
        allow = ["*"]
    http_middleware.append(
        Middleware(
            CORSMiddleware,
            allow_origins=allow,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    )
    return http_middleware
