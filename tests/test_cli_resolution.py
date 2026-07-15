import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from send_dm import __main__ as main_mod
from send_dm.constants import DEFAULT_SEC_UID


class TestCliResolution(unittest.TestCase):
    def test_shorthand_numeric_first_arg_is_douyin_id(self):
        target, content = main_mod.resolve_cli_target_and_content([
            "379250456",
            "测试私信收发功能",
        ])
        self.assertEqual(target, {"douyin_id": "379250456", "sec_uid": None})
        self.assertEqual(content, "测试私信收发功能")

    def test_shorthand_plain_content_keeps_default_target(self):
        target, content = main_mod.resolve_cli_target_and_content([
            "测试私信收发功能",
        ])
        self.assertEqual(target, {"douyin_id": None, "sec_uid": None})
        self.assertEqual(content, "测试私信收发功能")

    def test_send_parser_accepts_douyin_id(self):
        parser = main_mod.build_send_parser()
        args = parser.parse_args(["测试", "--douyin-id", "379250456"])
        self.assertEqual(args.content, "测试")
        self.assertEqual(args.douyin_id, "379250456")


class TestTargetSelection(unittest.TestCase):
    def test_sec_uid_has_priority_over_douyin_id(self):
        sec_uid, douyin_id = main_mod.choose_target_identifiers(
            sec_uid="MS4w-test",
            douyin_id="379250456",
            cli_target={"douyin_id": "111111", "sec_uid": None},
        )
        self.assertEqual(sec_uid, "MS4w-test")
        self.assertIsNone(douyin_id)

    def test_explicit_douyin_id_has_priority_over_shorthand_numeric(self):
        sec_uid, douyin_id = main_mod.choose_target_identifiers(
            sec_uid=None,
            douyin_id="888888",
            cli_target={"douyin_id": "379250456", "sec_uid": None},
        )
        self.assertIsNone(sec_uid)
        self.assertEqual(douyin_id, "888888")

    def test_default_sec_uid_is_used_when_no_target_is_provided(self):
        sec_uid, douyin_id = main_mod.choose_target_identifiers(
            sec_uid=None,
            douyin_id=None,
            cli_target={"douyin_id": None, "sec_uid": None},
        )
        self.assertEqual(sec_uid, DEFAULT_SEC_UID)
        self.assertIsNone(douyin_id)

    def test_resolve_target_user_from_douyin_id(self):
        auth = object()
        resolver = Mock(return_value={
            "uid": "75571828104",
            "sec_uid": "MS4w-target",
            "short_id": "379250456",
            "unique_id": "",
            "nickname": "HAHA.",
        })
        target = main_mod.resolve_target_user(
            auth=auth,
            sec_uid=None,
            douyin_id="379250456",
            resolver=resolver,
        )
        self.assertEqual(target["uid"], "75571828104")
        self.assertEqual(target["sec_uid"], "MS4w-target")
        resolver.assert_called_once_with(auth, "379250456")

    def test_normalize_search_user_item_supports_nested_user_info(self):
        item = {
            "user_info": {
                "uid": "75571828104",
                "sec_uid": "MS4w-target",
                "short_id": "379250456",
                "unique_id": "",
                "nickname": "HAHA.",
            }
        }
        target = main_mod.normalize_search_user_item(item)
        self.assertEqual(target["uid"], "75571828104")
        self.assertEqual(target["sec_uid"], "MS4w-target")
        self.assertEqual(target["short_id"], "379250456")
        self.assertEqual(target["nickname"], "HAHA.")

    def test_select_search_user_prefers_exact_short_id(self):
        item1 = {"user_info": {"uid": "1", "short_id": "111111", "nickname": "A"}}
        item2 = {"user_info": {"uid": "2", "short_id": "379250456", "nickname": "B"}}
        target, candidates = main_mod.select_search_user("379250456", [item1, item2])
        self.assertEqual(target["uid"], "2")
        self.assertEqual(len(candidates), 2)


