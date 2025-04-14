import os
import smtplib
import mimetypes
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app

class EmailService:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email(self, recipient_email, subject, body, save_path=None, original_filename=None):
        msg = MIMEMultipart()
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = recipient_email

        # 본문 추가
        msg.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))

        # 첨부파일 (옵션)
        if save_path and original_filename:
            try:
                mime_type, _ = mimetypes.guess_type(original_filename)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                maintype, subtype = mime_type.split('/', 1)

                with open(save_path, 'rb') as attachment:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)

                filename_header = Header(original_filename, 'utf-8')
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{str(filename_header)}\"",
                )
                part.add_header("Content-Type", mime_type)

                msg.attach(part)
            except Exception as e:
                print(f"첨부 파일 오류: {e}")

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string().encode('utf-8'))
                print("이메일 전송 성공")
                return True
        except Exception as e:
            print(f"이메일 전송 실패: {e}")
            return False