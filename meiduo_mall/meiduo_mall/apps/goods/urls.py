from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/hotskus/$', views.HotSKUListView.as_view()),
    # 商品列表数据接口
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view())
]

