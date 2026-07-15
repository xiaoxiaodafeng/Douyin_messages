import argparse
import ast
import asyncio
import os
import sys
import urllib.parse
import uuid
from pathlib import Path

import requests

from .auto_reply import AutoReplyService
from .client import DMClient
from .constants import DEFAULT_PROFILE, DEFAULT_SEC_UID
from .header import HeaderBuilder, HeaderType
from .llm_client import OpenAICompatibleChatClient, resolve_llm_config
from .params import Params
from .receiver import DouyinRecvMsg
from .storage import build_dm_auth, load_cookie_from_env
from .utils import generate_a_bogus, splice_url, trans_cookies


SEARCH_USER_API = "https://www.douyin.com/aweme/v1/web/discover/search/"
SEARCH_CONTEXT_ENV = "DY_SEARCH_CONTEXT"
SEARCH_CONTEXT_CANDIDATES = (
    Path.cwd() / "search_context.txt",
    Path.cwd() / "search_context.py",
    Path(__file__).resolve().parent.parent / "search_context.txt",
    Path(__file__).resolve().parent.parent / "search_context.py",
)


def resolve_cli_target_and_content(raw_args: list[str]):
    if len(raw_args) >= 2 and raw_args[0].isdigit():
        return {"douyin_id": raw_args[0], "sec_uid": None}, " ".join(raw_args[1:])
    return {"douyin_id": None, "sec_uid": None}, " ".join(raw_args)


def choose_target_identifiers(sec_uid: str | None, douyin_id: str | None, cli_target: dict[str, str | None]):
    if sec_uid:
        return sec_uid, None
    if douyin_id:
        return None, douyin_id
    if cli_target.get("douyin_id"):
        return None, cli_target["douyin_id"]
    return DEFAULT_SEC_UID, None


def resolve_search_context_file(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    env_path = os.getenv(SEARCH_CONTEXT_ENV)
    if env_path:
        path = Path(env_path)
        return path if path.exists() else None
    for path in SEARCH_CONTEXT_CANDIDATES:
        if path.exists():
            return path
    return None


def parse_search_context_text(text: str) -> dict:
    tree = ast.parse(text)
    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"headers", "params"}:
                    assignments[target.id] = ast.literal_eval(node.value)
    headers = dict(assignments.get("headers") or {})
    params = dict(assignments.get("params") or {})
    cookies = trans_cookies(headers.get("cookie", ""))
    return {
        "headers": headers,
        "params": params,
        "cookies": cookies,
    }


def load_search_context(explicit: str | None = None) -> dict | None:
    path = resolve_search_context_file(explicit)
    if not path:
        return None
    context = parse_search_context_text(path.read_text(encoding="utf-8"))
    context["path"] = str(path)
    return context


def build_default_search_user_request(auth, douyin_id: str):
    refer = f"https://www.douyin.com/search/{urllib.parse.quote(douyin_id)}?aid={uuid.uuid4()}&type=general"
    headers = HeaderBuilder.build(HeaderType.GET)
    headers.set_referer(refer)
    params = Params()
    params.add_param("device_platform", "webapp")
    params.add_param("aid", "6383")
    params.add_param("channel", "channel_pc_web")
    params.add_param("search_channel", "aweme_user_web")
    params.add_param("search_filter_value", r'{"douyin_user_fans":[""],"douyin_user_type":[""]}')
    params.add_param("keyword", douyin_id)
    params.add_param("search_source", "switch_tab")
    params.add_param("query_correct_type", "1")
    params.add_param("is_filter_search", "1")
    params.add_param("offset", "0")
    params.add_param("count", "10")
    params.add_param("need_filter_settings", "1")
    params.add_param("list_type", "single")
    params.add_param("update_version_code", "170400")
    params.add_param("pc_client_type", "1")
    params.add_param("version_code", "170400")
    params.add_param("version_name", "17.4.0")
    params.add_param("cookie_enabled", "true")
    params.add_param("screen_width", "1707")
    params.add_param("screen_height", "960")
    params.add_param("browser_language", "zh-CN")
    params.add_param("browser_platform", "Win32")
    params.add_param("browser_name", "Edge")
    params.add_param("browser_version", "125.0.0.0")
    params.add_param("browser_online", "true")
    params.add_param("engine_name", "Blink")
    params.add_param("engine_version", "125.0.0.0")
    params.add_param("os_name", "Windows")
    params.add_param("os_version", "10")
    params.add_param("cpu_core_num", "32")
    params.add_param("device_memory", "8")
    params.add_param("platform", "PC")
    params.add_param("downlink", "10")
    params.add_param("effective_type", "4g")
    params.add_param("round_trip_time", "150")
    params.with_web_id(auth, refer)
    params.add_param("verifyFp", auth.cookie["s_v_web_id"])
    params.add_param("fp", auth.cookie["s_v_web_id"])
    params.add_param("msToken", auth.msToken)
    params.with_a_bogus()
    return headers, params, dict(auth.cookie)


