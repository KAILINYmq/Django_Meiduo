from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
import re
from rest_framework.permissions import IsAuthenticated

from users import serializers
from .serializers import CreateUserSerializer
from .models import User
from . import constants
from verifications.serializers import CheckImageCodeSerialzier
from .utils import get_user_by_account
from goods.models import SKU
from goods.serializers import SKUSerializer
from carts.utils import merge_cart_cookie_to_redis

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

class PasswordView(mixins.UpdateModelMixin, GenericAPIView):
    """
    找回密码，用户密码修改
    """
    queryset = User.objects.all()
    serializer_class = serializers.RestPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)

class UserDetailView(RetrieveAPIView):
    """
    用户详情信息
    """
    serializer_class = serializers.UserDetailSerializer
    # 补充通过认证才能访问接口的权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        返回请求的用户对象
        :return: user
        """
        return self.request.user

class EmailView(UpdateAPIView):
    """
    保存邮件
    /email/
    """
    serializer_class = serializers.EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class EmailVerifyView(APIView):
    """验证邮箱"""
    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 校验 保存
        result = User.check_email_veerify_token(token)

        if result:
            return Response({"message": "OK"})
        else:
            return Response({"非法的token"}, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = serializers.UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            # 'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """用户浏览历史记录"""
    permission_classes = [IsAuthenticated]             # 必须登录之后才能获取
    serializer_class = serializers.AddUserHistorySerializer

    def post(self, request):
        """保存"""
        return self.create(request)

    def get(self, request):
        """返回用户详情页的浏览记录数据"""
        user_id = request.user.id
        # 查询redis数据库
        redis_conn = get_redis_connection('history')
        sku_id_list = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT)

        # 根据redis返回的sku id 查询数据
        # SKU.objects.filter(id__in=sku_id_list)
        sku_list = []
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)

        # 使用序列化器序列化
        serializer = SKUSerializer(sku_list, many=True)
        return Response(serializer.data)

class UserAuthorizationView(ObtainJSONWebToken):
    """用户登录合并购物车"""
    def post(self, request):
        # 调用jwt父类的扩展方法，对用户登录的数据进行验证
        response = super().post(request)

        # 如果用户登录成功，进行购物车数据合并
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 表示用户登陆成功
            user = serializer.validated_data.get("user")
            # 调用合并购物车方法
            response = merge_cart_cookie_to_redis(request, response, user)

        return response













