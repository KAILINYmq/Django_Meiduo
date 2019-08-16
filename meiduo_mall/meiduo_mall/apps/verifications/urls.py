from django.conf.urls import url

from . import views

# 定义路由
urlpatterns = [
    # 图片你验证码
    # url(r'image_codes/(?P<image_code_id>.+)/$', views.ImageCodeView.as_view()),

    # 发送短信验证码
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
]