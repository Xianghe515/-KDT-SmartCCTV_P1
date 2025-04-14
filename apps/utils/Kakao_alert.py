import requests
import json

class Kakao_alert:
    def send_kakao_message(message, kakao_token):
        print(f"Loaded Token: {kakao_token}")

        if not kakao_token:
            print("카카오 Access Token이 설정되지 않았습니다.")
            return False

        headers = {
            'Authorization': f'Bearer {kakao_token}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }

        # 템플릿 객체 구성("text", "link", "button_title")
        template_object = {
            "object_type": "text",
            "text": message,
            "link": {
                "web_url": "https://google.com",  # 필요에 따라 바꿔줘
                "mobile_web_url": "https://google.com"
            },
            "button_title": "확인"
        }

        data = {
            'template_object': json.dumps(template_object, ensure_ascii=False)
        }

        url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'

        try:
            print(f"카카오톡 메시지 전송 시도 (URL: {url}, Data: {data})")
            response = requests.post(url, headers=headers, data=data)
            print(f"카카오톡 API 응답 상태 코드: {response.status_code}")
            response.raise_for_status()
            print("카카오톡 메시지 전송 성공:", response.json())
            return True
        except requests.exceptions.RequestException as e:
            print(f"카카오톡 메시지 전송 실패 (RequestException): {e}")
            if response is not None:
                print("응답 내용:", response.text)
            return False
        except Exception as e:
            print(f"카카오톡 메시지 전송 실패 (Unexpected Error): {e}")
            return False
