"""Tests for multi-account cookie resolution."""

import asyncio
import json
from pathlib import Path

from lanhu_mcp_ext import AccountCookieStore, verify_lanhu_cookie_with_api


def test_account_cookie_store_reads_account_specific_cookie(tmp_path: Path):
    file_path = tmp_path / "account_cookies.json"
    file_path.write_text(
        json.dumps(
            {
                "accounts": {
                    "alice": {
                        "cookie": "lanhu_cookie=alice_cookie",
                        "dds_cookie": "dds_cookie=alice_dds",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    store = AccountCookieStore(file_path=file_path, default_cookie="default_cookie", default_dds_cookie="default_dds")
    cookie, dds_cookie = store.get_cookies("alice")

    assert cookie == "lanhu_cookie=alice_cookie"
    assert dds_cookie == "dds_cookie=alice_dds"


def test_account_cookie_store_falls_back_to_lanhu_cookie_when_dds_cookie_missing(tmp_path: Path):
    file_path = tmp_path / "account_cookies.json"
    file_path.write_text(
        json.dumps(
            {
                "accounts": {
                    "alice": {
                        "cookie": "lanhu_cookie=alice_cookie",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    store = AccountCookieStore(file_path=file_path, default_cookie="default_cookie", default_dds_cookie="default_dds")
    cookie, dds_cookie = store.get_cookies("alice")

    assert cookie == "lanhu_cookie=alice_cookie"
    assert dds_cookie == "lanhu_cookie=alice_cookie"


def test_account_cookie_store_upsert_and_clear_dds(tmp_path: Path):
    file_path = tmp_path / "account_cookies.json"
    file_path.write_text(json.dumps({"accounts": {}}, ensure_ascii=False), encoding="utf-8")

    store = AccountCookieStore(file_path=file_path, default_cookie="default_cookie", default_dds_cookie="default_dds")
    store.upsert_account("bob", "lanhu=bob", dds_cookie="dds=bob")
    cookie, dds = store.get_cookies("bob")
    assert cookie == "lanhu=bob"
    assert dds == "dds=bob"

    store.upsert_account("bob", "lanhu=bob2", dds_cookie=None)
    cookie, dds = store.get_cookies("bob")
    assert cookie == "lanhu=bob2"
    assert dds == "lanhu=bob2"


def test_verify_lanhu_cookie_rejects_empty():
    r = asyncio.run(
        verify_lanhu_cookie_with_api(
            "",
            base_url="https://lanhuapp.com",
            timeout=30,
            default_cookie="your_lanhu_cookie_here",
        )
    )
    assert r["ok"] is False
    assert "空" in r["message"]
