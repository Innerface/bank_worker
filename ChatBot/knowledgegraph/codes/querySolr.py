# coding=UTF-8
import pysolr

from codes import globalFuncsVariables as gf
from snownlp import SnowNLP
import sys
import importlib
importlib.reload(sys)

def querySolr(questionText):
    # create a connection to a solr server
    s = pysolr.Solr(gf.solrCoreIp)

    # add a document to the index
    # doc = dict(
    #     id=1,
    #     title='Lucene in Action',
    #     author=['Erik Hatcher', 'Otis Gospodnetić'],
    # )
    # s.add(doc, commit=True)

    # do a search
    questionText=questionText.replace('.','')\
        .replace('\'','').strip()
    results = s.search(q="text:"+questionText,rows=1)
    re = {}
    if len(results)>0:
        for result in results:
            re['stdAnswer'] = format(result['text'])
    if 'stdAnswer' in re:
        list = str(re['stdAnswer']).split("。")
        re['shortAnswer'] = '。'.join(list[0:3])+'。'
    return re

if __name__ == "__main__":
    '''
        pip install pysolr
    '''
    questionText=u'''
    未能成功办理股东帐户卡怎么办？
    A股银券通业务如何申请开通？
    贴现申请人需要满足哪些条件？
    介绍一下外币小额存款情况？
    信用卡逾期会收取滞纳金吗？
    '''
    questionText=u'个人理财是什么？'
    result=querySolr(questionText)
    print (result['stdAnswer'])
    if 'shortAnswer'in result:
        print(result['shortAnswer'])
    print ('done')
