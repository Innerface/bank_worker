# coding:utf-8
import numpy as np
import jieba
import re
import os
import pickle as cPickle
import sys
import importlib
importlib.reload(sys)
import globalFuncsVariables as gf
import jieba.posseg as pseg
import copy
from py2neo import Graph,Node,Relationship,Path,NodeSelector
import datetime
from neo4j.v1 import GraphDatabase, basic_auth
"""
def file2text(fname):
    # get plain text
    # 获取纯文本
    with open(fname, 'r') as f:
        return f.read()


def textSplitPara(text):
    # split to document-level
    # 拆分到文档级
    return text.split("\r\n\r\n")


def textSplitSent(text):
    intevel = ["。", "\r\n"]
    pattern = re.compile("|".join(intevel))
    return pattern.split(text)


def _compriseInLine(line):
    comprise = ["包含", "包括", "分为", "含"]
    pattern = re.compile("|".join(comprise))
    return pattern.search(line)


def comprise(sentences):
    sents = filter(_compriseInLine, sentences)
    sents = map(cleanLine, sents)
    return sents


def cleanLine(line):
    line = re.sub("\d+\.", "", line)
    line = line.strip()
    return line


def unstructured():
    fname = "guashi.txt"
    text = file2text(fname)
    sentences = textSplitSent(text)
    compriseRelation = comprise(sentences)
    for i in compriseRelation:
        print i
    return compriseRelation
    
    
 def parser():
    fname = "guashi.txt"
    print map(_getattr, open(fname, 'r').readlines()[:30])   
"""


def _getattr(line):
    if re.match("第.+章", line):
        return 1
    if re.match("\d\.\d(?=[^\.])", line):
        return 2
    if re.match("\d\.\d\.\d(?=[^\.])", line):
        return 3
    if re.match("\d\.\d\.\d\.\d(?=[^\.])", line):
        return 4
    if re.match("\d+\.(?=[^1-9])", line) or re.match("[^\d]", line) or re.match("\d+。", line):
        return 10
    return -1

class docnode:
    """
    Tree Node
    value is title, string, not None
    childs is subtitle, list of node, may None
    content is current content, list of string, may None
    For plain text, content is strings and childs is None.
    For subtitle, childs is nodes and content may be None or not.
    """
    def __init__(self, va=None, ch=None, co=None):
        self.value = va
        self.childs = ch
        self.content = co


def _loadBooks():
    """
    book list, book is a tree
    :return:
    """
    dirName = os.path.join(gf.baseDir,'bookpkls')
    books = []
    for fName in os.listdir(dirName):
        with open(os.path.join(dirName, fName), 'rb') as f:
            try:
                books.append(cPickle.load(f))
            except:
                pass
    return books


def _find(words, query):
    """
    whether words in query
    :param words: word list
    :param query: sentence string
    :return: bool
    """
    ans = list(filter(lambda word: word in query, words))
    return ans


def bfsTree(root, words, results):
    """
    find operation in tree, BFS
    search title first, if none, search content
    :param root: root book node
    :param words: operation
    :return: node includes operation
    """
    # search title and sub title
    queue = []
    queue.append(root)
    index = 0
    while(index < len(queue)):
        cur = queue[index]
        index += 1
        if not cur:#判断cur为空，则continue
            continue
        # process current node
        keywords=_find(words, cur.value)
        if len(keywords)>0:
            results.append((keywords,cur.value))
        # add children node
        if cur.childs:
            queue.extend(cur.childs)

    # search content
    index = 0
    while(index < len(queue)):
        cur = queue[index]
        index += 1
        if not cur:
            continue
        if cur.content is not None and len(cur.content)>0:
            for content in cur.content:
                keywords=_find(words, content)
                if len(keywords)>0:
                    results.append((keywords, content))


def findHitContents(baseReparse, incrementUpdatePkl=None):
    """
    从文档pkl资料中找到所有命中实体库的文本段落。

    baseReparse：是否需要对存量pkl库进行搜索
    incrementUpdatePkl: 表示对知识图谱更新操作指向的pkl文件，如果不为空，则进行增量更新
    :return: 返回匹配上的文本段落
    """
    # words = [u"信用卡",u"额度",u"银行卡"] #本行用于测试
    words = []
    with open(u'candidatesAll.txt', 'r',encoding='utf-8') as f:
        for line in f:
            words.append(line.strip())
    if baseReparse==True:#对pkl资料库中文档进行命名实体库匹配，一般第一次运行需要进行，之后不需要进行
        results = []
        books = _loadBooks()
        for book in books:
            bfsTree(book, words,results) #通过宽度优先搜索查找文本段
        print ('存量pkl库搜索到初步符合条件的条目数量',len(results))
        writeToPkl(results,os.path.join(gf.baseDir,'models',u'model.pkl'))
    if incrementUpdatePkl is not None:
        results = []
        book=cPickle.load(open(incrementUpdatePkl,'rb'))
        bfsTree(book, words, results)  # 通过宽度优先搜索查找文本段
        print ('增量pkl库搜索到初步符合条件的条目数量', len(results))
        writeToPkl(results, os.path.join(gf.baseDir, 'models', u'incrModel.pkl'))


