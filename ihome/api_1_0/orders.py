# coding=utf-8
# 此文件中定义和订单相关api接口
from datetime import datetime

from flask import current_app
from flask import g
from flask import request, jsonify

from ihome import db
from ihome.models import House, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api


@api.route("/order/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息:
    1. 获取订单评论信息
    2. 根据订单id查询订单信息(如果查不到，代表订单不存在)
    3. 设置订单的评论信息
    4. 更新数据表中的数据
    5. 返回应答
    """
    # 1. 获取订单评论信息
    req_dict = request.json
    comment = req_dict.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    # 2. 根据订单id查询订单信息(如果查不到，代表订单不存在)
    try:
        order = Order.query.filter(Order.id == order_id,
                                   Order.status == "WAIT_COMMENT",
                                   Order.user_id == g.user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    if not order:
        return jsonify(errno=RET.NODATA, errmsg="订单不存在")

    # 3. 设置订单的评论信息
    order.comment = comment
    order.status = "COMPLETE"

    # 4. 更新数据表中的数据
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存订单评论信息失败")

    # 5. 返回应答
    return jsonify(errno=RET.OK, errmsg="OK")

# /order/<int:order_id>/status?action=accept|reject
@api.route("/order/<int:order_id>/status", methods=["PUT"])
@login_required
def update_order_status(order_id):
    """
    接单或者拒单操作:
    1. 获取参数action，如果action==accept,接单 如果action==reject,拒单
    2. 根据订单id查询订单信息(如果查不到，代表订单不存在)
    3. 根据action来修改订单的状态
    4. 更新数据表中的数据
    5. 返回应答
    """
    # 1. 获取参数action，如果action==accept,接单 如果action==reject,拒单
    action = request.args.get("action")
    if not action:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 根据订单id查询订单信息(如果查不到，代表订单不存在)
    try:
        order = Order.query.filter(Order.id == order_id,
                                   Order.status == "WAIT_ACCEPT").first()

        # 判断登录用户是否是订单中对应房屋的房东
        user_id = g.user_id
        if order.house.user_id != user_id:
            return jsonify(errno=RET.DATAERR, errmsg="不是房屋的房东")

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    # 3. 根据action来修改订单的状态
    if action == "accept":
        # 接单
        order.status = "WAIT_COMMENT"  # 待评价
    else:
        # 拒单
        order.status = "REJECTED"
        # 接收拒单原因
        req_dict = request.json
        reason = req_dict.get("reason")

        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

        order.comment = reason

    # 4. 更新数据表中的数据
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="接单或者拒单失败")

    # 5. 返回应答
    return jsonify(errno=RET.OK, errmsg="OK")


# /orders?role=lodger|landlord
# 如果role == lodger，以房客身份查询自己预订别人房屋的订单信息
# 如果role == landlord，以房东的身份查询别人预订自己房屋的订单信息
@api.route("/orders")
@login_required
def get_order_list():
    """
    获取用户的订单信息:
    1. 获取用户的角色role
        1.1 如果role == lodger，以房客身份查询自己预订别人房屋的订单信息
        1.2 如果role == landlord，以房东的身份查询别人预订自己房屋的订单信息
    2. 组织数据，返回应答
    """
    # 1. 获取用户的角色role
    role = request.args.get("role")

    if not role:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    if role not in ("lodger", "landlord"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user_id = g.user_id

    try:
        if role == "lodger":
            # 1.1 如果role == lodger，以房客身份查询自己预订别人房屋的订单信息
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
        else:
            # 1.2 如果role == landlord，以房东的身份查询别人预订自己房屋的订单信息
            # 获取房东的所有的房屋信息
            houses = House.query.filter(House.user_id == user_id)#.all()
            # 获取房东所有房屋的id列表houses_id_li
            houses_id_li = [house.id for house in houses]
            # 查询订单对应的房屋的id在houses_id_li中的订单信息
            orders = Order.query.filter(Order.house_id.in_(houses_id_li)).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")

    # 2. 组织数据，返回应答
    order_dict_li = []
    for order in orders:
        order_dict_li.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data=order_dict_li)


# @api.route("/orders")
# @login_required
# def get_order_list():
#     """
#     获取用户的订单信息:
#     1. 根据登录用户的id查询用户的订单信息
#     2. 组织数据，返回应答
#     """
#     user_id = g.user_id
#     # 1. 根据登录用户的id查询用户的订单信息
#     try:
#         orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")
#
#     # 2. 组织数据，返回应答
#     order_dict_li = []
#     for order in orders:
#         order_dict_li.append(order.to_dict())
#
#     return jsonify(errno=RET.OK, errmsg="OK", data=order_dict_li)


@api.route("/orders", methods=["POST"])
@login_required
def save_order_info():
    """
    创建房屋预订订单:
    1. 接收参数(房屋id, 起始时间，结束时间)并进行参数验证
    2. 根据房屋id查询房屋的信息(如果查不到，说明房屋不存在)
    3. 创建Order对象并保存订单信息
    4. 将订单信息添加进数据库
    5. 返回应答，订单创建成功
    """
    # 1. 接收参数(房屋id, 起始时间，结束时间)并进行参数验证
    req_dict = request.json
    house_id = req_dict.get("house_id")
    start_date = req_dict.get("start_date")
    end_date = req_dict.get("end_date")

    if not all([house_id, start_date, end_date]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        assert start_date < end_date, Exception("搜索起始时间大于结束时间")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 根据房屋id查询房屋的信息(如果查不到，说明房屋不存在)
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询房屋信息失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 判断此房屋是否已经被预订
    try:
        conflict_count = Order.query.filter(end_date > Order.begin_date,
                                            start_date < Order.end_date,
                                            Order.house_id == house_id).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取冲突订单信息失败")

    if conflict_count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已预订")

    # 3. 创建Order对象并保存订单信息
    order = Order()
    days = (end_date - start_date).days # timedelta
    order.user_id = g.user_id
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = days * house.price

    # 房屋预订量+1
    house.order_count += 1

    # 4. 将订单信息添加进数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存订单信息失败")

    # 5. 返回应答，订单创建成功
    return jsonify(errno=RET.OK, errmsg="房屋预订成功")