class TestSearchContext(unittest.TestCase):
    def test_parse_search_context_text_extracts_headers_params_and_cookies(self):
        text = """
import requests

headers = {
    'referer': 'https://www.douyin.com/search/379250456?aid=test-aid&type=user',
    'uifid': 'uifid-value',
    'user-agent': 'UA',
    'cookie': 'sessionid=session-1; s_v_web_id=verify_abc; IsDouyinActive=true',
}

params = {
    'keyword': '379250456',
    'search_source': 'normal_search',
    'is_filter_search': '0',
    'count': '12',
    'webid': '7650094009012864555',
    'msToken': 'token-1',
    'verifyFp': 'verify_abc',
    'fp': 'verify_abc',
    'a_bogus': 'bogus-1',
}
"""
        ctx = main_mod.parse_search_context_text(text)
        self.assertEqual(ctx["headers"]["uifid"], "uifid-value")
        self.assertEqual(ctx["params"]["keyword"], "379250456")
        self.assertEqual(ctx["cookies"]["sessionid"], "session-1")
        self.assertEqual(ctx["cookies"]["s_v_web_id"], "verify_abc")

    def test_build_search_user_request_prefers_loaded_search_context(self):
        auth = Mock()
        ctx = {
            "headers": {
                "referer": "https://www.douyin.com/search/379250456?aid=test-aid&type=user",
                "uifid": "uifid-value",
                "user-agent": "UA",
                "cookie": "sessionid=session-1; s_v_web_id=verify_abc",
            },
            "params": {
                "keyword": "379250456",
                "search_source": "normal_search",
                "is_filter_search": "0",
                "count": "12",
                "webid": "7650094009012864555",
                "msToken": "token-1",
                "verifyFp": "verify_abc",
                "fp": "verify_abc",
                "a_bogus": "bogus-1",
            },
            "cookies": {
                "sessionid": "session-1",
                "s_v_web_id": "verify_abc",
            },
        }
        headers, params, cookies = main_mod.build_search_user_request(auth, "123456789", search_context=ctx)
        self.assertEqual(headers.get()["uifid"], "uifid-value")
        self.assertEqual(params.get()["keyword"], "123456789")
        self.assertEqual(params.get()["search_source"], "normal_search")
        self.assertEqual(params.get()["verifyFp"], "verify_abc")
        self.assertEqual(cookies["sessionid"], "session-1")

    @patch("send_dm.__main__.generate_a_bogus", return_value="bogus-new")
    def test_build_search_user_request_keeps_context_a_bogus_when_keyword_changes(self, gen_ab):
        auth = Mock()
        ctx = {
            "headers": {
                "referer": "https://www.douyin.com/search/379250456?aid=test-aid&type=user",
                "uifid": "uifid-value",
                "user-agent": "UA-CHROME-147",
                "cookie": "sessionid=session-1; s_v_web_id=verify_abc",
            },
            "params": {
                "keyword": "379250456",
                "search_source": "normal_search",
                "is_filter_search": "0",
                "count": "12",
                "webid": "7650094009012864555",
                "msToken": "token-1",
                "verifyFp": "verify_abc",
                "fp": "verify_abc",
                "a_bogus": "bogus-old",
            },
            "cookies": {
                "sessionid": "session-1",
                "s_v_web_id": "verify_abc",
            },
        }
        headers, params, cookies = main_mod.build_search_user_request(auth, "84907325057", search_context=ctx)
        self.assertEqual(params.get()["a_bogus"], "bogus-old")
        self.assertEqual(cookies["sessionid"], "session-1")
        self.assertEqual(headers.get()["user-agent"], "UA-CHROME-147")
        gen_ab.assert_not_called()

    @patch("send_dm.__main__.generate_a_bogus", return_value="bogus-new")
    def test_build_search_user_request_generates_a_bogus_when_context_missing_it(self, gen_ab):
        auth = Mock()
        ctx = {
            "headers": {
                "referer": "https://www.douyin.com/search/379250456?aid=test-aid&type=user",
                "uifid": "uifid-value",
                "user-agent": "UA-CHROME-147",
                "cookie": "sessionid=session-1; s_v_web_id=verify_abc",
            },
            "params": {
                "keyword": "379250456",
                "search_source": "normal_search",
                "is_filter_search": "0",
                "count": "12",
                "webid": "7650094009012864555",
                "msToken": "token-1",
                "verifyFp": "verify_abc",
                "fp": "verify_abc",
            },
            "cookies": {
                "sessionid": "session-1",
                "s_v_web_id": "verify_abc",
            },
        }
        headers, params, cookies = main_mod.build_search_user_request(auth, "84907325057", search_context=ctx)
        self.assertEqual(params.get()["a_bogus"], "bogus-new")
        self.assertEqual(cookies["sessionid"], "session-1")
        self.assertEqual(headers.get()["user-agent"], "UA-CHROME-147")
        _, kwargs = gen_ab.call_args
        self.assertEqual(kwargs["ua"], "UA-CHROME-147")


class TestHandleSend(unittest.IsolatedAsyncioTestCase):
    @patch("send_dm.__main__.DMClient.send_msg")
    @patch("send_dm.__main__.DMClient.create_conversation")
    @patch("send_dm.__main__.resolve_target_user")
    @patch("send_dm.__main__.build_dm_auth", new_callable=AsyncMock)
    async def test_handle_send_uses_douyin_id_resolution(
        self,
        build_auth,
        resolve_target_user,
        create_conversation,
        send_msg,
    ):
        auth = object()
        build_auth.return_value = (auth, "E:/DY/Douyin_Spider/.env")
        resolve_target_user.return_value = {
            "uid": "75571828104",
            "sec_uid": "MS4w-target",
            "short_id": "379250456",
            "unique_id": "",
            "nickname": "HAHA.",
        }
        create_conversation.return_value = ("cid", 123, "ticket")
        send_msg.return_value = {"message": "OK"}

        await main_mod.handle_send(
            content="测试私信收发功能",
            sec_uid=None,
            douyin_id="379250456",
            profile="profile",
            env_file=None,
        )

        resolve_target_user.assert_called_once_with(auth, None, "379250456")
        create_conversation.assert_called_once_with(auth, 75571828104)
        send_msg.assert_called_once_with(auth, "cid", 123, "ticket", "测试私信收发功能")


class TestMainDispatch(unittest.TestCase):
    @patch("send_dm.__main__.asyncio.run")
    @patch("send_dm.__main__.handle_send")
    def test_main_prefers_explicit_douyin_id_over_shorthand_numeric(self, handle_send, asyncio_run):
        asyncio_run.side_effect = lambda coroutine: coroutine.close()
        with patch("sys.argv", ["python", "379250456", "测试私信收发功能", "--douyin-id", "888888"]):
            main_mod.main()

        asyncio_run.assert_called_once()
        handle_send.assert_called_once_with("测试私信收发功能", None, "888888", str(main_mod.DEFAULT_PROFILE), None)


if __name__ == "__main__":
    unittest.main()
