import jieba
from questionlistall import questionlist
from exceptionList import answer_exc
from SOpair import buildSOpair, guidedinfoCompletion
from QuestionAdj import QuestionAdj
from GrammarMatching import GrammarMathcing, synFilter, syn_dict
from firstLayerClassify import KeyWordLSIClassifier
from knowledgegraph.codes.queryGraph import query_neo4j
import VariableFunction as vf
from ABCNN.scorrer_test import ABCNN_Score
import tensorflow as tf
from tfidf_same_cls import tfidf_same_cls
from MySQLConn import Mysql
from queryGraph import query_neo4j
import pandas as pd

class QAstream(object):
    def __init__(self, Query, new_SO_pair, CorruptionFlag):
        """
        Initialization phase, triggered by first customer query
        """
        # Optional: store parsed result of the raw query, in case future adjustments on
        # segmentator may influence performance
        self.Query_Parsed = synFilter(list(jieba.cut(Query, cut_all=False)), syn_dict)
        self.Query = Query
        # First layer classifier outputs a query attribute flag, temporarily only
        # 'OP','QR','TBD', and TBD points to QA procedure
        # modification 2017-08-08: merge second stage into first one
        # (cont'd) jointly output query attribute flag+most similar questions
        self.Query_Raw = ''.join(self.Query_Parsed)
        self.stdstream = questionlist(self.Query_Parsed)
        self.Query_attr, self.simscore, self.mostsimilarQuestions \
            = KeyWordLSIClassifier(vf.index_0, vf.lsi_0, vf.dictionary_0, vf.index_1, vf.lsi_1, vf.dictionary_1,
                                   vf.QA_base['question'], vf.QA_base['question_seg'],
                                   self.Query_Raw, vf.corpora_guashi, vf.corpora_chaxun, vf.corpora_qita, vf.corpora_QA,
                                   ImportantDic=vf.kwdic, topNum=5)
        # Build SCENARIO-OPERATION pair
        # self.SO_pair, self.CorruptionFlag = buildSOpair(self.Query_Parsed, Sdict=vf.S_df, Odict=vf.O_df,
        #                                                 Ldict=vf.L_dict)
        self.SO_pair = new_SO_pair
        self.CorruptionFlag = CorruptionFlag
        self.Query_History = [self.Query_Raw]

    def update(self, NewQuery):
        """
        For Multi-round QA scenarios, update attribute and SO pair to get prepaired for next answer
        Note: cases are that the current multi-round is essentially information completion, so input
        could be corrupted, i.e. self.SO_pair may include None.
        """
        if self.Query_Raw == NewQuery: pass
        NewQuery_Parsed = synFilter(list(jieba.cut(NewQuery, cut_all=False)), syn_dict)
        self.Query_Parsed = NewQuery_Parsed
        self.stdstream.update(NewQuery_Parsed)
        SO_pair_new, CorruptionFlag = buildSOpair(NewQuery_Parsed, Sdict=vf.S_df, Odict=vf.O_df, Ldict=vf.L_dict)
        # Question completion phase in multi-round QA
        if CorruptionFlag:
            # Entering this phase indicating current SO is Corrupted
            # Be careful! SO_pair_new may be ['No Source Matching']
            self.Query_Parsed, self.SO_pair, CorruptionFlag = QuestionAdj(self.SO_pair, self.CorruptionFlag,
                                                                          SO_pair_new, NewQuery, Ldict=vf.L_dict)
        else:
            self.SO_pair = SO_pair_new
        self.Query_Raw = ''.join(self.Query_Parsed)
        self.Query_attr, self.simscore, self.mostsimilarQuestions \
            = KeyWordLSIClassifier(vf.index_0, vf.lsi_0, vf.dictionary_0, vf.index_1, vf.lsi_1, vf.dictionary_1,
                                   vf.QA_base['question'], vf.QA_base['question_seg'],
                                   self.Query_Raw, vf.corpora_guashi, vf.corpora_chaxun, vf.corpora_qita,
                                   ImportantDic=vf.kwdic, topNum=5)
        self.CorruptionFlag = CorruptionFlag
        self.Query_History.append(NewQuery)

    def answer(self, session):
        """
        Answer phase
        """
        # Step 1: Examine the attribute: if is of operation type, go straightly to operation handler
        # Check exceptional cases
        mysql = Mysql()
        exc_flag, exc_answer = answer_exc(self.stdstream)
        if exc_flag != 'non_std':
            answer_value = {'answer_value': [exc_answer], 'recommend_question': [], 'recommend_answer': []}
            return answer_value
        if not self.SO_pair:
            self.SO_pair = [None,None]
        if self.CorruptionFlag:
            print(self.SO_pair)
            # answer_value = {'answer_value': [guidedinfoCompletion(self.SO_pair)], 'recommend_question': [],
            #                 'recommend_answer': []}
            answer_value = {'answer_value': [], 'recommend_question': [],
                            'recommend_answer': []}
            tfidf_result_t = tfidf_same_cls(self.Query,  vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t, vf.corpus_tfidf_t)
            if tfidf_result_t['max'] >= 0.8:
                sqlAll = 'select answer from question_t limit %s,1'% tfidf_result_t['index']
                result = mysql.getAll(sqlAll)
                # mysql.dispose()
                answer_value['answer_value'] = [result[0]['answer'].decode('utf-8')]
            else:
                tfidf_result_auto = tfidf_same_cls(self.Query, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                                vf.corpus_tfidf_auto)
                if tfidf_result_auto['max'] >= 0.8:
                    # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                    sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                    result = mysql.getAll(sqlAll)
                    answer_value['answer_value'] = [result[0]['answer'].decode('utf-8')]

            if tfidf_result_t['max'] >= 0.5 and tfidf_result_t['max'] < 0.8:
                # tfidf_result_rec = vf.corpus_t[tfidf_result_t['index']]
                sqlAll = 'select answer from question_t limit %s,1'% tfidf_result_t['index']
                result = mysql.getAll(sqlAll)
                # mysql.dispose()
                tfidf_result_rec = result[0]['answer'].decode('utf-8')
                answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_rec]
                # if guidedinfoCompletion(self.SO_pair) == '请您再问清楚一点':
                #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_rec]
                # elif guidedinfoCompletion(self.SO_pair) == '您的问题不在我们的业务范围内:)':
                #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，也许您的问题不在我们的业务范围内' % tfidf_result_rec]
                # else:
                #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，%s'%(tfidf_result_rec, guidedinfoCompletion(self.SO_pair))]
            else:
                tfidf_result_auto = tfidf_same_cls(self.Query, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                                vf.corpus_tfidf_auto)
                if tfidf_result_auto['max'] >= 0.8:
                    # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                    sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                    result = mysql.getAll(sqlAll)
                    # mysql.dispose()
                    answer_value['answer_value'] = [result[0]['answer'].decode('utf-8')]
                elif tfidf_result_auto['max'] >= 0.5:
                    sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                    result = mysql.getAll(sqlAll)
                    # mysql.dispose()
                    tfidf_result_auto = result[0]['answer'].decode('utf-8')
                    answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_auto]
                    # if guidedinfoCompletion(self.SO_pair) == '请您再问清楚一点':
                    #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_auto]
                    # elif guidedinfoCompletion(self.SO_pair) == '您的问题不在我们的业务范围内:)':
                    #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，也许您的问题不在我们的业务范围内' % tfidf_result_auto]
                    # else:
                    #     answer_value['answer_value'] = ['%s。如果这个回答不准确，那么，%s' % (tfidf_result_auto, guidedinfoCompletion(self.SO_pair))]

            return answer_value
        # If we reach this phase here, indicating w/ high probability that the question is a pure QA
        # First get a Keyword Matching + tf-idf Scoring based result for rough screening
        # simQlist should be stored in some specific data structure
        # Optional: A too small (LSA)-based similarity score indicates hardness of the question, and tries to get
        # into the knowledge base
        # print('OK')
        # print(self.simscore[0][1])
        # print(self.simscore)
        print(type(self.simscore))
        print(self.simscore[0][1])

        if self.simscore[0][1] < 0.1:
            answer_value = {}
            tfidf_result_t = tfidf_same_cls(self.Query, vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t, vf.corpus_tfidf_t)
            if tfidf_result_t['max'] >= 0.5:
                # tfidf_result_rec = vf.corpus_t[tfidf_result_t['index']]
                sqlAll = 'select answer from question_t limit %s,1'% tfidf_result_t['index']
                result = mysql.getAll(sqlAll)
                mysql.dispose()
                tfidf_result_rec = result[0]['answer'].decode('utf-8')
                answer_value['answer_value'] = [tfidf_result_rec]
            else:
                tfidf_result_auto = tfidf_same_cls(self.Query, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                                   vf.corpus_tfidf_auto)
                if tfidf_result_auto['max'] >= 0.5:
                    # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                    sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                    result = mysql.getAll(sqlAll)
                    mysql.dispose()
                    tfidf_result_rec_auto = result[0]['answer'].decode('utf-8')
                    answer_value['answer_value'] = [tfidf_result_rec_auto]
            if not answer_value:
                answer_KB = query_neo4j(self.Query_Raw, vf.tupu_type)['stdAnswer']

                if answer_KB != '':
                    answer_value['answer_value'] = [answer_KB]
                else:
                    answer_value['answer_value'] = [vf.dunnoTag]
            answer_value['recommend_question'] = []
            answer_value['recommend_answer'] = []
            return answer_value
        elif self.simscore[0][1] > vf.Threshold_tfidf:
            '''
            Answer phase
            return vf.QA_base['answer'][self.simscore[0][0]]
            '''
            answer_value = {'answer_value': [vf.QA_base['answer'][self.simscore[0][0]]],
                            'recommend_question': [vf.QA_base['question'][self.simscore[i][0]] for i in range(1, 4)],
                            'recommend_answer': [vf.QA_base['answer'][self.simscore[i][0]] for i in range(1, 4)]}
            return answer_value
        # Otherwise proceed to Grammer level
        # If SO_pair table is complete, hash to local SO region
        # local_QA_base = QA_base[QA_base['so'] == self.SO_pair]
        else:
            # QA_local = vf.QA_base[vf.QA_base['Guessed_SO_Pair'] == tuple(self.SO_pair)]
            # QA_local.index = list(range(len(QA_local.index)))

            # 利用SO_pair缩小卷积的数量
            QA_base_dic = {'answer':[],
                           'qid':[],
                           'question':[],
                           'question_seg':[],
                           'Guessed_SO_Pair':[]}
            print()
            print((vf.Mysql_SO_pair[2]['SO_pair']))
            print(vf.Mysql_SO_pair[0]['SO_pair'].decode('utf-8').split('|'))
            print(self.SO_pair)
            for i in range(len(vf.Mysql_SO_pair)):
                if not vf.Mysql_SO_pair[i]['SO_pair']:
                    continue
                for j in range(len(self.SO_pair)):
                    Mysql_SO_pair_list = vf.Mysql_SO_pair[i]['SO_pair'].decode('utf-8').split('|')
                    index = 0
                    for k in range(len(Mysql_SO_pair_list)):
                        if Mysql_SO_pair_list[k].split(',') == list(self.SO_pair[j]):
                            sql = 'select qid,answer,question,keyword_item,SO_pair from question_t limit %s,1' % i
                            answer_update = mysql.getAll(sql)
                            QA_base_dic['answer'].append(answer_update[0]['answer'].decode('utf-8'))
                            QA_base_dic['qid'].append(answer_update[0]['qid'].decode('utf-8'))
                            QA_base_dic['question'].append(answer_update[0]['question'].decode('utf-8'))
                            QA_base_dic['question_seg'].append(answer_update[0]['question_seg'].decode('utf-8'))
                            QA_base_dic['Guessed_SO_Pair'].append(answer_update[0]['SO_pair'].decode('utf-8'))
                            index = 1
                            break
                    if index == 1:
                        break
            if QA_base_dic['qid']:
                QA_local = pd.DataFrame(QA_base_dic)
            # 更新完成
                self.simscore, mostsimilarIndex, self.mostsimilarQuestions = \
                    ABCNN_Score(tfSession=session, clf=vf.clf, model=vf.abcnn_model,
                                w=int(vf.params["ws"]), l2_reg=float(vf.params["l2_reg"]), epoch=int(vf.params["epoch"]),
                                max_len=int(vf.params["max_len"]), model_type=vf.params["model_type"],
                                num_layers=int(vf.params["num_layers"]), data_type=vf.params["data_type"],
                                classifier=vf.params["classifier"], word2vec=vf.params["word2vec"],
                                Query=self.Query_Raw, QA_base=QA_local)
                if self.simscore > .01:
                    # return [QA_local['answer'][i] for i in mostsimilarIndex]
                    answer_value = {'answer_value': [QA_local['answer'][mostsimilarIndex[0]]],
                                    'recommend_question': [QA_local['question'][i] for i in mostsimilarIndex],
                                    'recommend_answer': [QA_local['answer'][i] for i in mostsimilarIndex]}
                    return answer_value
                print('Reached Grammar Phase, Answer maybe rather funny...')
                mostsimilarIndex = GrammarMathcing(self.Query_Raw, QA_local, vf.label_type, vf.type_list, vf.synonym_dict,
                                                   vf.adv_list, vf.parsecolumn)
                print('Estimated question:', [QA_local['question'][i] for i in mostsimilarIndex])
                # return [QA_local['answer'][i] for i in mostsimilarIndex]
                answer_value = {'answer_value': [QA_local['answer'][mostsimilarIndex[0]]],
                                'recommend_question': [QA_local['question'][i] for i in mostsimilarIndex],
                                'recommend_answer': [QA_local['answer'][i] for i in mostsimilarIndex]}
                return answer_value
            else:
                answer_value = {'recommend_question': [],
                                'recommend_answer': [],
                                'SO_pair': self.SO_pair}
                tfidf_result_t = tfidf_same_cls(self.Query, vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t,
                                                vf.corpus_tfidf_t)
                if tfidf_result_t['max'] >= 0.5:
                    sqlAll = 'select answer from question_t limit %s,1' % tfidf_result_t['index']
                    result = mysql.getAll(sqlAll)
                    # mysql.dispose()
                    answer_value['answer_value'] = [result[0]['answer'].decode('utf-8')]
                else:
                    answer_value['answer_value'] = ['对不起，小M听不懂您的问题，小M会好好学习，努力为您服务。您可以询问其他问题。']
                return answer_value



def run_QA(sess):
    round_counter = 1
    print('-------------Round {}--------------'.format(round_counter), '\n')
    question = input('Ask something:')
    test = QAstream(str(question))
    for _ in range(50):
        print('SO pair: ', test.SO_pair)
        print('Intention:', test.Query_attr)
        print('Answer: ', test.answer(sess))
        print('Ya probably asking... ', test.mostsimilarQuestions)
        round_counter += 1
        print('-------------Round {}--------------'.format(round_counter), '\n')
        question = input('Ask something:')
        test.update(question)
        if question == 'end':
            break


if __name__ == '__main__':
    with tf.Session() as sess:
        saver = tf.train.Saver()
        saver.restore(sess, vf.model_path + "-" + str(vf.params['epoch']))
        print(vf.model_path + "-" + str(vf.params['epoch']), "restored.")
        run_QA(sess)
