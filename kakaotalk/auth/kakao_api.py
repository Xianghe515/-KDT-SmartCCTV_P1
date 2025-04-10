# kakaotalk/auth/kakao_api.py
import requests
from urllib.parse import urlencode
from flask import current_app

class KakaoAPI:
    def __init__(self):
        self.rest_api_key = current_app.config['KAKAO_REST_API_KEY']
        self.redirect_uri = current_app.config['KAKAO_REDIRECT_URI']
        self.authorization_url = "https://kauth.kakao.com/oauth/authorize"
        self.token_url = "https://kauth.kakao.com/oauth/token"
        self.user_info_url = "https://kapi.kakao.com/v2/user/me"
        self.unlink_url = "https://kapi.kakao.com/v1/user/unlink"

    def get_authorization_url(self):
        params = {
            "client_id": self.rest_api_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    def get_access_token(self, code):
        headers = {'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'}
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.rest_api_key,
            'redirect_uri': self.redirect_uri,
            'code': code,
        }
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"Access Token 요청 실패: {e}")
            return None

    def get_user_info(self, access_token):
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        try:
            response = requests.post(self.user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"사용자 정보 요청 실패: {e}")
            return None

    def kakao_logout(self, access_token):
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        try:
            response = requests.post(self.unlink_url, headers=headers) # 카카오 로그아웃 API는 unlink와 동일합니다.
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"카카오 로그아웃 실패: {e}")
            return None