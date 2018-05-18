#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#���ʺ�
accountSid= '8aaf0708635e4ce001636c3cebb80966';

#���ʺ�Token
accountToken= '833448df463f4b3d8a2676bd199924c7';

#Ӧ��Id
appId='8aaf0708635e4ce001636c3cec12096d';

#�����ַ����ʽ���£�����Ҫдhttp://
serverIP='app.cloopen.com';

#����˿� 
serverPort='8883';

#REST�汾��
softVersion='2013-12-26';

class CCP(object):
    # cls._instance
    def __new__(cls, *args, **kwargs):
        # �ж�cls�Ƿ�ӵ������_instance, ��������������������Ψһ����(��������
        if not hasattr(cls, "_instance"):
            # ����һ����������
            obj = super(CCP, cls).__new__(cls, *args, **kwargs)
            # ��ʼ��REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls._instance = obj

            # ֱ�ӷ���
        return cls._instance

    # def __init__(self):
    #     # ��ʼ��REST SDK
    #     self.rest = REST(serverIP, serverPort, softVersion)
    #     self.rest.setAccount(accountSid, accountToken)
    #     self.rest.setAppId(appId)

      # ����ģ�����
      # @param to �ֻ�����
      # @param datas �������� ��ʽΪ���� ���磺{'12','34'}���粻���滻���� ''
      # @param $tempId ģ��Id

    def send_template_sms(self, to, datas, tempId):

        result = self.rest.sendTemplateSMS(to,datas,tempId)
        # print result
        if result.get("statusCode") == "000000":
            # ���ͳɹ�
            return 1
        else:
            # ����ʧ��
            return 0
   
#sendTemplateSMS(�ֻ�����,��������,ģ��Id)
if __name__ == "__main__":
    # sendTemplateSMS("18665939705", ["123456", 5], 1)
    # CCP().send_template_sms("18665939705", ["123456", 5], 1)
    obj1 = CCP()
    obj2 = CCP()
    obj3 = CCP()

    print id(obj1)
    print id(obj2)
    print id(obj3)