"""소셜 OAuth 클라이언트(카카오/네이버) — app.extensions로 주입, 테스트는 Fake 교체."""
import requests

AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
PROFILE_URL = "https://kapi.kakao.com/v2/user/me"

NAVER_AUTHORIZE_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"


class KakaoOAuthClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorize_url(self):
        return (f"{AUTHORIZE_URL}?client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}&response_type=code")

    def exchange_token(self, code):
        res = requests.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }, timeout=10)
        res.raise_for_status()
        return res.json()["access_token"]

    def get_profile(self, access_token):
        res = requests.get(PROFILE_URL, headers={
            "Authorization": f"Bearer {access_token}"}, timeout=10)
        res.raise_for_status()
        data = res.json()
        return {
            "oauth_id": str(data["id"]),
            "email": (data.get("kakao_account") or {}).get("email"),
            "nickname": ((data.get("kakao_account") or {}).get("profile") or {}).get("nickname"),
        }


class NaverOAuthClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorize_url(self, state):
        return (f"{NAVER_AUTHORIZE_URL}?response_type=code&client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}&state={state}")

    def exchange_token(self, code, state):
        res = requests.post(NAVER_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "state": state,
        }, timeout=10)
        res.raise_for_status()
        return res.json()["access_token"]

    def get_profile(self, access_token):
        res = requests.get(NAVER_PROFILE_URL, headers={
            "Authorization": f"Bearer {access_token}"}, timeout=10)
        res.raise_for_status()
        data = res.json().get("response") or {}
        return {
            "oauth_id": str(data["id"]),
            "email": data.get("email"),
            "nickname": data.get("nickname"),
        }


def get_kakao_client(app):
    if "kakao_oauth" not in app.extensions:
        app.extensions["kakao_oauth"] = KakaoOAuthClient(
            app.config["KAKAO_CLIENT_ID"],
            app.config["KAKAO_CLIENT_SECRET"],
            app.config["KAKAO_REDIRECT_URI"],
        )
    return app.extensions["kakao_oauth"]


def get_naver_client(app):
    if "naver_oauth" not in app.extensions:
        app.extensions["naver_oauth"] = NaverOAuthClient(
            app.config["NAVER_CLIENT_ID"],
            app.config["NAVER_CLIENT_SECRET"],
            app.config["NAVER_REDIRECT_URI"],
        )
    return app.extensions["naver_oauth"]
