"""Celery 应用配置：负责异步通知、图片压缩、订单超时取消等。"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("campus_market")

# 从 Django settings 读取配置，命名空间 CELERY_ 前缀
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现各 app 的 tasks.py
app.autodiscover_tasks()

# Beat 定时任务：每 5 分钟兜底清扫超时未支付订单
# （正常路径由 order_timeout_cancel 延时任务负责，此处防止 worker 重启丢失任务）
app.conf.beat_schedule = {
    "sweep-expired-orders": {
        "task": "orders.sweep_expired_orders",
        "schedule": 300.0,
    },
}


@app.task(bind=True)
def debug_task(self) -> str:
    """健康检查任务。"""
    return f"Request: {self.request!r}"