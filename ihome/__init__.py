# coding=utf-8
import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import Config, config_dict
from ihome.utils.commons import RegexConvter

# 创建数据库对象
db = SQLAlchemy()

redis_store = None

def set_logging(log_level):
    # 设置日志的记录等级
    logging.basicConfig(level=log_level)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)

# 工厂方法
def create_app(config_name):

    # 创建Flask应用程序实例
    app = Flask(__name__)
    # 获取配置类
    config_cls = config_dict[config_name]
    # 日志存储设置
    set_logging(config_cls.LOG_LEVEL)
    # 通过配置类加载配置
    app.config.from_object(config_cls)
    # db对象进行app关联
    db.init_app(app)
    # 创建redis存储对象
    global redis_store
    redis_store = redis.StrictRedis(host=config_cls.REDIS_HOST, port=config_cls.REDIS_PORT)
    # session信息存储
    Session(app)
    # 开启CSRF保护
    # 只做保护校验: 至于生成csrf_token cookie 还有 请求时携带csrf_token 需要自己来完成
    CSRFProtect(app)

    # 添加路由转换器
    app.url_map.converters["re"] = RegexConvter

    # 3.注册蓝图对象
    from ihome.api_1_0 import api
    app.register_blueprint(api, url_prefix="/api/v1.0")
    from ihome.web_html import html
    app.register_blueprint(html)

    return app