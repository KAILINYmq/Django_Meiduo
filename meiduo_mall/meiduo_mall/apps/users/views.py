from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CreateUserSerializer
from .models import User


# Create your views here.
class UserView(CreateAPIView):
    """注册"""

    # 指定序列化器类
    serializer_class = CreateUserSerializer


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