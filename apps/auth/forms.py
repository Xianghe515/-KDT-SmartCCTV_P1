from flask_wtf import FlaskForm  # type:ignore
from wtforms import PasswordField, StringField, SubmitField, FieldList, FormField, HiddenField, FileField, TextAreaField, BooleanField  # type:ignore
from wtforms.validators import DataRequired, Email, Length  # type:ignore
from wtforms.validators import Regexp, Optional, ValidationError


class SignUpForm(FlaskForm):
      user_name = StringField(
            "사용자명",
            validators=[
                  DataRequired("사용자명은 필수입니다."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
      ],
      )
      email = StringField(
            "메일 주소",
            validators=[
                  DataRequired("메일 주소는 필수입니다."),
                  Email("메일 주소의 형식으로 입력해주세요."),
            ],
      )
      password = PasswordField(
            "비밀번호",
            validators=[
                  DataRequired("비밀번호는 필수입니다."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
            ],
      )
      birth_date = StringField(
            "생년월일",
            validators=[
                 Optional(),
                  Regexp(
                        r"^\d{4}-\d{2}-\d{2}$",
                        message="YYYY-MM-DD 형식으로 입력해주세요."
                        ),
      ],
      )
      phone_number = StringField(
            "전화번호",
            validators=[
                  DataRequired("전화번호는 필수입니다."),
                  Regexp(
                        r"^\d{3}-\d{4}-\d{4}$",
                        message="000-0000-0000 형식으로 입력해주세요."
                        ),
      ],
      )
      submit = SubmitField("회원가입")
      
class LoginForm(FlaskForm):
      email = StringField(
                      "메일 주소",
            validators=[
                  DataRequired("메일 주소는 필수입니다."),
                  Email("메일 주소의 형식으로 입력해주세요."),
            ],
      )  
      password = PasswordField("비밀번호",
            validators=[DataRequired("비밀번호는 필수입니다.")])
      submit = SubmitField("로그인")

class UpdateForm(FlaskForm):
#       # 이름, 전화번호, 생일, 비밀번호 + 장치 식별 번호
      user_name = StringField(
            "사용자명",
            validators=[
                  DataRequired("사용자명은 필수입니다."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
      ],
      )

      birth_date = StringField(
            "생년월일",
            validators=[
                  Optional(),
                  Regexp(
                        r"^\d{4}-\d{2}-\d{2}$",
                        message="YYYY-MM-DD 형식으로 입력해주세요."
                        ),
      ],
      )
      phone_number = StringField(
            "전화번호",
            validators=[
                  Regexp(
                        r"^\d{3}-\d{4}-\d{4}$",
                        message="010-0000-0000 형식으로 입력해주세요."
                        ),
      ],
      )
      submit = SubmitField("수정")

class PasswordForm(FlaskForm):
      current_password = PasswordField(
            "현재 비밀번호",
            validators=[
                  DataRequired("현재 비밀번호를 입력해주세요."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
            ],
      )
      new_password = PasswordField(
            "새 비밀번호",
            validators=[
                  DataRequired("새 비밀번호를 입력해주세요."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
            ],
      )
      submit = SubmitField("변경")

    # IP 주소 유효성 검사 함수
def validate_ip_range(form, field):
    if not field.data.isdigit() or not (0 <= int(field.data) <= 255):
        raise ValidationError("0~255 사이의 숫자여야 합니다.")
    
class SingleDeviceForm(FlaskForm):
    camera_id = HiddenField()
    device_id = StringField(
        "일련번호",
        validators=[
            DataRequired("일련번호는 필수입니다."),
            Regexp(r"^\w{4}-\w{4}$", message="****-**** 형식으로 입력해주세요."),
        ],
    )
    device_name = StringField(
         "기기 별명",
         validators=[
              Optional(),
              Length(0, 15, "15문자 이내로 입력해주세요."),
         ],
    )
    ip_address_1 = StringField(validators=[DataRequired("IP 주소는 필수입니다."), Regexp(r"^\d{1,3}$"), validate_ip_range])
    ip_address_2 = StringField(validators=[DataRequired("IP 주소는 필수입니다."), Regexp(r"^\d{1,3}$"), validate_ip_range])
    ip_address_3 = StringField(validators=[DataRequired("IP 주소는 필수입니다."), Regexp(r"^\d{1,3}$"), validate_ip_range])
    ip_address_4 = StringField(validators=[DataRequired("IP 주소는 필수입니다."), Regexp(r"^\d{1,3}$"), validate_ip_range])


    def get_full_ip(self):
        return f"{self.ip_address_1.data}.{self.ip_address_2.data}.{self.ip_address_3.data}.{self.ip_address_4.data}"

        
class DeviceForm(FlaskForm):
    devices = FieldList(
         FormField(SingleDeviceForm), min_entries=1, max_entries=3,
         validators=[DataRequired("IP 주소는 필수입니다.")]
         )
    submit = SubmitField("등록")

class DeleteForm(FlaskForm):
     submit = SubmitField("삭제")

class SupportForm(FlaskForm):
      email = StringField(
            "메일 주소",
            validators=[
                  DataRequired("메일 주소는 필수입니다."),
                  Email("메일 주소의 형식으로 입력해주세요."),
            ],
      )
      title = StringField(
            "제목",
            validators=[
                  DataRequired("제목은 필수입니다."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
            ],
      )
      text = TextAreaField(
           "문의 내용",
           validators=[
                  DataRequired("문의 내용을 입력해주세요."),
                  Length(10, 1000, "10문자 이상, 500문자 이내로 입력해주세요."),
           ]
      )
      file = FileField("첨부파일")  # 선택 사항
      
class DeleteUserForm(FlaskForm):
    confirm_delete = BooleanField('동의', validators=[DataRequired('계정 탈퇴에 동의해야 합니다.')])
    submit = SubmitField('탈퇴')