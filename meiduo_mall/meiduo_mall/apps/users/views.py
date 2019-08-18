from django.shortcuts import render
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import re

from users import serializers
from .serializers import CreateUserSerializer
from .models import User
from verifications.serializers import CheckImageCodeSerialzier
from .utils import get_user_by_account

# Create your views here.
class UsernameCountView(APIView):
    """判断用户名是否已存在"""
    def get(self, request, username):
        # 用username去User模型中查询此用户名的数据
        # count:查到数据了会返回条数，没有查询到则会返回0
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }
        # 响应
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否已存在"""
    def get(self, request, mobile):
        # 用username去User模型中查询此用户名的数据
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }
        # 响应
        return Response(data)

class UserView(CreateAPIView):
    """注册"""
    # 指定序列化器类
    serializer_class = CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """获取发送短信验证码的凭据"""

    serializer_class = CheckImageCodeSerialzier

    def get(self, request, account):
        # 校验图片验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 根据account查询User对象
        user = get_user_by_account(account)
        if user is None:
            return  Response({"message": '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        # 根据User对象的手机号生成access_token
        access_token = user.generate_send_sms_code_token()

        # 修改手机号
        mobile = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1****\2', user.mobile)

        return Response({
            'mobile': mobile,
            'access_token': access_token
        })

class PasswordTokenView(GenericAPIView):
    """
    找回密码时用户设置账密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer
    def get(self, request, account):
        """
        根据用户账号获取修改密码的token
        """
        # 检验短信验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()
        return Response({'user_id': user.id, 'access_token': access_token})