def writeToPkl(obj,pklName):
    file = open(pklName, 'wb')
    cPickle.dump(obj, file, protocol=0)

def judgeNodeType(word,keywords,ind,wfs):
    '''
    :param word: word[0]表示词 word[1]表示词性
    :return: 返回'E'表示实体，返回'R'表示关系
    '''
    wd=word[0]
    pos=word[1]
    if len(wd.strip())==0 or wd.count('.')>1 :
        # print wd
        return None
    # 如果不包含合法字符串，则返回空
    if re.match('\d{1,3}\.$',wd) is not None:
        return None
    if wd in ['，','；','：',':','（','）','”',',','【','】','“','”',',','，','，','》','《']:
        return None
    if pos in ['x']:
        if ind +1<len(wfs):
            next_word = wfs[ind+1]
            if '、'in next_word[0]:
                return None
    if '、' in wd:
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

def _get_sentence_graph(sen,keywords=None):
    '''
    对句子构建图节点
    :param sen:
    :param keywords: 判断入口。如果是对问题解析，则keywords不用传入，默认为None
    :return: 句子图谱，包含E和R两种节点。若无结果，则为空数组
    '''
    tmp = pseg.cut(sen)#对句子分词，返回结果有词，和词性
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
        targets = set(keywords) & set([w[0] for w in wfs])  # 判断分词结果是否覆盖到了目标实体词     取并集
    # print content
    graph = []
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
                    entities.append(word[0] + '/' + word[1]);#word[0] ：词，word[1]：词性
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

def _analyze(inputModelPkl,outputRelationPkl):
    file = open(inputModelPkl, "rb")
    results = cPickle.load(file)
    file.close()
    results = filter(lambda x: len(x[0]) > 1, results)#挑选keywords大于1个的results
    jieba.load_userdict(u'candidatesAll.txt')  # 导入用户自定义词典
    paras = []
    for result in results:
        (keywords, content) = result
        keywords = [x for x in keywords]
        # print (','.join(keywords))
        content = content.replace(' ', '')

        # keywords = [u'结汇', u'额度']
        # content=u'以上开户证件均可通过自动语音操作结汇，每人每年等值5万美元（含）的结汇额度，,重点,目标'

        sentences = re.split(u"。|？|!|\?|！", content)
        para = []
        for sen in sentences:
            senGraph=_get_sentence_graph(sen,keywords)
            if len(senGraph) > 1:
                para.append(senGraph)
                # print (get_graph_str(senGraph))
                # print '\n', '*' * 40
        paras.append(para)
        # break
    with open(outputRelationPkl, 'wb') as f:
        cPickle.dump(paras, f, protocol=0)

def analyze(baseAnalyzer,incrementAnalyzePkl=None):
    '''
    对语料模型进行分析，得到知识图谱的表示模型。

    即为E-R-E-R等的多跳图谱，E表示实体，R表示关系。E为同一句子内部相邻的名词性词组，R为同一句子内部相邻的
    动词性词组。句子与句子构成段落。
    :return:
    '''
    if baseAnalyzer==True:
        inputModelPkl=os.path.join(gf.baseDir,'models','model.pkl')
        outputRelationPkl=os.path.join(gf.baseDir,'models','relationGraphs.pkl')
        _analyze(inputModelPkl,outputRelationPkl)
    if incrementAnalyzePkl is not None:
        outputIncrementRelationPkl = os.path.join(gf.baseDir,'models','incrementRelationGraphs.pkl')
        _analyze(incrementAnalyzePkl, outputIncrementRelationPkl)

def get_graph_str(graph):
    return  '->'.join([x[0]+'/'+x[1] for x in graph])

def writeToNeo4j(baseGraphWrite,incrementRelationPkl):
    graph = Graph("http://"+gf.baseIp+":7474", username="neo4j", password="123456")

    if baseGraphWrite==True:
        graph.delete_all()  # 删除所有节点和边
        inputRelationPkl=os.path.join(gf.baseDir,'models','relationGraphs.pkl')
        _writeToNeo4j(inputRelationPkl,graph)
    if incrementRelationPkl is not None:
        _writeToNeo4j(incrementRelationPkl, graph)

