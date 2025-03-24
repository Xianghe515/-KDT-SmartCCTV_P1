from flask_wtf import FlaskForm  # type:ignore
from wtforms import PasswordField, StringField, SubmitField  # type:ignore
from wtforms.validators import DataRequired, Email, Length  # type:ignore
from wtforms.validators import Regexp


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
                  DataRequired("비밀번호는 필수입니다.")
            ],
      )
      device_id = StringField(
            "장치 식별 번호",
            validators=[
                  DataRequired("장치 식별 번호는 필수입니다."),
                  Length(2, 30, "2문자 이상, 30문자 이내로 입력해주세요."),
      ],
      )
      birth_date = StringField(
            "생년월일",
            validators=[
                  Regexp(
                        r"^\d{4}-\d{2}-\d{2}$",
                        # message="생년월일은 YYYY-MM-DD 형식으로 입력해야 합니다."
                        ),
      ],
      )
      phone_number = StringField(
            "전화번호",
            validators=[
                  Regexp(
                        r"^\d{3}-\d{4}-\d{4}$",
                        # message="전화번호는 000-0000-0000 형식으로 입력해야 합니다."
                        ),
      ],
      )
      submit = SubmitField("신규등록")
      
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