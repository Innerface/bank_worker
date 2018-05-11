# coding=utf-8
import json


class ResultMsg(object):
    def __init__(self, **kwargs):
        """
        将nlp结果封装，
        :param kwargs: msgCode状态码代表nlp那边是否执行成功，
                        message错误信息，
                        flag表示是否推荐被接管，
                        dataNLP为返回主题
        """
        if kwargs:
            self.msgCode = kwargs["msgCode"]
            self.message = kwargs["message"]
            self.dataNLP = kwargs["dataNLP"]
        else:
            self.msgCode = 0
            self.message = None
            self.dataNLP = None

    def __repr__(self):
        return repr((self.msgCode, self.message, self.dataNLP))


class Type1(object):
    def __init__(self, **kwargs):
        if kwargs:
            self.id = kwargs['id']
            self.label = kwargs['label']
        else:
            self.id = 0
            self.label = None

    def __repr__(self):
        return repr((self.id, self.label))
        # return repr('{"id":'+str(self.id)+','+'"label":'+str(self.label))


class Type2(object):
    def __init__(self, **kwargs):
        if kwargs:
            self.answerList = kwargs["answerList"]
            self.recQuesList = kwargs["recQuesList"]
            self.recAnsList = kwargs["recAnsList"]
        else:
            self.answerList = None
            self.recQuesList = None
            self.recAnsList = None

    def __repr__(self):
        return repr((self.answerList, self.recQuesList, self.recAnsList))
        # return repr("self.answerList, self.recQuesList, self.recAnsList))


class DataNLP:
    def __init__(self, **kwargs):
        """
        type 返回类型，1代表type1，2代表type2
        flag 是否接管标识，2代表已接管，1代表推荐接管，0带表不接管
        type1 业务的返回参数
        type2 QA的返回参数
        :param kwargs:
        """
        if kwargs:
            self.flag = kwargs["flag"]
            self.type = kwargs["type"]
            self.type1 = kwargs["type1"]
            self.type2 = kwargs["type2"]
        else:
            self.flag = 0
            self.type = 1
            self.type1 = None
            self.type2 = None

    def __repr__(self):
        return repr((self.type, self.type1, self.type2))


def resChange(id, flag, ques, label):
    res = ResultMsg()
    d = DataNLP()
    t1 = Type1()
    t1.label = {}
    d.type = 1
    if id <= 0:
        t1.id = 21
    else:
        t1.id = id
    for i in label:
        t1.label[i] = "123456"
        print(i)
    d.flag = flag
    d.type1 = t1
    res.dataNLP = d
    res.msgCode = 1
    return object2json(res)


def object2json(obj):
    """
    将任意对象转换成json对象
    :param obj: 需要转的对象
    :return: 返回json字符串
    """
    return json.dumps(obj, default=lambda o: o.__dict__, encoding="utf-8")


def json2object(jsonStr):
    """
    将json字符串转换为ResultMsg对象
    :param jsonStr:
    :return:
    """
    # dic2ObjHook就是帮助json.loads转换为ResultMsg对象
    return json.loads(jsonStr, encoding="utf-8", object_hook=dic2ObjHook)


def dic2ObjHook(dic):
    """
    将字典dict转换为对象, 该方法主要用于转ResultMsg对象
    :param dic: 字典对象
    :return: 返回对象
    """
    if not isinstance(dic, dict):
        return dic
    if "id" in dic:
        return Type1(id=dic['id'], label=dic['label'])
    elif "answerList" in dic:
        return Type2(answerList=dic['answerList'], recAnsList=dic['recAnsList'],
                     recQuesList=dic['recQuesList'])
    elif "message" in dic:
        return ResultMsg(message=dic["message"], dataNLP=dic["dataNLP"],
                         msgCode=dic["msgCode"], flag=dic["flag"])
    return dic


if __name__ == "__main__":
    res = ResultMsg()
    dataNLP = DataNLP()
    t1 = Type1()
    t1.id = 12
    t1.label = ["asd", "asd"]
    dataNLP.type = 1
    dataNLP.type1 = t1
    res.dataNLP = dataNLP
    # print (classToDict(res))
    # t = object2dict(res.__dict__)
    s = json.dumps(res, default=lambda o: o.__dict__)
    print(json.dumps(res, default=lambda o: o.__dict__))
    # print(json.loads(s, encoding="utf-8", object_hook=dic2ObjHook, ))
    t = json.loads(s, encoding="utf-8", object_hook=dic2ObjHook, )
    print(type(t), t.__dict__)
    print("msgCode" in t.__dict__)
    falseTuple = (int(0), float(0.0), "", b"", False, None, tuple(), [], {})
    for item in falseTuple:
        if item:
            print("[{sth}] is True".format(sth=item))
    print("will exit.")

