import numpy as np
import jieba
import re
import os
import sys
# import uniout
import pprint
import globalFuncsVariables as gf
import jieba.posseg as pseg
import copy
from py2neo import Graph,Node,Relationship,Path,NodeSelector
import datetime
from neo4j.v1 import GraphDatabase, basic_auth
import webCrawParser as wp


def _expand_node_regex(words,nodeType):
    if nodeType=='E': #如果是实体如何扩展
        pass
    elif nodeType=='R': #如果是关系如何扩展
        rels1=[u'引起',u'导致',u'致使']
        if len(set(rels1)&set(words))>0:
            words.extend(set(rels1)-set(words))
        rels1 = [u'包含', u'包括']
        if len(set(rels1) & set(words)) > 0:
            words.extend(set(rels1) - set(words))

#u'白金卡/nr,金卡/n,额度/n'
def _get_regex_str(nodeStr,nodeType='E'):
    '''
    nodeType: E表示实体，R表示关系，默认为E
    :param nodeStr:
    :param nodeType:
    :return:
    '''
    nodeStr=nodeStr.strip()
    if nodeStr=='': return '.*'
    if nodeStr.startswith('$') and nodeType=='R':
        #此处约定如第一个符号为$，则表示关系必须满足此查询条件
        nodeStr=nodeStr[1:] #去掉第一个$符号
        str = re.subn('/[a-zA-Z]+', '', nodeStr)[0]
        ss = [x.strip() for x in str.split(',')]
        _expand_node_regex(ss,nodeType)
        reg = '.*(' + '|'.join(ss) + ')+.*' if nodeType == 'E' else '.*(' + '|'.join(ss) + ')+.*'  # 对于关系，此处要求强行要求匹配
        return reg
    else:
        str = re.subn('/[a-zA-Z]+', '', nodeStr)[0]
        ss=[x.strip() for x in str.split(',')]
        _expand_node_regex(ss, nodeType)
        reg='.*('+'|'.join(ss)+')+.*' if nodeType=='E' else '.*('+'|'.join(ss)+')?.*' #对于关系，不强行要求匹配
        reasons=[u'原因',u'因素'] #判断是否是原因问句，如“物价上涨的原因是什么？”，则物价上涨和原因两个词为先后必出现的关系
        if nodeType=='E' and len(set(reasons)&set(ss))>0:
            retain_ss=filter(lambda x:x not in reasons,ss)
            reg='.*('+'|'.join(retain_ss)+')+.*('+'|'.join(reasons)+')+.*'
        return reg

