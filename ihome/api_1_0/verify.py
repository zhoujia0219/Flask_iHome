# coding=utf-8
# 此文件中api用于提供图片验证码和短信验证码
import random

import re

from . import api

from ihome import redis_store, constants
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET

from flask import make_response, request, jsonify, current_app


@api.route("/sms_code", methods=["POST"])
def send_sms_code():
    """
    发送短信验证码:
    1. 接收参数(手机号，图片验证码，图片验证码标识)并进行参数校验
    2. 从redis中获取图片验证码(如果取不到，说明图片验证码已过期)
    3. 对比图片验证码，如果一致
    4. 使用云通讯发送短信验证码
        4.1 生成一个6位随机验证码
        4.2 使用云通讯发送短信
        4.3 在redis中存储短信验证码内容
    5. 返回应答，发送短信成功
    """
    # 1. 接收参数(手机号，图片验证码，图片验证码标识)并进行参数校验
    # req_data = request.data
    # req_dict = json.loads(req_data)
    # req_dict = request.get_json()
    # print 1
    req_dict = request.json
    # print 123
    mobile = req_dict.get("mobile")
    image_code = req_dict.get("image_code")
    image_code_id = req_dict.get("image_code_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    if not re.match(r"^1[35789]\d{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 2. 从redis中获取图片验证码(如果取不到，说明图片验证码已过期)
    try:
        real_image_code = redis_store.get("imagecode:%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取图片验证失败")

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")

    # 3. 对比图片验证码，如果一致
    if real_image_code != image_code:
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 4. 使用云通讯发送短信验证码
    # 4.1 随机生成一个6位短信验证码
    sms_code = "%06s" % random.randint(0, 999999) # 101
    current_app.logger.info("短信验证码是:%s" % sms_code)

    # 4.2 使用云通讯
    # try:
    #     res = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES/60], 1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")
    #
    # if res != 1:
    #     # 发送短信验证码失败
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送短信验证码失败')

    # 4.3 在redis中保存短信验证码内容
    try:
        redis_store.set("smscode:%s" % mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码失败")

    # 5. 返回应答，发送短信成功
    return jsonify(errno=RET.OK, errmsg="发送短信验证码成功")

@api.route("/image_code")
def get_image_code():
    # print 1
    """
    产生图片验证码:
    1. 接收参数(图片验证码标识)并进行校验
    2. 生成图片验证码
    3. 在redis中保存图片验证码
    4. 返回验证码图片
    """
    # 1. 接收参数(图片验证码标识)并进行校验
    image_code_id = request.args.get("cur_id")
    # print 2
    if not image_code_id:
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")

    # 2. 生成图片验证码
    # 文件名称 验证码文本 验证码图片内容
    name, text, content = captcha.generate_captcha()
    current_app.logger.info("图片验证码是:%s" % text)
    # print 3
    # 3. 在redis中保存图片验证码
    # redis_store.set("key", "value", "expires")
    try:
        redis_store.set("imagecode:%s" % image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码失败")

    # print 3
    # 4. 返回验证码图片
    response = make_response(content)
    # 指定返回内容的类型
    response.headers["Content-Type"] = "image/jpg"
    # print 6
    return response
