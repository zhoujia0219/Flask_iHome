# coding=utf-8
import redis
from flask import Flask

# 创建Flask应用程序实例
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 创建配置类
class Config(object):
    DEBUG = True

    # 数据库配置信息
    # 设置连接路径，库名
    SQLALCHEMY_DATABASE_URI="mysql://root:mysql@127.0.0.1:3306/ihome"
    # 关闭追踪数据变更
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST="127.0.0.1"
    REDIS_PORT=6379

# 通过配置类加载配置
app.config.from_object(Config)
# 创建数据库对象
db= SQLAlchemy(app)
# 创建redis存储对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

@app.route('/')
def index():
    # 测试redis
    redis_store.set("name", "zj")
    return 'index'

if __name__ == '__main__':
    # 运行开发web服务器
    app.run(debug=True)