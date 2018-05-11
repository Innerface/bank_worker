import pymysql.cursors
import pandas as pd
import random
import pickle
from GrammarMatching import sentence_to_dic
from datetime import datetime

# Currently question base is stored locally as a csv file
# To be written into remote server as a table
# But parsing and compatibility requires loading to local and apply related algorithms
try:
    conn = pymysql.connect(host='211.159.153.216',
                           user='root',
                           db='xiaoqing',
                           passwd='ibm@1q2w#E$R',
                           port=3306,
                           charset='utf8')
except Exception as inst:
    print(inst)

with conn.cursor() as cursor:
    encodeC = "show variables like 'character%'"
    sql = 'select qid,question,answer,keyword_item from xiaoqing.question_t'
    cursor.execute(sql)
    result = cursor.fetchall()
    qid,question,answer,question_seg = [col for col in zip(*result)]
    QAdf = pd.DataFrame({'qid':qid,'question':question,'answer':answer,'question_seg':question_seg})

    # label_type is results we want from parsing
    label_type = [['主谓关系'], ['核心关系'], ['定中关系'], ['动宾关系', '前置宾语', '间宾关系']]
    # type_list is types we want corresponding label_type
    type_list = ['s', 'v', 'a', 'o', 'f']
    # synonym_dict is set of synonym
    synonym_dict = {'能否': ['是否可以']}
    adv_list = ['如何', '何时', '能否', '网上', '明细', '综合']
    # all parsing result to question_all table

    question_parsing_list = []
    for i in QAdf.index:
        question_parsing_list.append(
            sentence_to_dic(QAdf['question'][i], label_type, type_list, adv_list, synonym_dict))
    QAdf['question_parsing'] = question_parsing_list
    with open('QA_parsed_new_{}.pickle'.format(str(datetime.today()).split()[0]),mode='wb') as f:
        pickle.dump(QAdf,f)

    #QAdf.to_csv('QA_parsed_new_{}.csv'.format(str(datetime.today()).split()[0]),encoding='utf-8',index=False, line_terminator='\n')
    #QA_base_version = '2017-08-09'
    #QA_base = pd.read_csv('QA_parsed_new_{}.csv'.format(QA_base_version),encoding='utf-8',lineterminator='\n')
    #print(QA_base[:20])
    print(QAdf['question'][:20])