def _query_for_answer(senGraph,question,session):
    i=0
    pairId=1
    matchClause=[]
    whereClause=[]
    returnVariableNames=[]
    partialReturnVariableNames=[]
    while i<len(senGraph)-2:
        if i==0:
            matchClause.append("(e%d:E)-[r%d:InSen]->(e%d:E)"%(pairId,pairId,pairId+1))
            whereClause.append("e%d.name=~'%s' and r%d.name=~'%s' and e%d.name=~'%s'"\
                               %(pairId,_get_regex_str(senGraph[i][0]),pairId,_get_regex_str(senGraph[i+1][0],'R') \
                                 ,pairId+1,_get_regex_str(senGraph[i+2][0])))
            if senGraph[i][0]=='': partialReturnVariableNames.append("e%d.name"%pairId)
            if senGraph[i+1][0] == '': partialReturnVariableNames.append("r%d.name" % pairId)
            if senGraph[i+2][0] == '': partialReturnVariableNames.append("e%d.name" % (pairId+1))
            returnVariableNames.extend(["e%d.name"%pairId,"r%d.name" % pairId,"e%d.name" % (pairId+1)])
        else:
            matchClause.append("-[r%d:InSen]->(e%d:E)" % (pairId, pairId+1))
            whereClause.append(" and r%d.name=~'%s' and e%d.name=~'%s'" \
                               % (pairId, _get_regex_str(senGraph[i + 1][0],'R') \
                                      , pairId + 1, _get_regex_str(senGraph[i + 2][0])))
            if senGraph[i + 1][0] == '': partialReturnVariableNames.append("r%d.name" % pairId)
            if senGraph[i + 2][0] == '': partialReturnVariableNames.append("e%d.name" % (pairId + 1))
            returnVariableNames.extend([ "r%d.name" % pairId, "e%d.name" % (pairId + 1)])
        i+=2;pairId+=1
    labelsVars=map(lambda x:x.replace('.name',''),filter(lambda x:x.startswith('e'),returnVariableNames))
    queryStr="MATCH "+' '.join(matchClause)+ \
        " WHERE "+' '.join(whereClause)+ \
        " RETURN "+','.join(returnVariableNames)+','+\
             ','.join(map(lambda x:'labels(%s) as %s_label'%(x,x),labelsVars))
    print(queryStr)
    # session.run("CREATE (a:Person {name: {name}, title: {title}})",
    #             {"name": "Arthur", "title": "King"})

    # result = session.run("MATCH (a:Person) WHERE a.name = {name} "
    #                      "RETURN a.name AS name, a.title AS title",
    #                      {"name": "Arthur"})
    result = session.run(queryStr)
    anss=[]
    for record in result:
        completeAnswer=[record[x] for x in returnVariableNames]
        ansLabels=dict([(x+'_label',record[x+'_label']) for x in labelsVars])
        confidenceScore=0
        for i,senNode in enumerate(senGraph):
            nameStr = re.subn('/[a-zA-Z]+', '', senNode[0])[0]
            nameStr=nameStr.strip().decode('utf8')
            if nameStr=='': continue
            qws=[x.strip() for x in nameStr.split(',')]
            cps=[x.strip() for x in completeAnswer[i].split(',')]
            # hitWords=filter(lambda x:x in completeAnswer[i],qws)
            # confidenceScore+=len(hitWords)/float(len(qws))
            weight=1.0 #对于来自WebE的节点，给予适当更大的权重
            if returnVariableNames[i].startswith('e') and \
                            'WebE' in ansLabels[returnVariableNames[i].replace('.name','')+'_label']:
                weight=1.1
            confidenceScore+=_cal_simi(qws,cps)*weight
        partialAnswer=[record[x] for x in partialReturnVariableNames]
        anss.append((completeAnswer,partialAnswer,confidenceScore))
    named_entities=_get_named_entities(question)
    if u'关系' in question and len(named_entities)>=2:
        #特别的，处理命名实体之间的关系问题，暂时只处理命名实体两两关系
        retain_ne=named_entities[:2]
        queryStr=u"MATCH (e1:E)<-[r1:InSen]-(e2:E)-[r2:InSen]->(e3:E) " \
                 u"WHERE e1.name=~'.*(%s)+.*' and" \
                 u" e3.name=~'.*(%s)+.*' and r1.name=r2.name " \
                 u"RETURN e2.name as parentName,r1.name as relationName,e1.name as leftName,e3.name as rightName," \
                 u"labels(e1) as leftLabel,labels(e3) as rightLabel"%(retain_ne[0],retain_ne[1])
        result = session.run(queryStr)
        print(queryStr)
        for record in result:
            parentName,relationName,leftName,rightName,leftLabel,rightLabel=record['parentName'], \
                record['relationName'],record['leftName'],record['rightName'],record['leftLabel'],record['rightLabel']
            completeAnswer = parentName+relationName+leftName+'、'+rightName
            weight=1.0
            if 'WebE' in leftLabel: weight+=0.05
            if 'WebE' in rightLabel: weight+=0.05
            confidenceScore = _cal_simi(retain_ne,[leftName,rightName])*weight
            partialAnswer = parentName
            anss.append((completeAnswer, partialAnswer, confidenceScore))
    anss=sorted(anss,_comp)
    return anss

def _cal_simi(query_words,complete_ans_words):
    andCount=0
    # complete_ans_words_str=','.join(complete_ans_words)
    for w in query_words:
        corr=None
        for t in complete_ans_words:
            if w in t:
                corr=t
                break
        if corr is not None: andCount+=1.0*len(w)/len(corr)
    return andCount/float(len(query_words)+len(complete_ans_words)-andCount)

def _comp(x,y):
    if (x[2] - y[2]) < 0: return 1
    elif (x[2] - y[2]) >0: return -1
    else: return 0

def _form_answer(questionText,anss):
    if re.match(u'.*(包含|包括|有)+.*(内容|什么|哪些)+.*',questionText) is not None:
        confidenceScore=anss[0][2]
        legalAnss=filter(lambda x:x[2]==confidenceScore,anss)
        if len(legalAnss)==1: return anss[0]
        else:
            shortAns=stdAns='、'.join(map(lambda x:''.join(x[1]),legalAnss))
            return (stdAns,shortAns,confidenceScore)
    return anss[0]
def _get_named_entities(sen):
    tmp = pseg.cut(sen)
    named_entites = [] #命名实体集合
    for w in tmp:
        if w.flag in ['nr','ns','nt','nz']: #如果是人名、地名、机构名或其他专有名词，则返回
            named_entites.append(w.word)
    return named_entites

