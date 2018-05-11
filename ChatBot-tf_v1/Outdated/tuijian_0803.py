# coding:utf-8
import sys
import jieba
import MySQLdb
import os
import sys
import urllib2
import json
from questionlistall import questionlist
from daikuan import daikuan
from nianfei import nianfei
from gensim import corpora,models,similarities
from queryGraph import query_neo4j
from classify import Doc
import cPickle

reload(sys)
sys.setdefaultencoding("utf8")

before = sys.path[0] +"/resource_classify.txt"
after = "split_resource.txt"
file1 = open(sys.path[0] +'/guashi_classify.txt', 'r')
corpora_guashi = file1.readlines()
file2 = open(sys.path[0] +'/chaxun_classify.txt', 'r')
corpora_chaxun = file2.readlines()
file3 = open(sys.path[0] +'/qita_classify.txt', 'r')
corpora_qita = file3.readlines()

class recommand(object):
    def __init__(self):
        pass

    def _simlarity(self, fenci, dictionary, tfidf, corpus_tfidf):
        vec_bow = dictionary.doc2bow(fenci)
        vec_tfidf = tfidf[vec_bow]

        index = similarities.MatrixSimilarity(corpus_tfidf)
        sims = index[vec_tfidf]

        similarity = list(sims)
        return (similarity)

    def _sameNum(self, fenci, question_fenci, dic):
        samenum = []

        for fenci_result in question_fenci:
            keyWord = str(fenci_result).split('|')
            i = 0

            for word in keyWord:
                if word in fenci:
                    i += 1
                if word in fenci and word in dic:
                    i += 2
            samenum.append(i)
        return samenum

    def _combine(self, similarity, samenum):
        dic = {}
        final = []
        kmax = float(max(samenum))
        samenum_1 = []
        if max(samenum) != 0:
            for item in samenum:
                ite = float(item/kmax)
                samenum_1.append(ite)
        else:
            for item in samenum:
                ite = float(item/(kmax+1))
                samenum_1.append(ite)
        p = 0.5
        q = 1-p
        for k in range(len(similarity)):
            final.append(p*samenum_1[k]+q*similarity[k])
        index  = range(len(final))
        index.sort(key=lambda i: -final[i])
        dic['index'] = index
        dic['max'] = max(final)
        return dic

    def Rec(self, ques, log_files, flag):
        text = ques
        jieba.load_userdict(sys.path[0] + '/dic_former.txt')
        jieba.load_userdict(sys.path[0] + '/time_dic.txt')
        jieba.load_userdict(sys.path[0] + '/type_dic.txt')
        #############################################################################
        try:
            conn = MySQLdb.connect(host='202.97.222.21',
                                   user='xq',
                                   db='xiaoqing',
                                   passwd='B!gd4t4s',
                                   port=3306)
        except Exception, e:
            print e
        
        cur = conn.cursor()
        cur.execute('SET NAMES UTF8')
        sql = 'select qid,question,answer,keyword_item from xiaoqing.question_t'
        
        try:
            cur.execute(sql)
            result = cur.fetchall()
        except Exception, e:
            print e

        #qid, answer, question and question_fenci stems from database call
        qid = []
        answer = []
        question = []
        question_fenci = []

        for item in result:
            qid.append(item[0])
            question_fenci.append(item[3])
            question.append(item[1])
            answer.append(item[2])

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        answer_value = {}
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        tupu_type = False
        #精确分类
        # Should put all exceptions in an exceptional list
        #########################################################################################
        str_test = text
        if (u'怎么办' not in text and u'咋办' not in text and u'短期贷款' not in text):
            doc = Doc(before,after)
            l = doc.split_questionFile(before,after)
            line_num = doc.docsim(l,str_test)
            line_num = str(line_num)
            line_num = line_num + ' '
            fenlei = doc.judgement(line_num, str_test)
            if fenlei == 'guashi':
                answer_value['flag'] = 'report'
                return answer_value
            elif fenlei == 'chaxun':
                answer_value['flag'] = 'query'
                return answer_value

        #########################################################################################

        if (u'挂失' in text or u'丢' in text or u'找不着' in text or u'找不到' in text or u'没了' in text or u'掉了' in text \
            or u'偷' in text) and u'怎么办' not in text and u'咋办' not in text:
            answer_value['flag'] = 'report'
            return answer_value
        if u'我要办理售汇' == text or u'我要办理结汇' == text or u'我要办理结售汇' == text:
            answer_value['flag'] = 'exchange'
            return answer_value
        if u"查" in text and (u"余额" in text or u"交易" in text):
            answer_value['flag'] = 'query'
            return answer_value

        if (u'短期贷款' in text or u'短期信用贷款' in text) and (u'办' in text or u'申请' in text):
            answer_value['flag'] = 'daikuan'
            # answer_value['answer_value']
            answer_value['daikuan'] = '您好，我们的短期信用贷款有诚意贷、随意贷、放心贷等，您大概需要的额度和期限呢'
            return answer_value

        if flag == 'daikuan':
            loan = daikuan()
            answer_value = loan.Loan(text)
            if answer_value['flag'] == 'daikuan':
                return answer_value

        if (u'储蓄卡' in text) and (u'年费' in text):
            answer_value['flag'] = 'nianfei'
            answer_value['nianfei'] = '您好，储蓄卡没有年费，但对月日均资产不达标的账户收取账户管理费，按月收取，请问您是在哪个城市办的卡呢'
            return answer_value

        if flag == 'nianfei':
            fee = nianfei()
            answer_value = fee.Fee(text)
            if answer_value['flag'] == 'nianfei':
                return answer_value


        f = open(sys.path[0] + '/dic_former.txt', 'r')
        #dic is for Keyword matching
        dic = []
        #################
        for res in f:
            res = str(res).split(' ')
            dic.append(res[0])
        f.close()

        ##关键词比对#######################################################################
        fenci = list(jieba.cut(text, cut_all=False))
        #Remove duplicates
        fenci = list(set(fenci))
        if '（' in fenci:
            fenci.remove('（')
        if '）' in fenci:
            fenci.remove('）')
        if '：' in fenci:
            fenci.remove('：')
        if ' ' in fenci:
            fenci.remove(' ')
        if '！' in fenci:
            fenci.remove('！')
        if '，' in fenci:
            fenci.remove('，')
        if '。' in fenci:
            fenci.remove('。')
        if ')' in fenci:
            fenci.remove(')')
        if '(' in fenci:
            fenci.remove('(')
        if '﻿' in fenci:
            fenci.remove('﻿')
        if '/' in fenci:
            fenci.remove('/')
        if '!' in fenci:
            fenci.remove('!')
        if ':' in fenci:
            fenci.remove(':')
        if '.' in fenci:
            fenci.remove('.')
        if '、' in fenci:
            fenci.remove('、')
        if '-' in fenci:
            fenci.remove('-')
        if '*' in fenci:
            fenci.remove('*')
        if '？' in fenci:
            fenci.remove('？')
        if '' in fenci:
            fenci.remove('')
        if '”' in fenci:
            fenci.remove('”')
        if '“' in fenci:
            fenci.remove('“')
        if '\n' in fenci:
            fenci.remove('\n')
        if '?' in fenci:
            fenci.remove('?')
        if '的' in fenci:
            fenci.remove('的')
        if '呢' in fenci:
            fenci.remove('呢')
        if '那' in fenci:
            fenci.remove('那')
        if '吗' in fenci:
            fenci.remove('吗')

        ####关键字匹配计算#########################################################
        samenum = self._sameNum(fenci, question_fenci, dic)

        ##tfidf相似度比较##################################################################
        dictionary_file = open(sys.path[0] + '/dictionary.pkl', 'r')
        dictionary = cPickle.load(dictionary_file)

        tfidf_file = open(sys.path[0] + '/tfidf.pkl','r')
        tfidf = cPickle.load(tfidf_file)

        corpus_tfidf_file = open(sys.path[0] + '/corpus_tfidf.pkl','r')
        corpus_tfidf = cPickle.load(corpus_tfidf_file)

        similarity = self._simlarity(fenci, dictionary, tfidf, corpus_tfidf)

        ##合并两种排序######################################################################
        index = self._combine(similarity, samenum)['index']
        final_max = self._combine(similarity, samenum)['max']
        ##################################################################################
        std_answer = questionlist()
        answer_value = {}

        for item in result:
            if ques == item[1]:
                answer_value['answer1'] = [item[0], item[1], item[2], 1, 5]
                answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], 0, 5]
                answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], 0, 5]
                answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], 0, 5]
                answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], 0, 5]
                answer_value['flag'] = 'other'
                return answer_value
        #flag_answer points to last but 2 columns in answer_value
        flag_answer = [0, 0, 0, 0, 0]
        if std_answer.matualanswer(ques) == 'No':
            if max(similarity) < 0.1 and max(samenum) == 0:
                answer_KB = query_neo4j(ques, tupu_type)['stdAnswer']
                if answer_KB != '':
                    answer_value['answer_tupu'] = answer_KB
                    answer_value['flag'] = 'tupu'
                    return answer_value
                else:
                    answer_value['answer_tuling'] = "小M还在业务学习中，请您多多包涵~~~"
                    answer_value['flag'] = 'tuling'
                    return answer_value
            ####2要改为0.8！！！！！！！！！！！！！
            if final_max >= 0.7:
                flag_answer[0] = 1
                answer_value['answer1'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[0], 5]
                answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                answer_value['flag'] = 'other'
                return answer_value
            else:
                log_chaxun = []
                ##需要log的地址##
                if os.path.exists(log_files):
                    with open(log_files, 'r') as log:
                        for logs in log:
                            log_chaxun.append(logs.split(' ')[12])
                    QA_num = len(log_chaxun)
                    sim_list = []
                    if QA_num != 0:
                        # ks should have some upper bound
                        for ks in range(len(log_chaxun)):
                            # aim_que:
                            aim_que = log_chaxun[QA_num - 1 - ks]
                            aim_que_fen = jieba.cut(aim_que, cut_all = False)
                            total_fen = list(set(aim_que_fen).union(set(fenci)))
                            total_similarity = self._simlarity(total_fen, dictionary, tfidf, corpus_tfidf)
                            total_sameNum = self._sameNum(total_fen, question_fenci, dic)
                            total_combine = self._combine(total_similarity, total_sameNum)
                            if total_combine['max'] >= 0.8:
                                index = total_combine['index']
                                flag_answer[0] = 1
                                answer_value['answer1'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[0], 5]
                                answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                                answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                                answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                                answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                                answer_value['flag'] = 'other'
                                return answer_value
                            sim_list.append(total_combine['max'])
                        max_simlarity_index = sim_list.index(max(sim_list))
                        max_que = log_chaxun[QA_num - 1 - max_simlarity_index]
                        max_que_fen = jieba.cut(max_que, cut_all=False)
                        max_fen = list(set(max_que_fen).union(set(fenci)))
                        max_similarity = self._simlarity(max_fen, dictionary, tfidf, corpus_tfidf)
                        max_sameNum = self._sameNum(max_fen, question_fenci, dic)
                        index = self._combine(max_similarity, max_sameNum)['index']
                        if max(sim_list)<0.2:
                            # knowledge_graph = queryGraph()
                            answer_KB = query_neo4j(ques,tupu_type)['stdAnswer']
                            if answer_KB != '':
                                flag_answer[0] = 1
                                answer_value['answer1'] = ['KB', 'KBquestion', answer_KB, flag_answer[0], 5]
                                answer_value['answer2'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[1], 5]
                                answer_value['answer3'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[2], 5]
                                answer_value['answer4'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[3], 5]
                                answer_value['answer5'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[4], 5]
                                answer_value['flag'] = 'other'
                                return answer_value
                            else:
                                answer_value['answer1'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[0], 5]
                                answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                                answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                                answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                                answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                                answer_value['flag'] = 'other'
                                return answer_value
                        else:
                            answer_value['answer1'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[0], 5]
                            answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                            answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                            answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                            answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                            answer_value['flag'] = 'other'
                            return answer_value
                    else:
                        answer_KB = query_neo4j(ques,tupu_type)['stdAnswer']
                        if answer_KB != '':
                            flag_answer[0] = 1
                            answer_value['answer1'] = ['KB', 'KBquestion', answer_KB, flag_answer[0], 5]
                            answer_value['answer2'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[1], 5]
                            answer_value['answer3'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[2], 5]
                            answer_value['answer4'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[3], 5]
                            answer_value['answer5'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[4], 5]
                            answer_value['flag'] = 'other'
                            return answer_value
                        else:
                            answer_given = '抱歉，小M可能没有听懂您的问题，请您说详细一些，谢谢：）'
                            flag_answer[0] = 1
                            answer_value['answer1'] = [qid[index[0]], question[index[0]], answer_given, flag_answer[0], 5]
                            answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                            answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                            answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                            answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                            answer_value['flag'] = 'other'
                            return answer_value
                else:
                    answer_KB = query_neo4j(ques,tupu_type)['stdAnswer']
                    if answer_KB != '':
                        flag_answer[0] = 1
                        answer_value['answer1'] = ['KB', 'KBquestion', answer_KB, flag_answer[0], 5]
                        answer_value['answer2'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[1], 5]
                        answer_value['answer3'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[2], 5]
                        answer_value['answer4'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[3], 5]
                        answer_value['answer5'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[4], 5]
                        answer_value['flag'] = 'other'
                        return answer_value
                    else:
                        answer_given = '抱歉，小M可能没有听懂您的问题，请您说详细一些，谢谢：）'
                        flag_answer[0] = 1
                        answer_value['answer1'] = [qid[index[0]], question[index[0]], answer_given, flag_answer[0], 5]
                        answer_value['answer2'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[1], 5]
                        answer_value['answer3'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[2], 5]
                        answer_value['answer4'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[3], 5]
                        answer_value['answer5'] = [qid[index[4]], question[index[4]], answer[index[4]], flag_answer[4], 5]
                        answer_value['flag'] = 'other'
                        return answer_value
        else:
            answer_value['answer1'] = [0, 'stdquestion', std_answer.matualanswer(ques), 1, 6]
            answer_value['answer2'] = [qid[index[0]], question[index[0]], answer[index[0]], flag_answer[1], 5]
            answer_value['answer3'] = [qid[index[1]], question[index[1]], answer[index[1]], flag_answer[2], 5]
            answer_value['answer4'] = [qid[index[2]], question[index[2]], answer[index[2]], flag_answer[3], 5]
            answer_value['answer5'] = [qid[index[3]], question[index[3]], answer[index[3]], flag_answer[4], 5]
            answer_value['flag'] = 'other'
            return answer_value


