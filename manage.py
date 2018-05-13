# coding=utf-8

from flask_migrate import Migrate, MigrateCommand, Config
from flask_script import Manager
from ihome import create_app #, db

app = create_app("development")
# # 创建Manager管理对象
# manager = Manager(app)
# # 使用迁移方式管理数据库
# Migrate(app, db)
# # 添加迁移命令
# manager.add_command("db", MigrateCommand)


@app.route('/', methods=["GET", "POST"])
def index():
    # 测试redis
    # redis_store.set("name", "zj")
    # 测试session存储
    # session['name']='zj'
    return 'index'

if __name__ == '__main__':
    # 运行开发web服务器
    app.run(debug=True)
    # manager.run()