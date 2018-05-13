# coding=utf-8
import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from config import Config, config_dict

# 创建数据库对象
db = SQLAlchemy()

def create_app(config_name):

    # 创建Flask应用程序实例
    app = Flask(__name__)
    # 获取配置类
    config_cls = config_dict[config_name]
    # 通过配置类加载配置
    app.config.from_object(config_cls)
    # db对象进行app关联
    db.init_app(app)
    # 创建redis存储对象
    redis_store = redis.StrictRedis(host=config_cls.REDIS_HOST, port=config_cls.REDIS_PORT)
    # session信息存储
    Session(app)
    # 开启CSRF保护
    # 只做保护校验: 至于生成csrf_token cookie 还有 请求时携带csrf_token 需要自己来完成
    csrf = CSRFProtect(app)

    return app