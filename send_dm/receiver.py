import hashlib
import json

import websocket
from websocket import WebSocketApp

from .assets import Live_pb2, Response_pb2
from .client import DMClient
from .header import HeaderBuilder
from .params import Params


class DouyinRecvMsg:
    appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
    fpId = "9"

    def __init__(self, auth, auto_reconnect=True, message_handler=None):
        self.auto_reconnect = auto_reconnect
        self.auth = auth
        self.message_handler = message_handler
        self.ws = None
        deviceId = DMClient.get_device_id(auth=self.auth)
        accessKey = f"{self.fpId + self.appKey + deviceId}f8a69f1719916z"
        accessKey = hashlib.md5(accessKey.encode("utf-8")).hexdigest()
        params = (
            Params()
            .add_param("aid", "6383")
            .add_param("device_platform", "douyin_pc")
            .add_param("fpid", self.fpId)
            .add_param("device_id", deviceId)
            .add_param("token", self.auth.cookie["sessionid"])
            .add_param("access_key", accessKey)
        )
        self.url = f"wss://frontier-im.douyin.com/ws/v2?{params.toString()}"

    def on_open(self, ws):
        print("WebSocket connection open.")

    @staticmethod
    def _parse_content(content: str):
        try:
            return json.loads(content)
        except Exception:
            return {"raw_text": content}

    def _build_event(self, response):
        message = response.body.new_message_notify.message
        content = self._parse_content(message.content)
        event = {
            "sender": str(message.sender),
            "message_type": message.message_type,
            "conversation_id": message.conversation_id,
            "index": message.index_in_conversation,
            "content": content,
            "raw_content": message.content,
        }
        if message.message_type == 7:
            event["text"] = content.get("text", "") if isinstance(content, dict) else ""
        return event

    @staticmethod
    def _print_event(event: dict):
        sender = event["sender"]
        conversation_id = event["conversation_id"]
        index = event["index"]
        msg_type = event["message_type"]
        content = event["content"]

        if msg_type == 7:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】文本消息:{content.get('text', '')}")
        elif msg_type == 5:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】表情包:{content['url']['url_list'][0]}")
        elif msg_type == 17:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】语音:{content['resource_url']['url_list'][0]}")
        elif msg_type == 27:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】图片:{content['resource_url']['origin_url_list'][0]}")
        elif msg_type == 8:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】分享视频ID:{content['itemId']}")
        elif msg_type == 50001:
            print(f"对方已读，消息标号:{content.get('read_index')}")
        else:
            print(f"【消息编号:{index}】【聊天室ID:{conversation_id}】【来自:{sender}】消息类型:{msg_type} 内容:{content}")

    def on_message(self, ws, message):
        frame = Live_pb2.PushFrame()
        frame.ParseFromString(message)
        if frame.payloadType == "pb":
            response = Response_pb2.Response()
            response.ParseFromString(frame.payload)
            event = self._build_event(response)
            self._print_event(event)
            if self.message_handler:
                self.message_handler(event)
        elif frame.payloadType == "text/json":
            print(json.loads(frame.payload))

    def on_error(self, ws, error):
        print("\033[31m### error ###")
        print(error)
        print("### ===error=== ###\033[m")
        if (type(error) == ConnectionRefusedError or type(error) == websocket._exceptions.WebSocketConnectionClosedException) and self.auto_reconnect:
            self.start()

    def on_close(self, ws, close_status_code, close_msg):
        print("\033[31m### closed ###")
        print(f"status_code: {close_status_code}, msg: {close_msg}")
        print("### ===closed=== ###\033[m")

    def start(self):
        self.ws = WebSocketApp(
            url=self.url,
            header={
                "Pragma": "no-cache",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "User-Agent": HeaderBuilder.ua,
                "Cache-Control": "no-cache",
                "Sec-WebSocket-Protocol": "binary, base64, pbbp2",
                "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            },
            cookie=self.auth.cookie_str,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        try:
            self.ws.run_forever(origin="https://www.douyin.com")
        except KeyboardInterrupt:
            self.ws.close()
        except Exception:
            self.ws.close()
