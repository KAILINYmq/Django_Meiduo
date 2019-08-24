from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.conf import settings

from . import constants

# Create your models here.

class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_send_sms_code_token(self):
        """
        找回密码生成短信验证码的access_token
        :return: access_token
        """
        serialier = TJWSSerializer(settings.SECRET_KEY, constants.SEND_SMS_CODE_TOKEN_EXIPIRES)
        data = {
            'mobile': self.mobile
        }
        token = serialier.dumps(data)
        return token.decode()

    @staticmethod
    def check_send_sms_code_token(token):
        """
        找回密码时检验access token
        :param token: access token
        :return: mobile None
        """
        # 创建itsdangerous模型的转换工具
        serialize = TJWSSerializer(settings.SECRET_KEY, constants.SEND_SMS_CODE_TOKEN_EXIPIRES)
        try:
            data = serialize.loads(token)
        except BadData:
            return None
        else:
            mobile = data.get('mobile')
            return mobile

    def generate_set_password_token(self):
        """
        生成修改密码的token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SET_PASSWORD_TOKEN_EXPIRES)
        data = {'user_id': self.id}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_set_password_token(token, user_id):
        """
        检验设置密码的token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SET_PASSWORD_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return  False
        else:
            if user_id != str(data.get('user_id')):
                return False
            else:
                return True











