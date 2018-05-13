# coding=utf-8
import redis
from flask import Flask, session
from flask_migrate import Migrate, MigrateCommand, Config
from flask_script import Manager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from config import Config

# 创建Flask应用程序实例
app = Flask(__name__)

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