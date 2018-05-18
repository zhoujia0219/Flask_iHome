# coding=utf-8
import logging

import redis

# 创建配置类
class Config(object):
    DEBUG = True

    # 设置SECRET_KEY
    SECRET_KEY='AsirL8oeqAv3Gzve+VJIapPXS4i5tfr6NFJ34k525UzKV+K3L0nkGFqZyFjcPuAt'
    # 数据库配置信息
    # 设置连接路径，库名
    SQLALCHEMY_DATABASE_URI="mysql://root:mysql@127.0.0.1:3306/ihome"
    # 关闭追踪数据变更
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST="127.0.0.1"
    REDIS_PORT=6379

    # session存储配置
    # session存到redis中
    SESSION_TYPE = 'redis'
    # session存储到哪个数据库中
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 设置session过期时间
    PERMANENT_SESSION_LIFETIME = 86400

class DevelopmentConfig(Config):
    """开发环境中配置类"""
    DEBUG = True

    # 开发阶段日志等级
    LOG_LEVEL = logging.DEBUG

class ProductionConfig(Config):
    """生产环境中的配置类"""
    # 设置数据库的链接地址
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@172.16.179.139:3306/ihome"

    # 生产阶段日志等级
    LOG_LEVEL = logging.WARN


class TestingConfig(Config):
    """测试环境中的配置类"""
    # 设置数据库的链接地址
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@172.16.179.139:3306/ihome_testcase"
    # 开启测试标志
    TESTING = True

config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}