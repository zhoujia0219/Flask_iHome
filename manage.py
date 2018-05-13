# coding=utf-8
import redis
from flask import Flask, session
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect



# 创建Flask应用程序实例
app = Flask(__name__)

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


# 通过配置类加载配置
app.config.from_object(Config)
# 创建数据库对象
db= SQLAlchemy(app)
# 创建redis存储对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 创建Manager管理对象
manager = Manager(app)
# 使用迁移方式管理数据库
Migrate(app, db)
# 添加迁移命令
manager.add_command("db", MigrateCommand)

# session信息存储
Session(app)


# 开启CSRF保护
# 只做保护校验: 至于生成csrf_token cookie 还有 请求时携带csrf_token 需要自己来完成
csrf = CSRFProtect(app)

@app.route('/', methods=["GET", "POST"])
def index():
    # 测试redis
    # redis_store.set("name", "zj")
    # 测试session存储
    session['name']='zj'
    return 'index'

if __name__ == '__main__':
    # 运行开发web服务器
    # app.run(debug=True)
    manager.run()