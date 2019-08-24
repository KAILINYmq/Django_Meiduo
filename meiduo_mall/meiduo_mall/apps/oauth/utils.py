from  django.conf import settings
from urllib.parse import urlencode

class OAuthQQ(object):
    """
    用户QQ登录的工具类
    提供了QQ登录可能使用的方法
    """
    def __init__(self, app_id=None, app_key=None, redirect_url=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_url = redirect_url or settings.QQ_REDIRECT_URL
        self.state = state or settings.QQ_STATE

    def generate_qq_login_url(self):
        """
        拼接用户的QQ登录的链接地址
        :return: 链接地址
        """
        url = 'https://graph.qq.com/oauth2.0/authorize'
        data ={
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_url,
            'state': self.state,
            'scope': 'get_user_info'  # 获取用户的QQ的openid
        }
        query_string = urlencode(data) # response_type=code&client_id=xxxx&redirect_uri=xxxx&....
        url += query_string
        print(url)

        return url