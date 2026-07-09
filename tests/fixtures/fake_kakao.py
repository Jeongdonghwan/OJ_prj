"""테스트용 카카오 OAuth 클라이언트 — HTTP 없음."""


class FakeKakaoClient:
    def __init__(self, profile=None):
        self.profile = profile or {
            "oauth_id": "kakao-12345",
            "email": "kakao_user@test.local",
            "nickname": "카카오유저",
        }
        self.exchanged_codes = []

    def get_authorize_url(self):
        return "https://kauth.kakao.com/oauth/authorize?client_id=fake"

    def exchange_token(self, code):
        self.exchanged_codes.append(code)
        return "fake-access-token"

    def get_profile(self, access_token):
        assert access_token == "fake-access-token"
        return dict(self.profile)
