from .client import DMClient


class AutoReplyService:
    def __init__(self, auth, llm_client, system_prompt: str, max_context_messages: int = 12):
        self.auth = auth
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.max_context_messages = max(2, max_context_messages)
        self.my_uid = str(auth.get_uid())
        self.histories: dict[str, list[dict[str, str]]] = {}

    def build_messages(self, conversation_id: str) -> list[dict[str, str]]:
        history = self.histories.get(conversation_id, [])
        return [{"role": "system", "content": self.system_prompt}] + history[-self.max_context_messages :]

    def handle_event(self, event: dict):
        if event.get("message_type") != 7:
            return

        sender = str(event.get("sender") or "")
        if not sender or sender == self.my_uid:
            return

        conversation_id = str(event.get("conversation_id") or "")
        text = str(event.get("text") or "").strip()
        if not conversation_id or not text:
            return

        history = self.histories.setdefault(conversation_id, [])
        history.append({"role": "user", "content": text})

        try:
            reply = self.llm_client.chat(self.build_messages(conversation_id))
            history.append({"role": "assistant", "content": reply})
            if len(history) > self.max_context_messages:
                del history[:-self.max_context_messages]

            cid, csid, ticket = DMClient.create_conversation(self.auth, int(sender))
            result = DMClient.send_msg(self.auth, cid, csid, ticket, reply)
            print("自动回复:", {"sender": sender, "conversation_id": conversation_id, "reply": reply, "result": result})
        except Exception as exc:
            if history and history[-1] == {"role": "user", "content": text}:
                history.pop()
            print("自动回复失败:", {"sender": sender, "conversation_id": conversation_id, "error": str(exc)})
