# coding=utf-8
# import sys
import json
import logging

import time

import os
from django.views.decorators.csrf import csrf_exempt
import jpype
from xiaom3.NLPResult import resChange, ResultMsg, DataNLP, Type1, Type2
from xiaom3.public import make_dic_response, make_normal_response
import main_NLP

logger = logging.getLogger("WeChat QA")
logger.setLevel(logging.DEBUG)
logNameByDay = "log/" + time.strftime('%Y-%m-%d', time.localtime(time.time())) + ".log"
if not os.path.exists("log/"):
    os.mkdir("log/")
# 创建一个handler，用于写入日志文件
fh = logging.FileHandler(logNameByDay, mode='a', encoding='utf8')
fh.setLevel(logging.DEBUG)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 定义日志输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 将logger添加到handle里面
logger.addHandler(fh)
logger.addHandler(ch)

@csrf_exempt
def post_nlp(request):
    # django调用jpype时需要先调用下面语句
    jpype.attachThreadToJVM()
    if request.method == 'POST':
        json_data = request.body
        # print(json_data)
        # print(json_data == "\n")
        if json_data is None or json_data == "" or json_data == "\n":
            res_dic = {"msgCode": 30005, "message": u"ValueError：Body 内没有值"}
            logger.info("请求body中没有值")
            return make_dic_response(res_dic, status='405')
        data_dic = json.loads(json_data, encoding='utf-8')
        # print(data_dic)
        question = data_dic.get("question", "")
        customerId = data_dic.get("customerId", "")
        node_id = data_dic.get("id", 0)
        label = data_dic.get("label", {})
        flag = data_dic.get("flag", 0)
        logger.info("业务引擎的请求内容:" + str(data_dic))
        result = None
        # print(resChange(node_id, flag=flag, label=label))
        # return make_normal_response(resChange(node_id, flag=flag, label=label))
        # print(type(question), " ", type(node_id), " ", type(label), " ", type(flag))
        try:
            answer_nlp = main_NLP.maintf(question, customerId, node_id, flag, label)
            # print(answer_nlp)
            logger.info("NLP返回结果：" + str(answer_nlp))
            result = nlp_coop_with_res(answer_nlp)
            logger.info("返回给业务引擎结果：" + result)
            return make_normal_response(result)
        except NotImplementedError as e:
            result = errorReturn(e)
            logger.info(result)
            return make_normal_response(result)

            # rec = recommand()
            # logNameByDay = sys.path[0] + "/log/" + time.strftime('%Y-%m-%d', time.localtime(time.time())) + ".log"
            # answer = rec.Rec(ques=question, log_files=logNameByDay, flag=id)
            # print("after", answer['flag'])

            # return HttpResponse(json.dumps(answer))
            # return make_normal_response(content, status='200')
    else:
        res_dic = {"msgCode": 405, "message": u"请使用post请求"}
        return make_dic_response(res_dic, status='405')


@csrf_exempt
def fenci_api(request):
    """

    :param request:
    :return:
    """
    if request.method == 'POST':
        json_data = request.body
        if json_data is None or json_data == "" or json_data == "\n":
            res_dic = {"msgCode": 30005, "message": u"ValueError：Body 内没有值"}
            logger.info("请求body中没有值")
            return make_dic_response(res_dic)
        data_dic = json.loads(json_data, encoding='utf-8')
        logger.info(str(data_dic))
        question = data_dic["question"]
        time_start = time.time()  # time.time()为1970.1.1到当前时间的毫秒数
        fenci, pair = main_NLP.seg_pair(question)
        logger.info("分词消耗时间为：" + str(time.time() - time_start))
        res = {"fenci": fenci, "pair": pair}
        logger.info(str(res))
        return make_dic_response(res)


    else:
        res_dic = {"msgCode": 405, "message": u"请使用post请求"}
        return make_dic_response(res_dic, status='405')



def nlp_coop_with_res(answer):
    """
    NLP回答封装成ResultMsg对象
    :param answer: NLP回答内容
    :return: 返回Json字符串
    """
    result = ResultMsg()
    dataNLPResult = DataNLP()
    result.msgCode = 1
    # print(answer.get("flag", ""))
    # 设置NLP判断结果，是否该用户被推荐接管
    dataNLPResult.flag = answer.get("flag", "")
    dataNLPResult.pair = answer.get("SO_pair", [])
    # NLP返回情况进行适配，不然转换成json，然后json转换java对象会出现问题
    if "ID" in answer:
        dataNLPResult.type = 1
        type1 = Type1()
        typeId = answer.get("ID", None)
        if isinstance(typeId, list):
            if len(typeId) == 0 or isinstance(typeId[0], list):
                type1.id = typeId
            else:
                # 转换成[[]]嵌套列表
                type1.id = [typeId]
        else:
            type1.id = [[typeId]]
        typeLabel = answer.get("label", None)
        if isinstance(typeLabel, dict):
            type1.label = typeLabel
        else:
            type1.label = None
        dataNLPResult.type1 = type1
    else:
        # 问答回答
        dataNLPResult.type = 2
        type2 = Type2()
        if isinstance(answer.get("answer_value", []), list):
            type2.answerList = answer.get("answer_value", [])
        else:
            type2.answerList = [answer.get("answer_value", [])]
        if isinstance(answer.get("recommend_question", []), list):
            type2.recQuesList = answer.get("recommend_question", [])
        else:
            type2.recQuesList = [answer.get("recommend_question", [])]
        if isinstance(answer.get("recommend_answer", []), list):
            type2.recAnsList = answer.get("recommend_answer", [])
        else:
            type2.recAnsList = [answer.get("recommend_answer", [])]
        dataNLPResult.type2 = type2
    result.dataNLP = dataNLPResult
    return json.dumps(result, default=lambda o: o.__dict__)


def errorReturn(error):
    result = ResultMsg()
    # dataNLP = DataNLP()
    result.msgCode = 0
    result.message = error
    logger.error(str(result.message))
    return json.dumps(result, default=lambda o: o.__dict__)


if __name__ == "__main__":
    tsad = "asdf"
    if tsad is []:
        print("dsaf")
    else:
        print("dsa")
        # res = ResultMsg()
        # dataNLP = DataNLP()
        # t1 = Type1()
        # t1.id = 12
        # t1.label = ["asd", "asd"]
        # dataNLP.type = 1
        # dataNLP.type1 = t1
        # res.dataNLP = dataNLP
        # # print(json.dumps(res.__dict__))
        # t = main_NLP.run_QA('储蓄卡', "asdfsadf")
        # print(t)
        # print(main_NLP.run_QA('储蓄卡', "asdfsadf"))
        # print(main_NLP.run_QA('信用卡', "asdfsadf"))
        # print(main_NLP.run_QA('挂失是', "asdfsadf"))
        # print(main_NLP.run_QA('你是', "asdfsadf"))