def build_search_user_request(auth, douyin_id: str, search_context: dict | None = None):
    if not search_context:
        return build_default_search_user_request(auth, douyin_id)

    context_headers = dict(search_context.get("headers") or {})
    context_params = dict(search_context.get("params") or {})
    cookies = dict(search_context.get("cookies") or {})

    headers = HeaderBuilder.build(HeaderType.GET)
    for key, value in context_headers.items():
        if key.lower() == "cookie":
            continue
        headers.set_header(key, value)

    original_keyword = str(context_params.get("keyword") or "")
    refer = context_headers.get("referer") or f"https://www.douyin.com/search/{urllib.parse.quote(douyin_id)}?type=user"
    if original_keyword and original_keyword != douyin_id:
        refer = refer.replace(urllib.parse.quote(original_keyword), urllib.parse.quote(douyin_id))
    headers.set_referer(refer)

    params = Params()
    params.update_params(context_params)
    params.add_param("keyword", douyin_id)
    params.add_param("verifyFp", cookies.get("s_v_web_id", context_params.get("verifyFp", "")))
    params.add_param("fp", cookies.get("s_v_web_id", context_params.get("fp", "")))
    if not context_params.get("a_bogus"):
        params.get().pop("a_bogus", None)
        params.add_param("a_bogus", generate_a_bogus(splice_url(params.get()), ua=headers.get().get("user-agent")))
    return headers, params, cookies


