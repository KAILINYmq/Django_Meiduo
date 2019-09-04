from django.conf.urls import url
from . import views

urlpatterns = [
    # 用户订单模块
    url(r'orders/settlement/$', views.OrderSettlementView.as_view()),
    # 保存订单模块
    url(r'orders/$', views.SaveOrderView.as_view()),
]