def _writeToNeo4j(inputRelationPkl,graph):
    '''
    将关系图谱读取出来，写入neo4j。对于同一个句子里面的实体的关系，加上label InSent，句子头部
    实体加上label STSen。对于同一段落相邻句子的首尾实体，加上label InPara，段落头部实体加上
    label STPara。
    :return:
    '''
    with open(inputRelationPkl,'rb') as f:
        paras=cPickle.load(f)

    cnt=0
    for para in paras:
        #逐段落进行分析
        if cnt>=0:
            nodes = []
            starttime=datetime.datetime.now()
            #构造该段落的节点链表，句子之间用None进行表征
            for i,sentence in enumerate(para):
                if len(sentence)>0 and sentence[0][1]=='R': del sentence[0]
                if len(sentence)>0 and sentence[-1][1]=='R': del sentence[-1] #保证句子内部首尾都是实体
                if len(sentence)<3: continue #至少要包含一个完整的E-R-E三元组
                for ind,graphNode in enumerate(sentence):
                    if graphNode[1]=='E':
                        nameStr=re.subn('/[a-zA-Z]+','',graphNode[0])[0]                #将graphNode[0]中任意字母替换成''
                        # print "nameStr:",nameStr,",graphNode[0]:",graphNode[0]
                        nn=Node('E',name=nameStr,pos=graphNode[0])      #nameStr为词，graphNode[0]  为词和词性
                        existNode=graph.find_one('E',property_key='name',property_value=nameStr)
                        if existNode is None:
                            if ind==0: nn.add_label('STSen')
                            if ind==0 and i==0: nn.add_label('STPara')
                            graph.create(nn)
                        else:
                            if ind==0:
                                existNode.add_label('STSen')
                            if ind==0 and i==0:
                                existNode.add_label('STPara')
                            graph.push(existNode)
                        nodes.append((nn,'E'))
                    elif graphNode[1]=='R':
                        nodes.append((graphNode[0],'R'))
                nodes.append(None)
            if len(nodes)>0 and nodes[-1] is None: del nodes[-1]

            sel = NodeSelector(graph)
            for i,node in enumerate(nodes):
                if node is None: #表示同一段落不同句子关联
                    startNode=list(sel.select('E',name=nodes[i-1][0]['name']))[0]
                    endNode=list(sel.select('E',name=nodes[i+1][0]['name']))[0]
                    relation=Relationship(startNode,'InPara',endNode)
                    graph.create(relation)
                elif node[1]=='R':
                    startNode = list(sel.select('E', name=nodes[i - 1][0]['name']))[0]
                    endNode = list(sel.select('E', name=nodes[i + 1][0]['name']))[0]
                    relation = Relationship(startNode, 'InSen', endNode)
                    relation['name']=re.subn('/|\w','',node[0])[0]
                    relation['pos']=node[0]
                    graph.create(relation)
            endtime=datetime.datetime.now()
            print (cnt,(endtime-starttime).seconds/60,' minues')
        cnt+=1
    print ('debug')


if __name__ == "__main__":
    """
    pip install django-extensions
    pip install django-werkzeug-debugger-runserver
    pip install pyOpenSSL
    pip install py2neo
    pip install neo4j-driver
    dos2unix dictionary.pkl  corpus_tfidf.pkl tfidf.pkl
    """
    print ("开始step1")
    print ("找到实体命中的文本段落，保存到model.pkl中")
    #step1: 找到实体命中的文本段落，保存到model.pkl中
    incrementUpdatePkl=os.path.join(gf.baseDir,'bookpkls','manualAddBook.pkl')
    findHitContents(baseReparse=True,incrementUpdatePkl=incrementUpdatePkl)
    print ("结束step1")


    #step2: 分析击中的段落，7获得实体关系结果
    print ("开始step2")
    print ("分析击中的段落，获得实体关系结果")
    incrementAnalyzePkl=os.path.join(gf.baseDir,'models','incrModel.pkl')
    analyze(baseAnalyzer=True,incrementAnalyzePkl=incrementAnalyzePkl)
    print ("结束step2")

    #step3：根据实体关系结果，写入neo4j
    print ("开始step3")
    print ("根据实体关系结果，写入neo4j")
    incrementRelationPkl=os.path.join(gf.baseDir,'models','incrementRelationGraphs.pkl')
    writeToNeo4j(baseGraphWrite=True,incrementRelationPkl=incrementRelationPkl)
    print ("结束step3")

    print ("done")