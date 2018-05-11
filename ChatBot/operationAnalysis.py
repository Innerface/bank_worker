# coding:utf-8
import sys
import jieba
import jieba.posseg as pseg
import sys
import re
import time,datetime
from jpype import *
import VariableFunction as vf

# reload(sys)
# sys.setdefaultencoding("utf-8")

class OperationAnalysis(object):
    def __init__(self, ques):
        self.ques = ques

    if not isJVMStarted():
        path1 = vf.localPath+'/hanlp-1.3.4-release/hanlp-1.3.4.jar'
        path2 = vf.localPath+'/hanlp-1.3.4-release'
        startJVM(getDefaultJVMPath(),
                 "-Djava.class.path=%s:%s"%(path1,path2),
                 "-Xms128m", "Xmx128m")
    # startJVM(getDefaultJVMPath(),
    #          "-Djava.class.path=/Users/wgh/Downloads/hanlp-1.3.4-release/hanlp-1.3.4.jar:/Users/wgh/Downloads/hanlp-1.3.4-release",
    #          "-Xms512m", "Xmx512m")

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

    def processQuesTime(self, para = [], operationID = 0):
        ##找出所有关键信息：时间
        type_list = {}
        type_list['begin_time']=[]
        type_list['end_time'] = []
        p = re.compile('((\d+年\d+月\d+(日|号)(至|到)\d+年\d+月\d+(日|号))|((今年\d+月\d+(号|日))(至|到)(今年\d+月\d+(号|日)))|((今年\d+月\d+(号|日))(至|到)(\d+月\d+(号|日)))|((\d+年\d+月\d+(号|日))(至|到)(\d+月\d+(号|日)))|(\d+年\d+月\d+(日|号))|(\d+月\d+(日|号))|(\d+(日|号))|(今年\d+月\d+(号|日)))')
        ymd = []
        for m in p.finditer(self.ques):
            ymd.append(m.group())

        if len(ymd) != 0:
            for mk in range(len(ymd)):
                if '到' in ymd[mk] or '至' in ymd[mk]:
                    if '到' in ymd[mk]:
                        ymd_list = ymd[mk].split('到')
                    if '至' in ymd[mk]:
                        ymd_list = ymd[mk].split('至')
                    time_list = []
                    for item in ymd_list:
                        num = re.compile(u'\d+')
                        md = []
                        for mt in num.finditer(item):
                            md.append(mt.group())
                        if '今年' in item:
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
                    if '今年' in ymd[mk]:
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
        p = re.compile('(上周一|周一|上周二|周二|上周三|周三|上周四|周四|上周五|周五|上周六|周六|上周日|周日|上星期一|星期一|上星期二|星期二|上星期三|星期三 \
            |上星期四|星期四|上星期五|星期五|上星期六|星期六|上星期天|星期天|上星期日|星期日|上礼拜一|礼拜一|上礼拜二|礼拜二|上礼拜三|礼拜三|上礼拜四|礼拜四 \
            |上礼拜五|礼拜五|上礼拜六|礼拜六|上礼拜天|礼拜天|上礼拜日|礼拜日)')
        week_day = []
        for m in p.finditer(self.ques):
            week_day.append(m.group())

        for item_day in week_day:
            day_list=self.get_week_day(item_day)
            type_list['begin_time'].append(day_list)
            type_list['end_time'].append(day_list)

        p = re.compile(u'(目前|现在|刚刚|当前|今天)')
        day_today = []
        for ms in p.finditer(self.ques):
            day_today.append(ms.group())

        if len(day_today)!=0:
            time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            type_list['begin_time'].append(time_now)
            type_list['end_time'].append(time_now)

        if ('昨天' in self.ques):
            time_now = datetime.datetime.now()
            time_yesterday = time_now + datetime.timedelta(days=-1)
            date_yesterday = str(time_yesterday).split(' ')[0]
            type_list['begin_time'].append(date_yesterday)
            type_list['end_time'].append(date_yesterday)

        if ('前天' in self.ques):
            time_now = datetime.datetime.now()
            time_before = time_now + datetime.timedelta(days=-2)
            date_before = str(time_before).split(' ')[0]
            type_list['begin_time'].append(date_before)
            type_list['end_time'].append(date_before)

        if ('大前天' in self.ques):
            time_now = datetime.datetime.now()
            time_before_yes = time_now + datetime.timedelta(days=-3)
            date_before_yes = str(time_before_yes).split(' ')[0]
            type_list['begin_time'].append(date_before_yes)
            type_list['end_time'].append(date_before_yes)

        return type_list

    def processQuesMoney(self, para = [], operationID = 0):
        ###查找金额#####
        type_list = {}
        type_list['amount'] = []
        p = re.compile('(\d+(多块钱|块钱|元钱|块|元|多元钱))')
        amount = []
        for m in p.finditer(self.ques):
            amount.append(m.group())

        for item_amount in amount:
            p = re.compile(u'\d+')
            # amount_num = []
            for kt in p.finditer(item_amount):
                # amount_num.append(kt.group())
                type_list['amount'].append(kt.group())

        return type_list

    def processQuesMerchant(self, para = [], operationID = 0):
        NLPTokenizer = JClass('com.hankcs.hanlp.tokenizer.NLPTokenizer')
        type_list = {}
        type_list['merchant'] = []
        l = []
        splitlist = NLPTokenizer.segment(self.ques)
        for w in range(len(splitlist)):
            l.append(str(splitlist[w]))
        for word in l:
            # 提取地点
            pattern_place = re.compile('(.*?)\/(nt\w*|nz|ns)', re.S)
            result_p = re.findall(pattern_place, word)
            for result_place in result_p:
                if result_place[0] != '':
                    type_list['merchant'].append(result_place[0])

        return type_list

    def processQuesName(self, para = [], operationID = 0):
        NLPTokenizer = JClass('com.hankcs.hanlp.tokenizer.NLPTokenizer')
        type_list = {}
        type_list['name'] = []
        l = []
        splitlist = NLPTokenizer.segment(self.ques)
        for w in range(len(splitlist)):
            l.append(str(splitlist[w]))
        for word in l:
            # 提取人名
            pattern_name = re.compile('(.*?)\/nr',re.S)
            result_n = re.findall(pattern_name,word)
            for result_name in result_n:
                if result_name != '':
                    type_list['name'].append(result_name)

        return type_list

    def processQuesAction(self, para = [], operationID = 0):
        type_list = {}
        type_list['action'] = []
        p1 = re.compile('(多少笔|几笔)')
        p2 = re.compile('(多少钱|收入了多少|花了多少)')
        mb = []
        mq = []
        for m in p1.finditer(self.ques):
            mb.append(m.group())
        for m in p2.finditer(self.ques):
            mq.append(m.group())
        if len(mb) != 0:
            type_list['action'].append(0)
        elif len(mq)!= 0:
            type_list['action'].append(1)
        else:
            type_list['action'].append(2)

        return type_list


    def processQuesType(self, para = [], operationID = 0):
        type_list = {}
        type_list['type'] = []
        ###确定类型##
        fenci_add_cixing = pseg.cut(self.ques)
        for item_type in fenci_add_cixing:
            if item_type.flag == 'ty':
                type_list['type'].append(item_type.word)
                break

        return type_list

    def processQuesNumber(self, para = [], operationID = 0):
        type_list = {}
        type_list['number'] = []
        p = re.compile('\d+')
        for m in p.finditer(self.ques):
            type_list['number'].append(m.group())

        return type_list

    def processQuesAll(self, para = [], operationID = 0):
        type_list = {}
        type_list['begin_time'] = self.processQuesTime(para, operationID)['begin_time']
        type_list['end_time'] = self.processQuesTime(para, operationID)['end_time']
        type_list['amount'] = self.processQuesMoney(para, operationID)['amount']
        type_list['merchant'] = self.processQuesMerchant(para, operationID)['merchant']
        type_list['name'] = self.processQuesName(para, operationID)['name']
        type_list['action'] = self.processQuesAction(para, operationID)['action']
        type_list['type'] = self.processQuesType(para, operationID)['type']

        return type_list


def processQuesAll(ques, para = [], operationID = 0):
    analysisObject = OperationAnalysis(ques)
    type_list = {}
    type_list['begin_time'] = analysisObject.processQuesTime(para, operationID)['begin_time']
    type_list['end_time'] = analysisObject.processQuesTime(para, operationID)['end_time']
    type_list['amount'] = analysisObject.processQuesMoney(para, operationID)['amount']
    type_list['merchant'] = analysisObject.processQuesMerchant(para, operationID)['merchant']
    type_list['name'] = analysisObject.processQuesName(para, operationID)['name']
    type_list['action'] = analysisObject.processQuesAction(para, operationID)['action']
    type_list['type'] = analysisObject.processQuesType(para, operationID)['type']

    return type_list



if __name__ == '__main__':
    result = processQuesAll('我想查询上星期一在家乐福给张三的200块钱')
    test = OperationAnalysis('我想查询上星期一在家乐福给张三的200块钱')
    # print test.get_week_day('上星期一')
    print (test.processQuesTime())
    print (result['merchant'])
    print (result['name'][0])
    print (result['amount'])
    print (result['end_time'])
    print (result)
