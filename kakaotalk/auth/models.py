from django.db import models

class DjangoUser(models.Model):
    user_name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # 해싱된 비밀번호 저장
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    social_platform = models.CharField(max_length=20, null=True, blank=True)
    kakao_access_token = models.CharField(max_length=255, null=True, blank=True)
    kakao_user_id = models.BigIntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.user_name

class DjangoVideo(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    detected_objects = models.CharField(max_length=255, null=True, blank=True)
    camera_id = models.IntegerField(null=True, blank=True) # 예시

    def __str__(self):
        return self.filename

class DjangoLog(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    action_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user_name} - {self.action}"

class DjangoCamera(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_name