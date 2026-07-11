"""테스트용 네이버 OAuth 클라이언트 — HTTP 없음."""


class FakeNaverClient:
    def __init__(self, profile=None):
        self.profile = profile or {
            "oauth_id": "naver-98765",
            "email": "naver_user@test.local",
            "nickname": "네이버유저",
        }
        self.exchanged = []

    def get_authorize_url(self, state):
        return f"https://nid.naver.com/oauth2.0/authorize?client_id=fake&state={state}"

    def exchange_token(self, code, state):
        self.exchanged.append((code, state))
        return "fake-naver-token"

    def get_profile(self, access_token):
        assert access_token == "fake-naver-token"
        return dict(self.profile)