def search_user_by_douyin_id(auth, douyin_id: str) -> dict:
    if not douyin_id.isdigit():
        raise RuntimeError("抖音号格式错误，仅支持纯数字 short_id")

    search_context = load_search_context()
    headers, params, cookies = build_search_user_request(auth, douyin_id, search_context=search_context)
    response = requests.get(
        SEARCH_USER_API,
        headers=headers.get(),
        cookies=cookies,
        params=params.get(),
        timeout=20,
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def iter_mappings(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_mappings(child)


def first_nested_value(item, *keys):
    for mapping in iter_mappings(item):
        for key in keys:
            value = mapping.get(key)
            if value not in (None, "", []):
                return value
    return None


def normalize_search_user_item(item: dict):
    return {
        "uid": first_nested_value(item, "uid", "user_id", "id"),
        "sec_uid": first_nested_value(item, "sec_uid", "secUid", "sec_user_id"),
        "short_id": first_nested_value(item, "short_id"),
        "unique_id": first_nested_value(item, "unique_id"),
        "nickname": first_nested_value(item, "nickname", "nick_name", "name"),
        "raw": item,
    }


def select_search_user(douyin_id: str, user_list: list[dict]):
    candidates = [normalize_search_user_item(item) for item in user_list]
    for candidate in candidates:
        if douyin_id in {str(candidate.get("short_id") or ""), str(candidate.get("unique_id") or "")}:
            return candidate, candidates
    return (candidates[0] if candidates else None), candidates


def resolve_user_by_douyin_id(auth, douyin_id: str):
    res = search_user_by_douyin_id(auth, douyin_id)
    user_list = res.get("user_list") or []
    target, _ = select_search_user(douyin_id, user_list)
    if not target:
        nil_type = (res.get("search_nil_info") or {}).get("search_nil_type")
        if nil_type:
            raise RuntimeError(f"discover/search 未返回用户结果: {nil_type}")
        raise RuntimeError("discover/search 未返回用户结果")
    if target.get("sec_uid") and not target.get("uid"):
        resolved = DMClient.resolve_user(auth, target["sec_uid"])
        target = {**target, **{k: v for k, v in resolved.items() if v not in (None, "", [])}}
    if not target.get("uid"):
        raise RuntimeError("discover/search 未解析到目标 uid")
    return target


def resolve_target_user(auth, sec_uid: str | None, douyin_id: str | None, resolver=None):
    resolver = resolver or resolve_user_by_douyin_id
    if sec_uid:
        target = DMClient.resolve_user(auth, sec_uid)
    elif douyin_id:
        target = resolver(auth, douyin_id)
    else:
        target = DMClient.resolve_user(auth, DEFAULT_SEC_UID)
    if not target.get("uid"):
        raise RuntimeError("没有解析到目标 uid")
    return target


async def handle_send(content: str, sec_uid: str | None, douyin_id: str | None, profile: str, env_file: str | None):
    auth, env_path = await build_dm_auth(env_file, profile)
    target = resolve_target_user(auth, sec_uid, douyin_id)
    cid, csid, ticket = DMClient.create_conversation(auth, int(target["uid"]))
    result = DMClient.send_msg(auth, cid, csid, ticket, content)
    print("env:", env_path)
    print("target:", {k: target.get(k) for k in ("uid", "sec_uid", "short_id", "unique_id", "nickname")})
    print("conversation_id:", cid)
    print("conversation_short_id:", csid)
    print("result:", result)


def handle_recv(profile: str, env_file: str | None):
    cookie_str, env_path = load_cookie_from_env(env_file)

    async def prepare():
        auth, _ = await build_dm_auth(env_file, profile)
        print("env:", env_path)
        print("cookie_loaded:", bool(cookie_str))
        return auth

    auth = asyncio.run(prepare())
    DouyinRecvMsg(auth).start()


def handle_autoreply(
    profile: str,
    env_file: str | None,
    api_key: str | None,
    base_url: str | None,
    workspace_id: str | None,
    model: str | None,
    system_prompt: str | None,
    max_context_messages: int,
):
    cookie_str, env_path = load_cookie_from_env(env_file)

    async def prepare():
        auth, _ = await build_dm_auth(env_file, profile)
        llm_config = resolve_llm_config(
            api_key=api_key,
            base_url=base_url,
            workspace_id=workspace_id,
            model=model,
            system_prompt=system_prompt,
        )
        print("env:", env_path)
        print("cookie_loaded:", bool(cookie_str))
        print("model:", llm_config.model)
        print("base_url:", llm_config.base_url)
        service = AutoReplyService(
            auth,
            OpenAICompatibleChatClient(llm_config),
            llm_config.system_prompt,
            max_context_messages=max_context_messages,
        )
        return auth, service

    auth, service = asyncio.run(prepare())
    DouyinRecvMsg(auth, message_handler=service.handle_event).start()


def build_send_parser():
    parser = argparse.ArgumentParser(description="send_dm send")
    parser.add_argument("content")
    parser.add_argument("--sec-uid", default=None)
    parser.add_argument("--douyin-id", default=None)
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--env", default=None)
    return parser


def build_recv_parser():
    parser = argparse.ArgumentParser(description="send_dm recv")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--env", default=None)
    return parser


def build_autoreply_parser():
    parser = argparse.ArgumentParser(description="send_dm autoreply")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--env", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--workspace-id", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--max-context-messages", type=int, default=12)
    return parser


def build_shorthand_parser():
    parser = argparse.ArgumentParser(description="send_dm")
    parser.add_argument("args", nargs="+")
    parser.add_argument("--sec-uid", default=None)
    parser.add_argument("--douyin-id", default=None)
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--env", default=None)
    return parser


def main():
    argv = sys.argv[1:]
    if not argv:
        print(
            "用法:\n"
            '  python -m send_dm send "测试私信收发功能"\n'
            "  python -m send_dm recv\n"
            "  python -m send_dm autoreply\n"
            '  python -m send_dm "测试私信收发功能"\n'
            '  python -m send_dm "测试私信收发功能" --douyin-id 379250456\n'
            '  python -m send_dm 379250456 "测试私信收发功能"'
        )
        return

    if argv[0] == "send":
        args = build_send_parser().parse_args(argv[1:])
        sec_uid, douyin_id = choose_target_identifiers(args.sec_uid, args.douyin_id, {"douyin_id": None, "sec_uid": None})
        asyncio.run(handle_send(args.content, sec_uid, douyin_id, args.profile, args.env))
        return

    if argv[0] == "recv":
        args = build_recv_parser().parse_args(argv[1:])
        handle_recv(args.profile, args.env)
        return

    if argv[0] == "autoreply":
        args = build_autoreply_parser().parse_args(argv[1:])
        handle_autoreply(
            profile=args.profile,
            env_file=args.env,
            api_key=args.api_key,
            base_url=args.base_url,
            workspace_id=args.workspace_id,
            model=args.model,
            system_prompt=args.system_prompt,
            max_context_messages=args.max_context_messages,
        )
        return

    args = build_shorthand_parser().parse_args(argv)
    cli_target, content = resolve_cli_target_and_content(args.args)
    sec_uid, douyin_id = choose_target_identifiers(args.sec_uid, args.douyin_id, cli_target)
    asyncio.run(handle_send(content, sec_uid, douyin_id, args.profile, args.env))


if __name__ == "__main__":
    main()
