"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    #  图片验证码
    # url(r'^', include('verifications.urls')),
    # 发送短信验证码
    url(r'^', include('verifications.urls')),
    # 用户登陆模块
    url(r'^', include('users.urls')),
    # QQ登陆
    url(r'oauth/', include('oauth.urls')),
    # 获取省市县三级
    url(r'', include('areas.urls')),
    # 富文本编辑器
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    # 商品详情页热销商品显示
    url(r'^', include('goods.urls')),
    # 购物车
    url(r'^', include('carts.urls')),
]
