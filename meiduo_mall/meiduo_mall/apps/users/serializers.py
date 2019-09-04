from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from . models import User
from .utils import get_user_by_account

from celery_tasks.emails.tasks import send_verify_email
from .models import User, Address
from . import constants
from goods.models import SKU

class CreateUserSerializer(serializers.ModelSerializer):
    """注册序列化器"""
    print("注册序列化器OK")
    password2 = serializers.CharField(label='密码2', required=True, allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='验证码', required=True, allow_null=False, allow_blank=False, write_only=True)
    allow = serializers.CharField(label='同意协议', required=True, allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='JWT token登录状态', read_only=True)
    """
    序列化器中需要的所有字段: 'id', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow'
    模型中已有字段: id', 'username', 'mobile', 'password'
    需要进行序列化的字段: 'token', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow'
    需要进行反序列化的字段:  'id', 'username', 'mobile'
    """

    def validate_mobile(self, value):
        """对手机号单独追加校验逻辑"""
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机号格式有误')
        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('请勾选同意协议')
        return value

    def validate(self, attrs):
        # 对两个密码进行判断
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError('两次密码不一致')

        # 校验验证码
        mobile = attrs.get('mobile')
        # 创建redis连接
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # 向redis存储数据时,都是以字符串的格式存储进行,将来获取出来后,都会变成'bytes'类型: str: bytes hash: {b'key':b''} list:[b'',] set:[b'']
        if not real_sms_code:
            raise serializers.ValidationError('验证码过期')
        # 此处一定要注意从redis中取出来的字符串是bytes类型需要转换成str
        if real_sms_code.decode() != attrs.get('sms_code'):
            raise serializers.ValidationError('验证码有误')
        return attrs

    def create(self, validated_data):
        """重写序列化器的保存方法把多余数据移除(创建用户)"""
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        # user = User.objects.create(**validated_data)
        user = User(**validated_data)
        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()
        # 手动生成JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token的函数
        payload = jwt_payload_handler(user)  # 通过传入user对象生成jwt 载荷部分
        token = jwt_encode_handler(payload)  # 传入payload 生成token
        # 将token保存到user对象中，随着返回值返回给前端
        user.token = token
        print("保存OK")
        return user

    class Meta:
        print("MetaOK")
        model = User
        fields = ['id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token']
        extra_kwargs = {  # 对序列化器中的字段进行额外配置
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义反序列化校验错误信息
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,  # 只做反序列化
                'min_length': 8,
                'max_length ': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

class CheckSMSCodeSerializer(serializers.Serializer):
    """
    检查sms code
    """
    sms_code = serializers.CharField(min_length=6, max_length=6)
    def validate_sms_code(self, value):
        account = self.context['view'].kwargs['account']
        # 获取user
        user = get_user_by_account(account)
        if user is None:
                raise serializers.ValidationError('用户不存在')
        # 把user对象保存到序列化器对象中
        self.user = user
        # 检验短信验证码
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if value != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')
        return value

class RestPasswordSerializer(serializers.ModelSerializer):
    """
    找回密码，重置密码序列化器
    """
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='操作token', write_only=True)

    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password':{
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        """
        校验数据
        """
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断access token
        # 需要对比 access token中的user_id与请求用户的id是否一致
        allow = User.check_send_sms_code_token(attrs['access_token'], self.context['view'].kwargs['pk'])
        if not allow:
            raise serializers.ValidationError('无效的access token')
        return attrs

    def update(self, instance, validated_data):
        """
        更新密码
        """
        # 调用django 用户模型类的设置密码方法
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

class UserDetailSerializer(serializers.ModelSerializer):
    """用户个人信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        """
        重写更新方法，添加发送邮件
        instance == User
        """
        email = validated_data['email']
        instance.email = email
        instance.save()

        # 生成激活链接
        verify_url = instance.generate_smail_vereify_url()
        # 发送验证邮件
        send_verify_email.delay(email, verify_url)

        return instance

class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def create(self, validated_data):
        """
        保存
        """
        # Address模型类中有user属性，将user对象添加到模型类的创建参数中
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """

    class Meta:
        model = Address
        fields = ('title',)


class AddUserHistorySerializer(serializers.Serializer):
    """用户浏览记录序列化器"""
    sku_id = serializers.IntegerField(min_value=1)

    def validate_sku_id(self, value):
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("sku id 不存在")
        return value

    def create(self, validated_data):
        """保存"""
        # user_id
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        # 保存记录到redis中
        redis_conn = get_redis_connection('history')

        # 创建redis管道
        pl = redis_conn.pipeline()

        # 清除sku_id在redis中的记录，防止存储的数据是[1,1,1,1,1]
        # lrem(name, count, value)
        pl.lrem('history_%s' % user_id, 0, sku_id)

        # 向redis追加数据
        # lpush  [1,2,3,4] 5   -> [5,1,2,3,4]
        pl.lpush('history_%s' % user_id, sku_id)

        # 如果超过数量，截断
        # ltrim(name, start, end)
        pl.ltrim('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)

        pl.execute()

        return validated_data



