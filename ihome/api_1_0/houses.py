# coding=utf-8
# 此文件定义和房屋相关api接口
import json

from datetime import datetime
from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session

from ihome import constants, redis_store
from ihome import db
from ihome.models import Area, House, Facility, HouseImage, Order
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage_image
from ihome.utils.response_code import RET
from . import api


@api.route("/user/houses")
@login_required
def get_user_houses():
    """
    获取用户发布的房屋信息:
    1. 根据登录用户的id获取用户的所有房屋信息
    2. 组织数据，返回应答
    """
    user_id = g.user_id
    # 1. 根据登录用户的id获取用户的所有房屋信息
    try:
        houses = House.query.filter(House.user_id == user_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询房屋信息失败")

    # 2. 组织数据，返回应答
    house_dict_li = []
    for house in houses:
        house_dict_li.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data=house_dict_li)


@api.route("/houses")
def get_house_list():
    """
    搜索房屋的信息:
    """
    aid = request.args.get("aid")  # 城区id
    # new: 最新上线 booking: 入住最多 price-inc: 价格低->高 price-des:价格高->低
    sort_key = request.args.get("sk", "new")  # 排序方式，默认按照最新上线进行排序
    page = request.args.get("p", 1)  # 页码
    sd = request.args.get("sd")  # 搜索起始时间
    ed = request.args.get("ed")  # 搜索结束时间
    start_date = None
    end_date = None

    print request.args

    try:
        if aid:
            aid = int(aid)

        page = int(page)

        # 处理搜索时间
        if sd:
            start_date = datetime.strptime(sd, "%Y-%m-%d")

        if ed:
            end_date = datetime.strptime(ed, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date < end_date, Exception("搜索起始时间大于结束时间")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 尝试从缓存中获取搜索结果
    try:
        key = "%s:%s:%s:%s" % (aid, sd, ed, sort_key)
        res_str = redis_store.hget(key, page)
        if res_str:
            return jsonify(errno=RET.OK, errmsg="OK", data=json.loads(res_str))
    except Exception as e:
        current_app.logger.error(e)

    # 获取所有房屋的信息
    try:
        houses_query = House.query

        # 根据城区id对房屋信息进行过滤
        if aid:
            houses_query = houses_query.filter(House.area_id == aid)  # BaseQuery

        try:
            # 排除和搜索时间冲突房屋信息
            conflict_orders_li = []
            if start_date and end_date:
                conflict_orders_li = Order.query.filter(end_date > Order.begin_date, start_date < Order.end_date).all()
            elif start_date:
                conflict_orders_li = Order.query.filter(start_date < Order.end_date).all()
            elif end_date:
                conflict_orders_li = Order.query.filter(end_date > Order.begin_date).all()

            if conflict_orders_li:
                # 获取和搜索时间冲突房屋id列表
                conflict_houses_id = [order.house_id for order in conflict_orders_li]

                # 排除冲突房屋信息
                houses_query = houses_query.filter(House.id.notin_(conflict_houses_id))
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="排除冲突房屋信息失败")

        # 对查询结果进行排序
        if sort_key == "booking":
            # 按照房屋订单数量排序
            houses_query = houses_query.order_by(House.order_count.desc())
        elif sort_key == "price-inc":
            # 价格低->高
            houses_query = houses_query.order_by(House.price)
        elif sort_key == "price-des":
            # 价格高->低
            houses_query = houses_query.order_by(House.price.desc())
        else:
            # 按照最新上线进行排序
            houses_query = houses_query.order_by(House.create_time.desc())

        # 进行分页操作
        paginate = houses_query.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)

        # 获取搜索结果
        # houses = houses_query.all()
        houses = paginate.items
        total_page = paginate.pages  # 分页之后总页数
        current_page = paginate.page  # 当前页页码

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")

    # 组织数据，返回应答
    house_dict_li = []
    for house in houses:
        house_dict_li.append(house.to_basic_dict())

    resp = {
        "houses": house_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    # 在redis中缓存搜索结果
    try:
        key = "%s:%s:%s:%s" % (aid, sd, ed, sort_key)
        # 创建一个redis管道对象
        pipeline = redis_store.pipeline()

        # 开启redis事务
        pipeline.multi()

        # 向管道中添加命令
        pipeline.hset(key, page, json.dumps(resp))
        pipeline.expire(key, constants.HOUSE_LIST_REDIS_EXPIRES)

        # 执行事务
        pipeline.execute()
    except Exception as e:
        current_app.logger.error(e)

    # return jsonify(errno=RET.OK, errmsg="OK", data={"houses": house_dict_li})
    return jsonify(errno=RET.OK, errmsg="OK", data=resp)


@api.route('/house/index')
def get_house_index():
    """
    获取首页展示房屋的信息:
    1. 获取房屋的信息，按照房屋发布时间进行排序，默认展示前5个
    2. 组织数据，返回应答
    """
    # 1. 获取房屋的信息，按照房屋发布时间进行排序，默认展示前5个
    try:
        houses = House.query.order_by(House.create_time.desc()).\
            limit(constants.HOME_PAGE_MAX_HOUSES).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取首页房屋信息失败")

    # 2. 组织数据，返回应答
    house_dict_li = []
    for house in houses:
        house_dict_li.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data=house_dict_li)


