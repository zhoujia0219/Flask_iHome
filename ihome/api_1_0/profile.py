# coding=utf-8
# 此文件定义和用户个人信息相关api接口
from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session

from ihome import constants
from ihome import db
from ihome.models import User
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage_image
from ihome.utils.response_code import RET
from . import api


# 实名认证过程:
# 1. 人工进行审核
# 2. 调用第三方接口验证真实姓名和身份证是否一致
# 3. 真实姓名，身份证号，银行卡号
# 4. 真实姓名，身份证号，银行卡号，银行预留手机号


@api.route("/user/auth")
@login_required
def get_user_auth():
    """
    获取用户的实名认证信息:
    1. 获取登录用户的id
    2. 根据登录用户id获取用户的信息
    3. 组织数据，返回应答
    """
    # 1. 获取登录用户的id
    user_id = g.user_id

    # 2. 根据登录用户id获取用户的信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    # 3. 组织数据，返回应答
    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


@api.route("/user/auth", methods=["POST"])
@login_required
def set_user_auth():
    """
    用户进行实名认证:
    1. 接收参数(真实姓名，身份证号)并进行参数校验
    2. todo: 调用第三方接口验证真实姓名和身份证是否一致
    3. 设置用户实名认证信息
    4. 返回应答，实名认证成功
    """
    # 1. 接收参数(真实姓名，身份证号)并进行参数校验
    req_dict = request.json
    real_name = req_dict.get("real_name")
    id_card = req_dict.get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 2. todo: 调用第三方接口验证真实姓名和身份证是否一致
    # 3. 设置用户实名认证信息
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    if user.real_name and user.id_card:
        # 已实名认证
        return jsonify(errno=RET.DATAEXIST, errmsg="已进行实名认证")

    user.real_name = real_name
    user.id_card = id_card

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存实名认证信息失败")

    # 4. 返回应答，实名认证成功
    return jsonify(errno=RET.OK, errmsg="实名认证成功")


@api.route("/user/name", methods=["PUT"])
@login_required
def set_user_name():
    """
    设置用户的用户名:
    0. todo: 判断用户是否登录
    1. 接收参数(用户名)并进行校验
    2. 判断用户名是否重复
    3. 设置用户的用户名
    4. 返回应答，设置用户名成功
    """
    # 1. 接收参数(用户名)并进行校验
    req_dict = request.json
    username = req_dict.get("username")

    if not username:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    # 2. 判断用户名是否重复
    try:
        user = User.query.filter(User.name == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="用户名已存在")

    # 3. 设置用户的用户名
    # user_id = session.get("user_id")
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    user.name = username
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="设置用户名失败")

    # 4. 返回应答，设置用户名成功
    return jsonify(errno=RET.OK, errmsg="设置用户名成功")


@api.route("/user/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像信息:
    0. todo: 判断用户是否登录
    # 1. 获取用户上传头像文件对象
    # 2. 把头像文件上传到七牛云
    # 3. 设置用户的头像记录
    # 4. 返回应答，上传头像成功
    """
    # 1. 获取用户上传头像文件对象
    file = request.files.get("avatar")

    if not file:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少数据")

    # 2. 把头像文件上传到七牛云
    try:
        key = storage_image(file.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传用户头像失败")

    # 3. 设置用户的头像记录
    # user_id = session.get("user_id")
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    # 设置用户头像地址
    user.avatar_url = key

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="设置用户头像记录失败")

    # 4. 返回应答，上传头像成功
    avatar_url = constants.QINIU_DOMIN_PREFIX + key

    return jsonify(errno=RET.OK, errmsg="上传头像成功", data={"avatar_url": avatar_url})


@api.route("/user")
@login_required
def get_user_info():
    """
    获取用户个人信息:
    0. todo: 判断用户是否登录
    1. 获取登录用户的id
    2. 根据id查询用户的信息(如果查不到，说明用户不存在)
    3. 组织数据，返回应答
    """
    # 1. 获取登录用户的id
    # user_id = session.get("user_id")
    user_id = g.user_id

    # 2. 根据id查询用户的信息(如果查不到，说明用户不存在)
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息失败")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    # 3. 组织数据，返回应答
    # resp = {
    #     "user_id": user.id,
    #     "username": user.name,
    #     "avatar_url": constants.QINIU_DOMIN_PREFIX + user.avatar_url if user.avatar_url else '',
    # }

    # constants.QINIU_DOMIN_PREFIX + user.avatar_url if user.avatar_url else ''
    # if user.avatar_url:
    #     constants.QINIU_DOMIN_PREFIX + user.avatar_url
    # else:
    #     ''

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())














