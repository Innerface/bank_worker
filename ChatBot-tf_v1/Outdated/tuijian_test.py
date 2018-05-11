# coding:utf-8
import sys
import jieba
import jieba.posseg as pseg
import MySQLdb
import os
import sys
import urllib2
import json
import re
import nltk
import time,datetime
from openpyxl.reader.excel import load_workbook
from chaxun import chaxun
from tuijian_0719 import recommand
from queryGraph import query_neo4j

# newque = chaxun()
# input = '我昨天用支付宝在华联超市买了200多块钱的东西，但是支付宝没有记录，能帮我查一下卡上有没有这笔交易'
# flag = [0,0,0,0,0,0,0]
jieba.load_userdict(sys.path[0] + '\\dic_former.txt')
jieba.load_userdict(sys.path[0] + '\\time_dic.txt')
jieba.load_userdict(sys.path[0] + '\\type_dic.txt')
# answer = newque.query(input, flag)
# print answer['begin_time']
# print answer['end_time']
# print answer['amount']
# print answer['type']
# print answer['merchant'][0]
# print answer['unit']

# f = open('dic_former.txt', 'r')
# dic = []
# for res in f:
#     #print res
#     res = res.split(' ')
#     dic.append(res[0])
# f.close()
newque = recommand()
input ='我想办理短期贷款'
answer = newque.Rec(input,'log.txt','other')
# print answer
# print answer['answer1']
print answer
for ty in answer['answer1']:
    print ty
print answer['answer1']
# for ty in answer['answer1']:
#     print ty
# ans = query_neo4j('通货')
# print 'ok'
# print ans
# if ans['stdAnswer'] == '':
#     print 'yes'
# print ans['shortAnswer']

# input = '我2017年3月20日用支付宝在华普超市消费了几笔'
# time_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
# time_yes = time_now - 2
# print time_yes

# d1 = datetime.datetime.now()
# d3 = d1+datetime.timedelta(days = -33)
# d3.ctime()
# d3 = str(d3).split(' ')[0]
# print(d1.weekday()+1)
#
# print d3


#
# fenci = jieba.cut(input, cut_all=False)
# fenci = list(set(fenci))
# fenci1 = pseg.cut(input)
# for item in fenci1:
#     word = item.word
#     print word
#     flag = item.flag
#     print flag
# kt = input.split('号')
# for st in kt:
#     print st

# p = re.compile(r'((\d*年\d*月\d*(日|号))|(\d*月\d*(日|号))|(\d+(日|号))|(今年\d+月\d+(号|日)))')
# p = re.compile(r'\d+(日|号)')
# p = re.compile(r'\d+')
# p = re.compile(r'(上周一|周一)')
# ymd = []
# for m in p.finditer(input):
#     # print m.group()
#     ymd.append(m.group())
#
# print ymd
# print len(ymd)
# print min(ymd)
# if ymd[0] > ymd[1]:
#     a = 1
# else:
#     a= 2
# print a
# for k in ymd:
#     print k
# time_now = time.strftime('%Y-%m-%d',time.localtime(time.time()))
# print time_now.split('-')[0]
# for k in fenci:
#     print k


# nltk.download()
# with open('combine.txt','w+') as combine:
#     with open('u1.txt','r') as u1:
#         for kt in u1:
#             print >> combine, kt
#     with open('u2.txt','r') as u2:
#         for ks in u2:
#             print >> combine, ks

