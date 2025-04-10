from django.shortcuts import render

# Create your views here.
# myproject/auth/views.py
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .kakao_api import KakaoAPI

def kakao_login_request(request):
    kakao_api = KakaoAPI()
    authorization_url = kakao_api.get_authorization_url()
    return redirect(authorization_url)

def kakao_login_callback(request):
    code = request.GET.get('code')
    if code:
        kakao_api = KakaoAPI()
        try:
            access_token = kakao_api.get_access_token(code)
            user_info = kakao_api.get_user_info(access_token)

            kakao_id = user_info.get('id')
            kakao_email = user_info.get('kakao_account', {}).get('email')
            kakao_nickname = user_info.get('properties', {}).get('nickname')

            if kakao_id:
                try:
                    user = User.objects.get(username=kakao_id)
                    login(request, user)
                    return redirect('home')  # 로그인 성공 후 리다이렉트할 URL
                except User.DoesNotExist:
                    # 카카오 계정으로 처음 로그인하는 경우, 사용자 생성
                    new_user = User.objects.create_user(username=kakao_id, email=kakao_email, first_name=kakao_nickname)
                    login(request, new_user)
                    return redirect('home')  # 로그인 성공 후 리다이렉트할 URL
        except Exception as e:
            print(f"카카오 로그인 오류: {e}")
            return redirect('login_failed')  # 로그인 실패 페이지로 리다이렉트
    return redirect('login')  # 인가 코드 없음

def kakao_logout_request(request):
    # 실제 로그아웃 로직은 프론트엔드에서 Kakao SDK를 사용하는 것이 일반적입니다.
    # 서버 측에서 연결 해제를 원한다면 Access Token을 얻어 처리해야 합니다.
    # 여기서는 단순히 서비스 로그아웃만 처리합니다.
    from django.contrib.auth import logout
    logout(request)
    return redirect('home') # 로그아웃 후 리다이렉트할 URL