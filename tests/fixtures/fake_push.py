"""테스트용 푸시 발송기."""


class FakePushSender:
    def __init__(self, dead_tokens=None, raise_error=False):
        self.sent = []
        self.dead_tokens = dead_tokens or []
        self.raise_error = raise_error

    def send(self, messages):
        if self.raise_error:
            raise RuntimeError("expo push down")
        self.sent.extend(messages)
        return list(self.dead_tokens)
