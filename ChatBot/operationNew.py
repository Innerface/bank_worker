# coding:utf-8
import sys
import jieba
import jieba.posseg as pseg
import sys
import re
from operationAnalysis import OperationAnalysis
from firstLayerClassify import firstLayerClassifyFun
import pymysql.cursors


# reload(sys)
# sys.setdefaultencoding("utf8")

class ENRoperation(object):
    def __init__(self, ques):
        self.ques = ques
        self.analysis = OperationAnalysis(self.ques)

    def ENR(self, operationID=0, flag=0,label=[]):

        ##开始没有提供任何提示信息，直接返回所有能够找到的关键信息
        try:
            conn = pymysql.connect(host='211.159.153.216',
                                   user='xq',
                                   db='xiaoqing',
                                   passwd='123456',
                                   port=3306,
                                   charset='utf8')
        except Exception as e:
            print(e)
        if operationID <= 0:

            # conn = vf.pool.connection()
            with conn.cursor() as cursor:
                encodeC = "show variables like 'character%'"
                sql = "select id,keyWord,nodeName from xiaoqing.engine_node_info where keyWord !=''"
                try:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                except Exception as e:
                    print (e)

            # operationType = firstLayerClassifyFun(self.ques)
            fenci = list(jieba.cut(self.ques, cut_all=False))

            answer_value = {'ID': 0}
            sim = []
            for item in result:
                k = 0
                for word_fenci in fenci:
                    wordset = re.split(',|，',item[1])
                    for word in wordset:
                        if word_fenci == word:
                            k =k+1
                sim.append(k)
            if not result:
                answer_value['ID'] = 999
                return answer_value
            if max(sim)!=0:
                max_index = [i for i,word in enumerate(sim) if word == max(sim)]
                answer_value['ID'] = [[result[k][0],result[k][2]] for k in max_index]
                answer_value['ID'] = answer_value['ID'][0:4]
                # answer_value['ID'] = result[sim.index(max(sim))][0]
            else:
                answer_value['ID'] = 999
                return answer_value

            # if answer_value['ID'] == 0:
            #     # answer_value['type'] = 0
            #     answer_value['flag'] = flag
            #     answer_value['label'] = self.analysis.processQuesAll()
            #     return answer_value

            ##需要加入业务分类模型，得到operationID
            answer_value['flag'] = flag
            answer_value['label'] = self.analysis.processQuesAll(label, operationID)
            # answer_value['type'] = 1
            return answer_value
        else:
            answer_value = {'label': {}, 'ID': operationID, 'flag': 0}
            with conn.cursor() as cursor:
                encodeC = "show variables like 'character%'"
                sql = "select nodeName from xiaoqing.engine_node_info where id !=%s" % operationID
                try:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                except Exception as e:
                    print (e)

            answer_value['ID'] = [[operationID,result[0][0]]]
            ##提供了需要获得的具体信息，按照需求提供相应的信息
            # answer_value['type'] = 1
            if not label:
                answer_value['label'] = self.analysis.processQuesAll()
                flag = [1 for key in answer_value['label'] if answer_value['label'][key] == []]
                if sum(flag) == len(answer_value['label']) or sum(flag) == (len(answer_value['label'])-1):
                    answer_value['ID'] = 999
                    return answer_value
                else:
                    return answer_value
            else:
                for words in label:
                    if words == 'time':
                        answer_value['label']['time'] = {
                            'begin_time': self.analysis.processQuesTime(label, operationID)['begin_time'],
                            'end_time': self.analysis.processQuesTime(label, operationID)['end_time']}

                    if words == 'name':
                        answer_value['label']['name'] = self.analysis.processQuesName(label, operationID)['name']

                    if words == 'amount':
                        answer_value['label']['amount'] = self.analysis.processQuesMoney(label, operationID)['amount']

                    if words == 'merchant':
                        answer_value['merchant']['merchant'] = self.analysis.processQuesName(label, operationID)[
                            'merchant']

                    if words == 'action':
                        answer_value['label']['action'] = self.analysis.processQuesName(label, operationID)['action']

                    if words == 'type':
                        answer_value['label']['type'] = self.analysis.processQuesType(label, operationID)['type']

                    if words == 'bank_card':
                        answer_value['label']['bank_card'] = self.analysis.processQuesNumber(label, operationID)[
                            'number']

                    if words == 'password':
                        answer_value['label']['password'] = self.analysis.processQuesNumber(label, operationID)[
                            'number']

                    if words == 'id_card':
                        answer_value['label']['id_card'] = self.analysis.processQuesNumber(label, operationID)[
                            'number']
                flag = [1 for key in answer_value['label'] if answer_value['label'][key] == []]

                if sum(flag) == len(answer_value['label']):
                    answer_value['ID'] = 999
                    return answer_value
                return answer_value


if __name__ == '__main__':
    ques = '1234'
    test = ENRoperation(ques)
    answer = test.ENR(operationID=30, flag=0,label=['bank_card'])
    print(answer)
    print (answer['ID'])