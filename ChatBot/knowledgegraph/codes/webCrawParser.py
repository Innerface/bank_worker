# coding=UTF-8

import numpy as np
import jieba
import re
import os
import _pickle as cPickle
import sys

import importlib
importlib.reload(sys)

import jieba.posseg as pseg
import copy
from py2neo import Graph,Node,Relationship,Path,NodeSelector
import datetime
from neo4j.v1 import GraphDatabase, basic_auth

import globalFuncsVariables as gf
import urllib

import unittest
from selenium import webdriver
from bs4 import BeautifulSoup

def _cut_text(text):
    tmp = pseg.cut(text)
    words = []
    flags = []
    for w in tmp:
        words.append(w.word)
        flags.append(w.flag)
    wfs = zip(words, flags)
    return wfs

def _create_node(text,graph):
    if text.strip()=='': return
    wfs = _cut_text(text)
    nameStr = ','.join([w[0] for w in wfs])
    posStr = ','.join([w[0] + '/' + w[1] for w in wfs])
    existNode = graph.find_one('E', property_key='name', property_value=nameStr)
    if existNode is None:
        nn = Node('E', name=nameStr, pos=posStr)
        nn.add_label('WebE')
        graph.create(nn)
        print (nn)
    else:
        existNode.add_label('WebE')
        graph.push(existNode)

def _create_relation(leftText,rightText,props,graph):
    if leftText.strip()=='' or rightText.strip()=='':return
    sel = NodeSelector(graph)
    leftWfs = _cut_text(leftText)
    leftNameStr = ','.join([w[0] for w in leftWfs])
    rightWfs = _cut_text(rightText)
    rightNameStr = ','.join([w[0] for w in rightWfs])
    print (leftNameStr,rightNameStr)
    startNode = list(sel.select('E', name=leftNameStr))[0]
    endNode = list(sel.select('E', name=rightNameStr))[0]
    relation = Relationship(startNode, 'InSen', endNode)
    relation['name'] = props['name']
    relation['pos'] = props['pos']
    graph.create(relation)
    print (relation)

def build_graph(parentNode,childrenNodes):
    jieba.load_userdict(u'candidatesAll.txt')  # 导入用户自定义词典
    graph = Graph("http://" + gf.baseIp + ":7474", username="neo4j", password="123456")
    _create_node(parentNode,graph)
    for cn in childrenNodes:
        left=cn[0]
        right=cn[1]
        _create_node(left,graph)
        _create_node(right,graph)
    for cn in childrenNodes:
        props={'name':u'包括','pos':u'包括/v'}
        left = cn[0]
        right = cn[1]
        _create_relation(parentNode,left,props,graph)
        props = {'name': u'是', 'pos': u'是/v'}
        _create_relation(left,right,props,graph)



def _filter_text(raw_text):
    if raw_text.startswith(u'是'): raw_text=raw_text.replace(u'是', '')
    if raw_text.startswith(u'又称'): raw_text=raw_text.replace(u'又称', '')
    return raw_text.strip()

def webGraphCrawlParser_sougou(queryText):
    print (u'扩展%s的知识图谱'%(queryText))
    req_header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    }
    req_timeout = 20
    href = u'http://www.sogou.com/web?query=%s&ie=utf8&s_from=result_up' % (queryText)
    # python 2.7
    # req = urllib2.Request(href, None, req_header)
    # resp = urllib2.urlopen(req, None, req_timeout)
    # python 3.6
    req = urllib.Request(href, None, req_header)
    resp = urllib.urlopen(req, None, req_timeout)
    html = resp.read()
    soup = BeautifulSoup(html, 'html5lib')
    section = soup.find_all('script')
    try:
        a = None
        for s in section:
            if 'kmapRight ' in s.text:
                a = s.text
                break
        # print 'a=',a
        b = re.findall(r"kmapRight = (.+\"distype\":0});", a)
        c = eval(b[0])
        # print c['xml']
        t = c['xml'].replace('\\', '')
        # print t
        soup2 = BeautifulSoup(t, 'xml')
        parentNode=soup2.attribute['word']
        eles = soup2.select('element')
        childrenNodes=[(queryText,'')]
        for ele in eles:
            name=_filter_text(ele['name'])
            desc=_filter_text(ele['year'])
            if name!='' and desc!='':
                childrenNodes.append((name,desc))
        build_graph(parentNode,childrenNodes)
    except KeyError as e:
        print ('key error',e)

def webGraphCrawlParser_baidu(queryText):
    try:
        req_header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        }
        req_timeout = 20
        href = u'http://zhidao.baidu.com/search?ct=17&pn=0&tn=ikaslist&rn=10&word=%s&fr=wwwt' % (queryText)
        # print href
        req = urllib.Request(href, None, req_header)
        resp = urllib.urlopen(req, None, req_timeout)
        html = resp.read()
        soup = BeautifulSoup(html, 'html5lib')
        strs = soup.select("dd.answer")
        lines = []
        for str in strs:
            lines.append(str.text.replace(u'答：', '') + '\n')
        with open('webAddCorpus.txt', 'a') as f:
            f.writelines(lines)
    except:
        pass



if __name__ == "__main__":
    queryText=u'中国银行'
    webGraphCrawlParser_sougou(queryText)
    # webGraphCrawlParser_baidu(u'通货膨胀和通货紧缩的关系?')

