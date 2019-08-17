# celery的启动程序包
from celery import Celery

celery_app = Celery('meiduo')

# 导入配置文件
celery_app.config_from_object('celery_tasks.config')

# 自动注册celery任务，系统会自动找到sms目录下的文件
celery_app.autodiscover_tasks(['celery_tasks.sms'])

# 开启celery命令
# celery -A 应用路径(.包路经) worker -l info
# celery -A celery_tasks.main worker -l info
# win10上运行celery4.x就会出现这个问题(ValueError: not enough values to unpack (expected 3, got 0))
# 需要安装pip install eventlet后用以下命令执行
# celery -A celery_tasks.main worker -l info -P eventlet