def _qualifi_question(question):
    question=question.strip()
    regex=u'((什么|哪些).{0,3}(问题|结果|后果))'
    res=re.findall(regex,question)
    if len(res)>0:
        question=question.replace(res[0][0],'')
    return question

def query_neo4j(questionText,expand_graph=False):
    '''

    :param questionText: 问题字符串
    :param expand_graph: 在查询时是否从web上进行知识库扩展，默认为False
    :return:
    '''
    # graph = Graph("http://localhost:7474", username="neo4j", password="123456")
    # sel=NodeSelector(graph)
    # results=sel.select(('E','R'),name=('总结','商业银行,个人'))
    # print type(list(results)[0])
    # nn=Node(label='E',name=u'商业银行')
    # graph.create(Node('E',name=u'商业银行2'))
    jieba.load_userdict(sys.path[0] + '/candidatesAll.txt')  # 导入用户自定义词典

    driver = GraphDatabase.driver("bolt://"+gf.baseIp+":7687", auth=basic_auth("neo4j", "123456"))
    session = driver.session()
    questions = re.split(u"。|？|!|\?|！", questionText.strip())
    bestAnss=[]
    for i,question in enumerate(questions):
        question=_qualifi_question(question)
        print('final question is %s'%question)
        if len(question)==0: continue
        if expand_graph==True:
            wp.webGraphCrawlParser_baidu(question)
            named_entities=_get_named_entities(question)
            for named_entity in named_entities:
                wp.webGraphCrawlParser_sougou(named_entity)
        senGraph=gf._get_sentence_graph(question)
        if len(senGraph)>1 or (len(senGraph)==1 and senGraph[0][1]!='R'): #如果只有一个条件，也不能只是关系R限定
            if senGraph[0][1] == 'R':  # 假如第一个是关系，则补充一个查询节点
                senGraph.insert(0, ('', 'E'))
            if senGraph[-1][1] == 'R':  # 假如最后一个是关系，则补充一个查询节点
                senGraph.append(('', 'E'))
            if len(senGraph) == 1 and senGraph[0][1] == 'E':
                senGraph.extend([('', 'R'), ('', 'E')])
            anss=_query_for_answer(senGraph,question,session)
            if len(anss)==0 and len(senGraph)>3: #如果没有找到答案，则截取第一个三元组进行查询
                partSenGraph=senGraph[0:3]
                anss.extend(_query_for_answer(partSenGraph,question,session))
            if re.match(u'.*(原因)(是|是什么).*',question) is not None: #如果问的是原因，则加入转换问法的查询
                new_senGraph=[]
                new_senGraph.extend([('','E'),(u'导致/v','R')])
                new_senGraph.append((','.join(filter(lambda x:not x.startswith(u'原因'),senGraph[0][0].split(','))),'E')) #将原来的第一个E实体加入
                anss.extend(_query_for_answer(new_senGraph, question, session))
            anss = sorted(anss, _comp) #对所有渠道得到的答案就行排序
            print('查询到可能答案数量%d'%(len(anss),))
            if len(anss)>0:
                form_ans=_form_answer(question,anss)
                bestAnss.append(form_ans)
        # print 'here'
    result={}
    result['stdAnswer']='。'.join([''.join(bestAns[0]).replace(',','') for bestAns in bestAnss])
    if len(bestAnss)==1: #如果是单句提问，则同时返回缩略回答
        result['shortAnswer'] = '。'.join([''.join(bestAns[1]).replace(',', '') for bestAns in bestAnss])
    session.close()
    return result

if __name__ == "__main__":
    """
    pip install py2neo
    pip install neo4j-driver
    """
    #step4: 在neo4j中进行查询
    questionText = u"""
    白金卡和金卡的额度一样吗？
    白金卡的有效期一般是多久？
    信用卡的预留手机号可以更改吗？
    什么是信用卡？
    现在企业贷款的基本利率是多少？
    购买基金需要保证金账户吗？
    如何办理银行卡？
    美元和人民币汇率是多少？
    通货膨胀的影响有哪些？
    经济发展的目的是什么？
    企业怎样才能进行合法经营？
    商品供不应求会导致哪些问题？
    通货膨胀会导致什么问题？
    物价上涨的原因是什么？
    中国银行业金融机构包括哪些机构？
    中国银行和中国工商银行的关系是什么？
    商业银行的理财对象是谁？
    """
    questionText = u"""
    物价上涨的原因是什么？
    """
    result=query_neo4j(questionText=questionText,expand_graph=False)
    print(result['stdAnswer'])
    if result.has_key('shortAnswer'):
        print(result['shortAnswer'])


    print("done")