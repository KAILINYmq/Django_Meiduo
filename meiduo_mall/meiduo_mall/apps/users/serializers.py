from rest_framework import serializers
import re
from django_redis import get_redis_connection
from . models import User

class CreateUserSerializer(serializers.ModelSerializer):
    """注册序列化器"""
    password2 = serializers.CharField(label='密码2', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='JWT token登录状态', read_only=True)
    """
    序列化器中需要的所有字段: 'id', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow'
    模型中已有字段: id', 'username', 'mobile', 'password'
    需要进行序列化的字段: 'token', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow'
    需要进行反序列化的字段:  'id', 'username', 'mobile'
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'password', 'password2', 'sms_code', 'allow', 'token']
        extra_kwargs = {  # 对序列化器中的字段进行额外配置
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
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

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
        """重写序列化器的保存方法把多余数据移除"""
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        password = validated_data.pop('password')  # 把字典中的password移除

        user = User(**validated_data)
        user.set_password(password)  # 对密码进行加密后再赋值给user模型对象的password属性
        user.save()
        # return User.objects.create(**validated_data)


        # 手动生成JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token的函数
        payload = jwt_payload_handler(user)  # 通过传入user对象生成jwt 载荷部分
        token = jwt_encode_handler(payload)  # 传入payload 生成token
        # 给user 模型对象多增加一个token属性,再给序列化器多增加token字段只做序列化
        user.token = token

        return user