@api.route("/house/<int:house_id>")
def get_house_detail(house_id):
    """
    获取房屋的详情信息:
    1. 根据房屋id查询房屋的信息
    2. 组织数据，返回应答
    """
    # 1. 根据房屋id查询房屋的信息
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 2. 组织数据，返回应答
    # 尝试从session获取user_id,
    # 如果用户登录，获取的登录用户的id，如果用户未登录，返回-1
    user_id = session.get("user_id", -1)

    return jsonify(errno=RET.OK, errmsg="OK", data={"house": house.to_full_dict(), "user_id": user_id})


@api.route("/house/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存上传房屋图片:
    1. 接收房屋id和房屋图片文件对象
    2. 根据房屋id获取房屋的信息(如果获取不到，说明房屋不存在)
    3. 将房屋的图片上传到七牛云
    4. 创建HouseImage对象并保存房屋图片记录
    5. 返回应答，上传成功
    """
    # 1. 接收房屋id和房屋图片文件对象
    house_id = request.form.get("house_id")
    file = request.files.get("house_image")

    if not all([house_id, file]):
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    # 2. 根据房屋id获取房屋的信息(如果获取不到，说明房屋不存在)
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 3. 将房屋的图片上传到七牛云
    try:
        key = storage_image(file.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="上传房屋图片失败")

    # 4. 创建HouseImage对象并保存房屋图片记录
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = key

    # 判断房屋是否设置了默认图片
    if not house.index_image_url:
        house.index_image_url = key

    try:
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存房屋图片记录失败")

    # 5. 返回应答，上传成功
    img_url = constants.QINIU_DOMIN_PREFIX + key
    return jsonify(errno=RET.OK, errmsg="上传房屋图片成功", data={"img_url": img_url})


@api.route("/houses", methods=["POST"])
@login_required
def save_house_info():
    """
    保存发布房屋的信息:
    1. 接收参数并进行参数校验
    2. 创建House对象并保存房屋的基本信息
    3. 将房屋的信息添加进数据库
    4. 返回应答，发布房屋信息成功
    """
    # 1. 接收参数并进行参数校验
    req_dict = request.json

    title = req_dict.get('title')
    price = req_dict.get('price')
    address = req_dict.get('address')
    area_id = req_dict.get('area_id')
    room_count = req_dict.get('room_count')
    acreage = req_dict.get('acreage')
    unit = req_dict.get('unit')
    capacity = req_dict.get('capacity')
    beds = req_dict.get('beds')
    deposit = req_dict.get('deposit')
    min_days = req_dict.get('min_days')
    max_days = req_dict.get('max_days')

    if not all([title, price, address, area_id, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    try:
        # 数据库中房屋单价和押金以 分 为单位保存
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 创建House对象并保存房屋的基本信息
    house = House()
    house.user_id = g.user_id
    house.area_id = area_id
    house.title = title
    house.price = price
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    # 获取房屋的设施信息
    facility = req_dict.get("facility") # [1, 3, 4]
    if facility:
        # 获取房屋的设施的信息
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取房屋设施失败")
        # 设置房屋设施信息
        house.facilities = facilities

    # 3. 将房屋的信息添加进数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存房屋信息失败")

    # 4. 返回应答，发布房屋信息成功
    return jsonify(errno=RET.OK, errmsg="发布房屋信息成功", data={"house_id": house.id})


@api.route("/areas")
def get_areas_info():
    """
    获取所有城区信息:
    1. 获取所有城区信息
    2. 组织数据，返回应答
    """
    try:
        # 先尝试从redis缓存中获取缓存的城区信息
        areas_str = redis_store.get("areas")
        # 如果获取到，直接返回
        if areas_str:
            return jsonify(errno=RET.OK, errmsg="OK", data=json.loads(areas_str))
    except Exception as e:
        current_app.logger.error(e)

    # 如果获取不到，查询数据库
    # 1. 获取所有城区信息
    try:
        areas = Area.query.all() # list
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取城区信息失败")

    # 2. 组织数据，返回应答
    areas_dict_li = []
    for area in areas:
        areas_dict_li.append(area.to_dict())

    # 在redis中缓存城区的信息
    try:
        redis_store.set("areas", json.dumps(areas_dict_li), constants.AREA_INFO_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK", data=areas_dict_li)