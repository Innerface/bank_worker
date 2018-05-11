# coding=UTF-8

import numpy as np
import jieba
import re
import os
import _pickle as cPickle
import sys
import importlib
import VariableFunction as vf
importlib.reload(sys)
import jieba.posseg as pseg

# baseDir='/Users/wgh/Documents/ChatBot/knowledgegraph'
baseDir=vf.localPath+'/knowledgegraph'
# baseIp='localhost'
# solrCoreIp = 'http://192.168.155.1:8984/solr'
solrCoreIp='http://211.159.153.216:8090/solr/docimportcore'#提供solr core服务的机器IP
# baseIp='211.159.153.216'
baseIp = 'localhost'

def _get_sentence_graph_specific(wfs,keywords=None): #对特定问题进行解析，keywords默认为None，表示问题解析
    graph=[]
    words = [x[0] for x in wfs]
    if keywords is None:
        if u'关系' in words:
            # 首先判定关系类的问题，如 政府和市场的关系是什么？
            entities=[]
            for ind, word in enumerate(wfs):
                if word[0]==u'关系': continue
                nodeType = judgeNodeType(word, keywords, ind, wfs)
                if nodeType=='E': entities.append(word[0]+'/'+word[1])
            if len(entities)>1: #至少包含2个以上实体
                for i in range(0,len(entities)-1):
                    graph.extend([(entities[i],'E'),('','R')])
                graph.append((entities[len(entities)-1],'E'))
        elif re.match(u'.*(包含|包括)+.*(内容|什么|哪些)+.*',''.join(words)) is not None:
            #其次判定包含类问题，如金融学包括哪些内容？或 金融学包括什么
            entities = []
            for ind, word in enumerate(wfs):
                if word[0] in [u'包含',u'包括']: break
                nodeType = judgeNodeType(word, keywords, ind, wfs)
                if nodeType == 'E': entities.append(word[0] + '/' + word[1])
            if len(entities) > 0:  # 至少包含1个以上实体
                graph.extend([(','.join(entities), 'E'), (u'$包含/v', 'R'),('','E')]) #此处约定如第一个符号为$，则表示必须满足此查询条件
    return graph


def _get_sentence_graph(sen,keywords=None):
    '''
    对句子构建图节点
    :param sen:
    :param keywords: 判断入口。如果是对问题解析，则keywords不用传入，默认为None
    :return: 句子图谱，包含E和R两种节点。若无结果，则为空数组
    '''
    tmp = pseg.cut(sen)
    words = []
    flags = []
    for w in tmp:
        if keywords is not None: #如果是训练图谱阶段
            if w.word in words and w.flag not in ['v','Vg','vn']:
                continue
        words.append(w.word)
        flags.append(w.flag)
    wfs = list(zip(words, flags))
    if keywords is not None:
        targets = set(keywords) & set([w[0] for w in wfs])  # 判断分词结果是否覆盖到了目标实体词
    # print content
    graph = []
    specific_graph=_get_sentence_graph_specific(wfs)
    if len(specific_graph)>0: #如果有返回结果的话（默认范围结果为有效），则不进入一般构造流程
        graph.extend(specific_graph)
        return graph
    if (keywords is not None and len(targets) > 0) or keywords is None:
        # 分词结果至少包含一个实体，否则不进行下一步分析；或者是问题解析入口，则keywords参数不设置，表示一定进行分析
        # print sen
        entities = []
        relations = []
        pre = 'E'  # E代表实体
        for ind, word in enumerate(wfs):
            nodeType = judgeNodeType(word, keywords, ind, wfs)
            if nodeType is not None:
                if nodeType != pre:
                    # if nodeType=='E' and len(word[0])<2:#要求实体词至少包含2个汉字
                    #     continue
                    if len(entities) > 0:
                        # es = filter(lambda x: sum([x.split('/')[0] in y for y in entities]) == 1,
                        #             entities)  # 除去包含的子串，如金融市场包含市场，则除去市场
                        es = entities
                        graph.append(((','.join(es)), 'E'));
                        entities = []
                    elif len(relations) > 0:
                        graph.append(((','.join(relations)), 'R'));
                        relations = []
                if nodeType == 'E':
                    entities.append(word[0] + '/' + word[1]);
                    pre = nodeType
                elif nodeType == 'R':
                    relations.append(word[0] + '/' + word[1]);
                    pre = nodeType
        if len(entities) > 0:
            # es = filter(lambda x: sum([x.split('/')[0] in y for y in entities]) == 1, \
            #             entities)  # 除去包含的子串，如金融市场包含市场，则除去市场
            es = entities
            graph.append(((','.join(es)), 'E'));
            entities = []
        elif len(relations) > 0:
            graph.append(((','.join(relations)), 'R'));
            relations = []
    return graph


def judgeNodeType(word,keywords,ind,wfs):
    '''
    :param word: word[0]表示词 word[1]表示词性
    :return: 返回'E'表示实体，返回'R'表示关系
    '''
    wd=word[0]
    pos=word[1]
    if len(wd.strip())==0 or re.match('^\.+|\s+$',wd) is not None \
           or re.match(',|，|，',wd) is not None or wd.count('.')>1 : #如果不包含合法字符串，则返回空
        # print wd
        return None
    if pos in ['l','Ng','n','nr','ns','nt','nz'] and len(wd)>1: #表示名词性实体
        return 'E'
    if pos in ['v','Vg','vn']:
        return 'R'
    if pos in ['x','q','m']: #如果是数字，则如果下一个词跟着是货币单位，也识别成实体
        if ind+1<len(wfs):
            next_word=wfs[ind+1]
            if next_word[1] in ['x','q','m']:
                return 'E'
        if ind-1>=0:
            pre_word=wfs[ind-1]
            if pre_word[1] in ['x','q','m']:
                return 'E'
    if pos in ['x'] and len(wd)>1:
        return 'E' #特别的，如果是未识别的生词且超过一个字符，仍然认为是实体
    if keywords is not None and word in keywords:
        return 'E'
    return None