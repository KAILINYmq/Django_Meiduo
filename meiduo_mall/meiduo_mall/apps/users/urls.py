from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    # 注册
    url(r'^users/$', views.UserView.as_view()),
    # 判断用户名是否存在
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否存在
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 登陆, 获取JWT token
    url(r'^authorizations/$', obtain_jwt_token),
    # 找回密码, 发送短信验证码的token
    url(r'^accounts/(?P<account>\w{4,20}/sms/token/$)', views.SMSCodeTokenView.as_view()),
    # 找回密码, 获取修改密码的token
    url(r'^accounts/(?P<account>\w{4,20}/password/token/$)', views.PasswordTokenView.as_view()),
    # 找回密码， 设置密码
    url(r'^accounts/(?P<pk>/password/$)', views.PasswordView.as_view()),
]
