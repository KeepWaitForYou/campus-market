"""config 应用包：Django 项目配置 + Celery 入口。"""
import pymysql

pymysql.install_as_MySQLdb()

from .celery import app as celery_app

__all__ = ("celery_app",)