# coding:utf-8
import sys
import jieba
import jieba.posseg as pseg
import MySQLdb
import os
import sys
import urllib2
import json
from questionlistall import questionlist
from gensim import corpora,models,similarities
import re
import time,datetime
import cPickle

reload(sys)
sys.setdefaultencoding("utf8")

class chaxun(object):
    def __init__(self):
        pass

    def get_week_day(self,date):
        week_day_dict = {
            7: ['星期一','周一','礼拜一'],
            8: ['星期二','周二','礼拜二'],
            9: ['星期三','周三','礼拜三'],
            10: ['星期四','周四','礼拜四'],
            11: ['星期五','周五','礼拜五'],
            12: ['星期六','周六','礼拜六'],
            13: ['星期天','周日','礼拜天','礼拜日','星期日'],
            0: ['上周一','上星期一','上礼拜一'],
            1: ['上周二','上星期二','上礼拜二'],
            2: ['上周三','上星期三','上礼拜三'],
            3:['上周四','上星期四','上礼拜四'],
            4:['上周五','上星期五','上礼拜五'],
            5:['上周六','上星期六','上礼拜六'],
            6:['上周日','上星期日','上礼拜日','上星期天'],
        }
        for key in week_day_dict:
            if date in week_day_dict[key]:
                time_now =datetime.datetime.now()
                today_week = time_now.weekday()
                diff_day = today_week+7-int(key)
                date_pass = time_now + datetime.timedelta(days=-diff_day)
                date_query = str(date_pass).split(' ')[0]
                break
        return date_query

    def query(self, ques, type_flag = 0):
        jieba.load_userdict(sys.path[0] + '\\dic_former.txt')
        jieba.load_userdict(sys.path[0] + '\\time_dic.txt')
        jieba.load_userdict(sys.path[0] + '\\type_dic.txt')
        fenci = jieba.cut(ques, cut_all=False)
        ##开始时间，结束时间，交易金额，交易类型，交易商户，交易单位，备注
        ##unit : 0代表几笔，1代表金额总和，2代表业务流水
        type_list = {}
        type_list['begin_time']=[]
        type_list['end_time'] = []
        type_list['amount'] = []
        type_list['type'] = []
        type_list['merchant'] = []
        type_list['unit'] = []
         ##时间 类型 地点 金额 商户
        ##我上周三用支付宝在华联超市买了200多块钱的东西，但是支付宝没有记录，能帮我查一下卡上有没有这笔交易

        ##时间插查找
        ##**年**月**日查找

        p = re.compile(u'((\d+年\d+月\d+(日|号)(至|到)\d+年\d+月\d+(日|号))|((今年\d+月\d+(号|日))(至|到)(今年\d+月\d+(号|日)))|((今年\d+月\d+(号|日))(至|到)(\d+月\d+(号|日)))|((\d+年\d+月\d+(号|日))(至|到)(\d+月\d+(号|日)))|(\d+年\d+月\d+(日|号))|(\d+月\d+(日|号))|(\d+(日|号))|(今年\d+月\d+(号|日)))')
        # p = re.compile(r'((\d+年\d+月\d+(日|号))|(\d+月\d+(日|号))|(\d+(日|号))|(今年\d+月\d+(号|日)))')
        ymd = []
        for m in p.finditer(ques):
            ymd.append(m.group())

        if len(ymd) != 0:
            for mk in range(len(ymd)):
                if u'到' in ymd[mk] or u'至' in ymd[mk]:
                    if u'到' in ymd[mk]:
                        ymd_list = ymd[mk].split('到')
                    if u'至' in ymd[mk]:
                        ymd_list = ymd[mk].split('至')
                    time_list = []
                    for item in ymd_list:
                        num = re.compile(u'\d+')
                        md = []
                        for mt in num.finditer(item):
                            md.append(mt.group())
                        if u'今年' in item:
                            time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                            year = time_now.split('-')[0]
                            tmp_time = '-'.join([year, md[0], md[1]])
                            time_list.append(tmp_time)
                        else:
                            if len(md) == 3:
                                tmp_time = '-'.join([md[0], md[1], md[2]])
                                time_list.append(tmp_time)
                            if len(md) == 2:
                                time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                                year = time_now.split('-')[0]
                                tmp_time = '-'.join([year, md[0], md[1]])
                                time_list.append(tmp_time)
                            if len(md) == 1:
                                time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                                year = time_now.split('-')[0]
                                month = time_now.split('-')[1]
                                tmp_time = '-'.join([year, month, md[0]])
                                time_list.append(tmp_time)
                    type_list['begin_time'].append(time_list[0])
                    type_list['end_time'].append(time_list[1])
                else:
                    num = re.compile(u'\d+')
                    md = []
                    for mt in num.finditer(ymd[mk]):
                        md.append(mt.group())
                    if u'今年' in ymd[mk]:
                        time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                        year = time_now.split('-')[0]
                        time_list = '-'.join([year, md[0], md[1]])
                        type_list['begin_time'].append(time_list)
                        type_list['end_time'].append(time_list)
                    else:
                        if len(md) == 3:
                            time_list = '-'.join([md[0], md[1], md[2]])
                            type_list['begin_time'].append(time_list)
                            type_list['end_time'].append(time_list)
                        if len(md) == 2:
                            time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                            year = time_now.split('-')[0]
                            time_list = '-'.join([year, md[0], md[1]])
                            type_list['begin_time'].append(time_list)
                            type_list['end_time'].append(time_list)
                        if len(md) == 1:
                            time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                            year = time_now.split('-')[0]
                            month = time_now.split('-')[1]
                            time_list = '-'.join([year, month, md[0]])
                            type_list['begin_time'].append(time_list)
                            type_list['end_time'].append(time_list)

        ###按周、星期查找##
        p = re.compile(u'(上周一|周一|上周二|周二|上周三|周三|上周四|周四|上周五|周五|上周六|周六|上周日|周日|上星期一|星期一|上星期二|星期二|上星期三|星期三 \
            |上星期四|星期四|上星期五|星期五|上星期六|星期六|上星期天|星期天|上星期日|星期日|上礼拜一|礼拜一|上礼拜二|礼拜二|上礼拜三|礼拜三|上礼拜四|礼拜四 \
            |上礼拜五|礼拜五|上礼拜六|礼拜六|上礼拜天|礼拜天|上礼拜日|礼拜日)')
        week_day = []
        for m in p.finditer(ques):
            week_day.append(m.group())

        for item_day in week_day:
            day_list=self.get_week_day(item_day)
            type_list['begin_time'].append(day_list)
            type_list['end_time'].append(day_list)

        p = re.compile(u'(目前|现在|刚刚|当前|今天)')
        day_today = []
        for ms in p.finditer(ques):
            day_today.append(ms.group())

        if len(day_today)!=0:
            time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            type_list['begin_time'].append(time_now)
            type_list['end_time'].append(time_now)

        if (u'昨天' in ques):
            time_now = datetime.datetime.now()
            time_yesterday = time_now + datetime.timedelta(days=-1)
            date_yesterday = str(time_yesterday).split(' ')[0]
            type_list['begin_time'].append(date_yesterday)
            type_list['end_time'].append(date_yesterday)

        if (u'前天' in ques):
            time_now = datetime.datetime.now()
            time_before = time_now + datetime.timedelta(days=-2)
            date_before = str(time_before).split(' ')[0]
            type_list['begin_time'].append(date_before)
            type_list['end_time'].append(date_before)

        if (u'大前天' in ques):
            time_now = datetime.datetime.now()
            time_before_yes = time_now + datetime.timedelta(days=-3)
            date_before_yes = str(time_before_yes).split(' ')[0]
            type_list['begin_time'].append(date_before_yes)
            type_list['end_time'].append(date_before_yes)

        ###查找金额#####
        p = re.compile(u'(\d+(多块钱|块钱|元钱|块|元))')
        amount = []
        for m in p.finditer(ques):
            amount.append(m.group())

        for item_amount in amount:
            p = re.compile(u'\d+')
            # amount_num = []
            for kt in p.finditer(item_amount):
                # amount_num.append(kt.group())
                type_list['amount'].append(kt.group())

        ###确定类型##
        fenci_add_cixing = pseg.cut(ques)
        for item_type in fenci_add_cixing:
            if item_type.flag == 'ty':
                type_list['type'].append(item_type.word)
                break

        ###确定商户##
        fenci_add_cixing = pseg.cut(ques)
        label = 0
        for item_merchant in fenci_add_cixing:
            if label == 1:
                type_list['merchant'].append(item_merchant.word)
                break
            if item_merchant.word == '在':
                label = 1

        ###确定单位##
        p1 = re.compile(u'(多少笔|几笔)')
        p2 = re.compile(u'(多少钱|收入了多少|花了多少)')
        mb = []
        mq = []
        for m in p1.finditer(ques):
            mb.append(m.group())
        for m in p2.finditer(ques):
            mq.append(m.group())
        if len(mb) != 0:
            type_list['unit'].append(0)
        elif len(mq)!= 0:
            type_list['unit'].append(1)
        else:
            type_list['unit'].append(2)

        return type_list