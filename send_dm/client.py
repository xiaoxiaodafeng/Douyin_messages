import hashlib
import json

import requests
from protobuf_to_dict import protobuf_to_dict

from .assets import Response_pb2 as ResponseProto
from .header import HeaderBuilder, HeaderType
from .params import Params
from .proto_builder import ProtoBuilder
from .utils import generate_a_bogus, generate_msToken, splice_url

requests.packages.urllib3.disable_warnings()


class DMClient:
    douyin_url = "https://www.douyin.com"

    @staticmethod
    def get_my_uid(auth) -> int:
        url = "https://www.douyin.com/aweme/v1/web/query/user/"
        headers = HeaderBuilder().build(HeaderType.GET)
        refer = "https://www.douyin.com/"
        headers.set_header("referer", refer)
        params = Params()
        params.with_platform()
        params.with_web_id(auth, refer)
        params.with_ms_token()
        params.add_param("verifyFp", auth.cookie["s_v_web_id"])
        params.add_param("fp", auth.cookie["s_v_web_id"])
        params.with_a_bogus()
        resp = requests.get(url, params=params.get(), verify=False, headers=headers.get(), cookies=auth.cookie)
        return int(json.loads(resp.text)["user_uid"])

    @staticmethod
    def get_user_info(auth, user_url: str) -> dict:
        api = "/aweme/v1/web/user/profile/other/"
        user_id = user_url.split("/")[-1].split("?")[0]
        headers = HeaderBuilder().build(HeaderType.GET)
        headers.set_referer(user_url)
        params = Params()
        params.add_param("device_platform", "webapp")
        params.add_param("aid", "6383")
        params.add_param("channel", "channel_pc_web")
        params.add_param("publish_video_strategy_type", "2")
        params.add_param("source", "channel_pc_web")
        params.add_param("sec_user_id", user_id)
        params.add_param("personal_center_strategy", "1")
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
        params.add_param("round_trip_time", "50")
        params.with_web_id(auth, user_url)
        params.add_param("msToken", auth.msToken)
        params.with_a_bogus()
        params.add_param("verifyFp", auth.cookie["s_v_web_id"])
        params.add_param("fp", auth.cookie["s_v_web_id"])
        resp = requests.get(f"{DMClient.douyin_url}{api}", headers=headers.get(), cookies=auth.cookie, params=params.get(), verify=False)
        return json.loads(resp.text)

    @staticmethod
    def get_device_id(auth) -> str:
        url = "https://www.douyin.com/aweme/v1/web/query/user"
        headers = HeaderBuilder().build(HeaderType.GET)
        refer = "https://www.douyin.com/discover"
        headers.set_header("referer", refer)
        params = (
            Params()
            .with_platform()
            .add_param("publish_video_strategy_type", "2")
            .with_web_id(auth, refer)
            .with_ms_token()
            .add_param("verifyFp", auth.cookie["s_v_web_id"])
            .add_param("fp", auth.cookie["s_v_web_id"])
            .with_a_bogus()
        )
        resp = requests.get(url, params=params.get(), verify=False, headers=headers.get(), cookies=auth.cookie)
        return json.loads(resp.text)["id"]

    @staticmethod
    def create_conversation(auth, to_user_id: int):
        url = "https://imapi.douyin.com/v2/conversation/create"
        requestProto = ProtoBuilder.build_create_conversation_request(auth, to_user_id, auth.get_uid())
        headers = HeaderBuilder().build(HeaderType.PROTOBUF)
        headers.set_header("referer", "https://www.douyin.com/")
        resp = requests.post(url, headers=headers.get(), cookies=auth.cookie, data=requestProto.SerializeToString(), verify=False)
        responseProto = ResponseProto.Response()
        responseProto.ParseFromString(resp.content)
        resp_json = protobuf_to_dict(responseProto)
        conversation = resp_json["body"]["create_conversation_v2_body"]["conversation_info_list"][0]
        return conversation["conversation_id"], conversation["conversation_short_id"], conversation["ticket"]

    @staticmethod
    def get_conversation_info(auth, to_user_id: int, conversation_short_id: int):
        import blackboxprotobuf

        url = "https://imapi.douyin.com/v2/conversation/get_info_list"
        requestProto = ProtoBuilder.build_get_conversation_list_info_request(auth, to_user_id, auth.get_uid(), conversation_short_id)
        headers = HeaderBuilder().build(HeaderType.PROTOBUF)
        headers.set_header("referer", "https://www.douyin.com/")
        resp = requests.post(url, headers=headers.get(), cookies=auth.cookie, data=requestProto.SerializeToString(), verify=False)
        try:
            deserialized_data, _ = blackboxprotobuf.decode_message(resp.content)
            return deserialized_data
        except Exception:
            return None

    @staticmethod
    def send_msg(auth, conversation_id, conversation_short_id, ticket, content: str):
        url = "https://imapi.douyin.com/v1/message/send"
        headers = HeaderBuilder().build(HeaderType.PROTOBUF)
        headers.set_header("referer", "https://www.douyin.com/")
        requestProto = ProtoBuilder.build_send_message_request(auth, conversation_id, conversation_short_id, ticket, content)
        params = {
            "verifyFp": auth.cookie["s_v_web_id"],
            "fp": auth.cookie["s_v_web_id"],
            "msToken": generate_msToken(),
        }
        query = splice_url(params)
        params["a_bogus"] = generate_a_bogus(query)
        resp = requests.post(url, params=params, headers=headers.get(), verify=False, cookies=auth.cookie, data=requestProto.SerializeToString())
        responseProto = ResponseProto.Response()
        responseProto.ParseFromString(resp.content)
        return protobuf_to_dict(responseProto)

    @staticmethod
    def resolve_user(auth, sec_uid: str):
        info = DMClient.get_user_info(auth, f"https://www.douyin.com/user/{sec_uid}")
        user = info.get("user") or {}
        return {
            "uid": user.get("uid"),
            "sec_uid": user.get("sec_uid") or sec_uid,
            "short_id": user.get("short_id"),
            "unique_id": user.get("unique_id"),
            "nickname": user.get("nickname"),
            "raw": info,
        }
