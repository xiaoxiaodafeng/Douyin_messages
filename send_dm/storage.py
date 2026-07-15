import base64
import json
import os
import shutil
import tempfile
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

from .auth import DouyinAuth
from .constants import DEFAULT_ENV_CANDIDATES, DEFAULT_PROFILE


def resolve_env_file(explicit=None):
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for item in DEFAULT_ENV_CANDIDATES:
        if item.exists():
            return item
    return None


def load_cookie_from_env(env_file=None):
    env_path = resolve_env_file(env_file)
    if not env_path:
        raise RuntimeError("未找到 .env 文件")
    load_dotenv(env_path)
    cookie_str = os.getenv("DY_COOKIES")
    if not cookie_str:
        raise RuntimeError(f"{env_path} 中缺少 DY_COOKIES")
    return cookie_str, env_path


def decode_bd_ticket_data(cookie: dict) -> dict:
    raw = cookie.get("bd_ticket_guard_client_data_v2") or cookie.get("bd_ticket_guard_client_data")
    if not raw:
        return {}
    try:
        return json.loads(base64.b64decode(urllib.parse.unquote(raw)).decode("utf-8"))
    except Exception:
        return {}


async def read_security_storage(profile_dir=None):
    from playwright.async_api import async_playwright

    profile = Path(profile_dir or DEFAULT_PROFILE)
    if not profile.exists():
        raise RuntimeError(f"浏览器资料目录不存在: {profile}")

    temp_profile = Path(tempfile.mkdtemp(prefix="send-dm-profile-"))
    try:
        for item in ("Local State", "Last Version", "Default/Local Storage"):
            source = profile / item
            target = temp_profile / item
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(str(temp_profile), channel="chrome", headless=True)
            page = await ctx.new_page()
            try:
                await page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass
            await page.wait_for_timeout(1500)
            data = await page.evaluate(
                """() => ({
                    keys: localStorage.getItem('security-sdk/s_sdk_crypt_sdk'),
                    cert: localStorage.getItem('security-sdk/s_sdk_server_cert_key')
                })"""
            )
            await ctx.close()
            return data
    finally:
        shutil.rmtree(temp_profile, ignore_errors=True)


async def build_dm_auth(env_file=None, profile_dir=None):
    cookie_str, env_path = load_cookie_from_env(env_file)
    storage = await read_security_storage(profile_dir)
    if not storage.get("keys") or not storage.get("cert"):
        raise RuntimeError("没有读取到 security-sdk localStorage")

    auth = DouyinAuth()
    auth.perepare_auth(cookie_str, "", storage["keys"])
    bd = decode_bd_ticket_data(auth.cookie)
    auth.ts_sign = bd.get("ts_sign")
    auth.ticket = auth.cookie.get("__security_mc_1_s_sdk_sign_data_key_web_protect")
    auth.client_cert = json.loads(storage["cert"])["cert"]

    missing = [name for name in ("private_key", "ticket", "ts_sign", "client_cert") if not getattr(auth, name, None)]
    if missing:
        raise RuntimeError(f"鉴权字段缺失: {', '.join(missing)}")

    return auth, env_path
