import pymysql.cursors
import pandas as pd
import random

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




