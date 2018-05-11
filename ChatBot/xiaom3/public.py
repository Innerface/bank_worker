# coding:utf-8
import json
from django.http import HttpResponse


def make_json_returns(content, question="", return_type=-100, status="201", end=False):
    if not return_type == -100:
        return_json = {'text': content, 'question': question, 'type': return_type, 'end': end}
    else:
        return_json = {'text': content, 'question': question, 'end': end}
    return HttpResponse(json.dumps(return_json), content_type='application/json', status=status)


def make_normal_response(content, status='201'):
    """
    :param content: json字符串
    :param status: 状态码
    :return:
    """
    return HttpResponse(content, content_type='application/json', status=status)


def make_dic_response(content, status='201'):
    """
    字典类型直接转换为json并返回为HttpResponse
    :param content:
    :param status:
    :return:
    """
    return HttpResponse(json.dumps(content), content_type='application/json', status=status)
