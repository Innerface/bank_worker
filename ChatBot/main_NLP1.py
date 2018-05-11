# coding:utf-8
import jieba
from exceptionList import answer_exc
from SOpair import buildSOpair, guidedinfoCompletion
from QuestionAdj import QuestionAdj
from GrammarMatching import GrammarMathcing, synFilter, syn_dict
from firstLayerClassify import KeyWordLSIClassifier
from knowledgegraph.codes.queryGraph import query_neo4j
from rediscluster import StrictRedisCluster
from operationNew import ENRoperation
import sys
import pickle
import VariableFunction as vf
from QA_class_test import QAstream
from ABCNN.scorrer_test import ABCNN_Score
from ABCNN.ABCNN import ABCNN
from ABCNN.preprocess import Word2Vec
from ABCNN.utils import build_path
import tensorflow as tf
import os
from LRclassifier import lr_classifier, sen_vector
import pandas as pd
from textcnn import cnnclassifier
from tfidf_same_cls import  tfidf_same_cls
from MySQLConn import Mysql
import similarity_words
from different_ques import diff_ques
redis_nodes = [{'host': '47.94.201.120', 'port': 7000},
               {'host': '47.94.201.120', 'port': 7001},
               {'host': '47.94.201.120', 'port': 7002},
               {'host': '47.94.201.120', 'port': 7003},
               {'host': '47.94.201.120', 'port': 7004},
               {'host': '47.94.201.120', 'port': 7005}
               ]
# redis_nodes = [{'host': '127.0.0.1', 'port': 7000}]
try:
    redisconn = StrictRedisCluster(startup_nodes=redis_nodes)
except Exception as e:
    print(e)
    sys.exit(1)


def QA_update(NewQuery, Query_Raw, stdstream, SO_pair, CorruptionFlag, Query_History):
    """
    For Multi-round QA scenarios, update attribute and SO pair to get prepaired for next answer
    Note: cases are that the current multi-round is essentially information completion, so input
    could be corrupted, i.e. self.SO_pair may include None.
    """
    if Query_Raw == NewQuery:
        pass
    NewQuery_Parsed = synFilter(list(jieba.cut(NewQuery, cut_all=False)), syn_dict)
    Query_Parsed = NewQuery_Parsed
    stdstream.update(NewQuery_Parsed)
    SO_pair_new, CorruptionFlag1 = buildSOpair(NewQuery_Parsed, Sdict=vf.S_df, Odict=vf.O_df, Ldict=vf.L_dict)
    # Question completion phase in multi-round QA
    if CorruptionFlag1:
        # Entering this phase indicating current SO is Corrupted
        # Be careful! SO_pair_new may be ['No Source Matching']
        Query_Parsed, SO_pair, CorruptionFlag1 = QuestionAdj(SO_pair, CorruptionFlag,
                                                             SO_pair_new, NewQuery, Ldict=vf.L_dict)
    else:
        SO_pair = SO_pair_new
    Query_Raw = ''.join(Query_Parsed)
    Query_attr, simscore, mostsimilarQuestions \
        = KeyWordLSIClassifier(vf.index_0, vf.lsi_0, vf.dictionary_0, vf.index_1, vf.lsi_1, vf.dictionary_1,
                               vf.QA_base['question'], vf.QA_base['question_seg'],
                               Query_Raw, vf.corpora_guashi, vf.corpora_chaxun, vf.corpora_qita, vf.corpora_QA,
                               ImportantDic=vf.kwdic, topNum=5)
    CorruptionFlag = CorruptionFlag1
    Query_History.append(NewQuery)
    return (Query_attr, simscore, CorruptionFlag, mostsimilarQuestions, Query_Raw, Query_Parsed, SO_pair, Query_History,
            stdstream)


def QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw):
    """
    Answer phase
    """
    # Step 1: Examine the attribute: if is of operation type, go straightly to operation handler
    # Check exceptional cases
    mysql = Mysql()
    exc_flag, exc_answer = answer_exc(stdstream)
    if exc_flag != 'non_std':
        answer_value = {'answer_value': [exc_answer], 'recommend_question': [], 'recommend_answer': []}
        return answer_value
    # for words in similarity_words.different_similarity:
    #     if words in NewQuery:

    if CorruptionFlag:
        # 如果so_pair没有找齐，那么启动tfidf算法，在问题库中匹配最相近的问题，并将答案返回。如果相似度大于0.8，直接返回答案，不再
        # 进行so_pair的提示，同时将标准问题的so_pair打到该问题上；若相似度在0.5到0.8之间，在返回答案的同时，提示补齐so_pair。
        answer_value = {'answer_value': [guidedinfoCompletion(SO_pair)], 'recommend_question': [],
                        'recommend_answer': []}
        tfidf_result_t = tfidf_same_cls(NewQuery, vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t, vf.corpus_tfidf_t)
        if tfidf_result_t['max'] >= 0.8:
            sqlAll = 'select answer from question_t limit %s,1' % tfidf_result_t['index']
            result = mysql.getAll(sqlAll)
            answer_value['answer_value'] = result[0]['answer'].decode('utf-8')
        else:
            tfidf_result_auto = tfidf_same_cls(NewQuery, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                               vf.corpus_tfidf_auto)
            if tfidf_result_auto['max'] >= 0.8:
                # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                result = mysql.getAll(sqlAll)
                answer_value['answer_value'] = result[0]['answer'].decode('utf-8')

        if tfidf_result_t['max'] >= 0.5 and tfidf_result_t['max'] < 0.8:
            # tfidf_result_rec = vf.corpus_t[tfidf_result_t['index']]
            sqlAll = 'select answer from question_t limit %s,1' % tfidf_result_t['index']
            result = mysql.getAll(sqlAll)
            tfidf_result_rec = result[0]['answer'].decode('utf-8')
            if guidedinfoCompletion(SO_pair) == '请您再问清楚一点':
                answer_value['answer_value'] = '%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_rec
            elif guidedinfoCompletion(SO_pair) == '您的问题不在我们的业务范围内:)':
                answer_value['answer_value'] = '%s。如果这个回答不准确，那么，也许您的问题不在我们的业务范围内' % tfidf_result_rec
            else:
                answer_value['answer_value'] = '%s。如果这个回答不准确，那么，%s' % (
                tfidf_result_rec, guidedinfoCompletion(SO_pair))
        else:
            tfidf_result_auto = tfidf_same_cls(NewQuery, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                               vf.corpus_tfidf_auto)
            if tfidf_result_auto['max'] >= 0.8:
                # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                result = mysql.getAll(sqlAll)
                answer_value['answer_value'] = result[0]['answer'].decode('utf-8')
            elif tfidf_result_auto['max'] >= 0.5:
                sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                result = mysql.getAll(sqlAll)
                tfidf_result_auto = result[0]['answer'].decode('utf-8')
                if guidedinfoCompletion(SO_pair) == '请您再问清楚一点':
                    answer_value['answer_value'] = '%s。如果这个回答不准确，那么，请您再问清楚一点' % tfidf_result_auto
                elif guidedinfoCompletion(SO_pair) == '您的问题不在我们的业务范围内:)':
                    answer_value['answer_value'] = '%s。如果这个回答不准确，那么，也许您的问题不在我们的业务范围内' % tfidf_result_auto
                else:
                    answer_value['answer_value'] = '%s。如果这个回答不准确，那么，%s' % (
                    tfidf_result_auto, guidedinfoCompletion(SO_pair))

        return answer_value
    # If we reach this phase here, indicating w/ high probability that the question is a pure QA
    # First get a Keyword Matching + tf-idf Scoring based result for rough screening
    # simQlist should be stored in some specific data structure
    # Optional: A too small (LSA)-based similarity score indicates hardness of the question, and tries to get
    # into the knowledge base
    if simscore[0][1] < 0.1:
        answer_value = {}
        tfidf_result_t = tfidf_same_cls(NewQuery, vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t, vf.corpus_tfidf_t)
        if tfidf_result_t['max'] >= 0.5:
            # tfidf_result_rec = vf.corpus_t[tfidf_result_t['index']]
            sqlAll = 'select answer from question_t limit %s,1' % tfidf_result_t['index']
            result = mysql.getAll(sqlAll)
            mysql.dispose()
            tfidf_result_rec = result[0]['answer'].decode('utf-8')
            answer_value['answer_value'] = tfidf_result_rec
        else:
            tfidf_result_auto = tfidf_same_cls(NewQuery, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto,
                                               vf.corpus_tfidf_auto)
            if tfidf_result_auto['max'] >= 0.5:
                # tfidf_result_rec_auto = vf.corpus_auto[tfidf_result_auto['index']]
                sqlAll = 'select answer from question_auto limit %s,1' % tfidf_result_auto['index']
                result = mysql.getAll(sqlAll)
                mysql.dispose()
                tfidf_result_rec_auto = result[0]['answer'].decode('utf-8')
                answer_value['answer_value'] = tfidf_result_rec_auto
        if not answer_value:
            answer_KB = query_neo4j(Query_Raw, vf.tupu_type)['stdAnswer']

            if answer_KB != '':
                answer_value['answer_value'] = [answer_KB]
            else:
                answer_value['answer_value'] = [vf.dunnoTag]
        answer_value['recommend_question'] = []
        answer_value['recommend_answer'] = []
        return answer_value
    elif simscore[0][1] > vf.Threshold_tfidf:
        # Answer phase
        #     return vf.QA_base['answer'][self.simscore[0][0]]
        answer_value = {'answer_value': [vf.QA_base['answer'][simscore[0][0]]],
                        'recommend_question': [vf.QA_base['question'][simscore[i][0]] for i in range(1, 4)],
                        'recommend_answer': [vf.QA_base['answer'][simscore[i][0]] for i in range(1, 4)]}
        return answer_value
    # Otherwise proceed to Grammer level
    # If SO_pair table is complete, hash to local SO region
    # local_QA_base = QA_base[QA_base['so'] == self.SO_pair]
    else:
        QA_local = vf.QA_base[vf.QA_base['Guessed_SO_Pair'] == tuple(SO_pair)]
        QA_local.index = list(range(len(QA_local.index)))

        simscore, mostsimilarIndex, mostsimilarQuestions = \
            ABCNN_Score(tfSession=session, clf=vf.clf, model=vf.abcnn_model,
                        w=int(vf.params["ws"]), l2_reg=float(vf.params["l2_reg"]), epoch=int(vf.params["epoch"]),
                        max_len=int(vf.params["max_len"]), model_type=vf.params["model_type"],
                        num_layers=int(vf.params["num_layers"]), data_type=vf.params["data_type"],
                        classifier=vf.params["classifier"], word2vec=vf.params["word2vec"],
                        Query=Query_Raw, QA_base=QA_local)
        if simscore > .01:
            # return [QA_local['answer'][i] for i in mostsimilarIndex]
            answer_value = {'answer_value': [QA_local['answer'][mostsimilarIndex[0]]],
                            'recommend_question': [QA_local['question'][i] for i in mostsimilarIndex],
                            'recommend_answer': [QA_local['answer'][i] for i in mostsimilarIndex]}
            return answer_value
        print('Reached Grammar Phase, Answer maybe rather funny...')
        mostsimilarIndex = GrammarMathcing(Query_Raw, QA_local, vf.label_type, vf.type_list, vf.synonym_dict,
                                           vf.adv_list, vf.parsecolumn)
        print('Estimated question:', [QA_local['question'][i] for i in mostsimilarIndex])
        # return [QA_local['answer'][i] for i in mostsimilarIndex]
        answer_value = {'answer_value': [QA_local['answer'][mostsimilarIndex[0]]],
                        'recommend_question': [QA_local['question'][i] for i in mostsimilarIndex],
                        'recommend_answer': [QA_local['answer'][i] for i in mostsimilarIndex]}
        return answer_value


def run_QA(session, ques, id, operationID=0, flag=0, label=None):
    """

    :param ques: 输入的问题
    :param id: 客户的ID
    :param operationID: 业务树的ID编号
    :param flag: 是否是人工接管 0当前机器接管 1当前人工接管 2推荐人工接管 3客户要求人工接管
    :param label: 需要获得的信息
    :return:
    """
    # 在内存中搜索是否有当前对话的信息，如果没有，进行初始化，如果有，直接读入
    def first_answer(ques):
        question = ques
        test = QAstream(str(question))
        queryPair = [None, None]
        # 需要每次问答都更新的量：
        initial_parameter2 = {'Query_Raw': test.Query_Raw, 'Query_Parsed': test.Query_Parsed, 'SO_pair': test.SO_pair,
                              'Query_History': test.Query_History, 'stdstream': test.stdstream,
                              'CorruptionFlag': test.CorruptionFlag, 'history_so_pair': [test.SO_pair]}
        # 通过redis存入缓存。
        redisconn.set('%s+NLP' % id, pickle.dumps(initial_parameter2), ex=60)
        answerdict = test.answer(session)
        jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')

        # columns_names = ['feature%s' % num for num in range(1, 101)]
        # input_sen_vec = sen_vector(question)
        # input_feature = pd.DataFrame([input_sen_vec], columns=columns_names)
        # classify_result = lr_classifier.predict(input_feature)[0]

        classify_result = cnnclassifier(question)
        try:
            queryPair = test.SO_pair
        except:
            pass
        if '怎么办' in question or '咋办' in question:
            classify_result = 1
        if '是多少' in question or '是什么' in question:
            classify_result = 0
        # if test.Query_attr not in ('其他', '问答'):
        print(classify_result)
        if classify_result == 1:
            # 走业务流程，返回ID、flag和Label 返回值形如： {'ID': 3, 'flag': 0, 'label': {'begin_time': ['2017-08-21'], 'end_time': [
            # '2017-08-21'], 'amount': ['200'], 'merchant': [], 'name': ['周杰伦'], 'action': [2], 'type': []}}
            ques_operation = ENRoperation(str(question))
            answer_value = ques_operation.ENR(operationID, flag, label)

            answer_value['SO_pair'] = queryPair

            if '人工接管' in question or '人工' in question:
                answer_value['flag'] = 3
            print(answer_value['ID'])
            if answer_value['ID'] == 999:
                if '人工接管' in question or '人工' in question:
                    answer_value = {'flag': 3, 'recommend_question': answerdict['recommend_question'],
                                    'recommend_answer': answerdict['recommend_answer'],
                                    'answer_value': answerdict['answer_value'], 'SO_pair': queryPair}
                else:
                    answer_value = {'flag': 0, 'recommend_question': answerdict['recommend_question'],
                                    'recommend_answer': answerdict['recommend_answer'],
                                    'answer_value': answerdict['answer_value'], 'SO_pair': queryPair}
                return answer_value
            else:
                return answer_value
        else:
            # 走问答流程，并且没有人工接管，返回一个推荐回答，5个推荐问题。
            # 返回值形如：
            # {'flag':0,
            # 'answer':'分期办理成功后，扣款金额将占用卡片的信用额度，您将不可以使用此部分占用的额度',
            # 'recommend':['信用卡手机银行网页版还款',
            # '储蓄卡换卡换号，会有什么影响',
            # '储蓄卡IC卡与磁条卡相比有哪些优势',
            # '开通个人版需要多少钱',
            # '查询基金费率']}
            if flag == 0:
                if '人工接管' in question or '人工' in question:
                    answer_value = {'flag': 3, 'recommend_question': answerdict['recommend_question'],
                                    'recommend_answer': answerdict['recommend_answer'],
                                    'answer_value': answerdict['answer_value'],
                                    'SO_pair': queryPair}
                else:
                    answer_value = {'flag': 0, 'recommend_question': answerdict['recommend_question'],
                                    'recommend_answer': answerdict['recommend_answer'],
                                    'answer_value': answerdict['answer_value'],
                                    'SO_pair': queryPair}
                return answer_value
            # 走问答流程，而且有人工接管，返回5个推荐答案。
            # 返回值形如：
            # {'flag':1,
            # 'recommend':['分期办理成功后，扣款金额将占用卡片的信用额度，您将不可以使用此部分占用的额度。信用卡可用额度将根据每期还款金额恢复。',
            # '请您拨打95588，根据语音提示选择“6信用卡服务-9人工服务”，即可针对符合条件的交易办理贷记卡消费分期哦~',
            # '当您使用贷记卡在POS机上刷卡消费后，小M会筛选您符合短信消费分期条件的交易向您发送分期邀请短信，请您按照短信内容回复至95588即可办理贷记卡消费分期哦~',
            # '请您登录手机银行“最爱-信用卡”功能，在页面中选择需要办理的信用卡，点击“分期付款-分期付款”，系统会自动筛选出符合条件的交易，您根据提示即可办理贷记卡消费分期哦~',
            # '请您登录手机银行，选择“信用卡-现金分期-申请现金分期”，即可根据页面提示办理贷记卡现金分期哦~']}
            if flag == 1:
                answer_value = {'flag': 1, 'recommend_question': answerdict(session)['recommend_question'],
                                'recommend_answer': answerdict(session)['recommend_answer'],
                                'answer_value': answerdict(session)['answer_value'],
                                'SO_pair': queryPair}
                return answer_value
    if label is None:
        label = []
    value = redisconn.get('%s+NLP' % id)
    if value == None:
        # 搜索结果为None，进行初始化，并通过redis保存如内存
        for words in similarity_words.different_similarity:
            if words in ques:
                answer_list = diff_ques(ques)
                print(answer_list)
                if answer_list:
                    answer_value = {'answer_value':[]}
                    for sentence in answer_list:
                        result = first_answer(sentence)
                        if type(result['answer_value']).__name__ == 'list':
                            answer_value['answer_value'].append(result['answer_value'][0])
                        else:
                            answer_value['answer_value'].append(result['answer_value'])
                    print(answer_value['answer_value'])
                    answer_value['recommend_question'] = result['recommend_question']
                    answer_value['recommend_answer'] = result['recommend_answer']
                    answer_value['answer_value'] = '。'.join(answer_value['answer_value'])
                    answer_value['SO_pair'] = result['SO_pair']
                    return answer_value
                    break
        answer_value = first_answer(ques)
        return answer_value
    else:
        # 搜索结果不为空，说明之前有对话，从缓存中提取之前的信息。
        # 需要每次问答都更新的量：
        ###############################################################################################
        # redis mode
        type_value2 = pickle.loads(value)
        Query_Raw = type_value2['Query_Raw']
        Query_Parsed = type_value2['Query_Parsed']
        SO_pair = type_value2['SO_pair']
        Query_History = type_value2['Query_History']
        stdstream = type_value2['stdstream']
        CorruptionFlag = type_value2['CorruptionFlag']
        history_so_pair = type_value2['history_so_pair']

        NewQuery = ques

        def success_answer(NewQuery, Query_Raw, stdstream, SO_pair, CorruptionFlag, Query_History):
            (Query_attr, simscore, CorruptionFlag, mostsimilarQuestions, Query_Raw, Query_Parsed, SO_pair, Query_History,
             stdstream) = QA_update(NewQuery, Query_Raw, stdstream, SO_pair, CorruptionFlag, Query_History)
            history_so_pair.append(SO_pair)

            queryPair = [None, None]
            try:
                queryPair = SO_pair
            except:
                pass
            # redis mode
            initial_parameter2 = {'Query_Raw': Query_Raw, 'Query_Parsed': Query_Parsed, 'SO_pair': SO_pair,
                                  'Query_History': Query_History, 'stdstream': stdstream, 'CorruptionFlag': CorruptionFlag,
                                  'history_so_pair': history_so_pair}
            redisconn.set('%s+NLP' % id, pickle.dumps(initial_parameter2), ex=60)

            jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')

            # columns_names = ['feature%s' % num for num in range(1, 101)]
            # input_sen_vec = sen_vector(NewQuery)
            # input_feature = pd.DataFrame([input_sen_vec], columns=columns_names)
            # classify_result = lr_classifier.predict(input_feature)[0]

            classify_result = cnnclassifier(NewQuery)

            # if Query_attr not in ('其他', '问答') or not label or operationID > 0:
            if '怎么办' in NewQuery or '咋办' in NewQuery:
                classify_result = 1
            if '是多少' in NewQuery or '是什么' in NewQuery:
                classify_result = 0
            print(classify_result)
            if classify_result == 1 or label or operationID > 0:
                # 加入用户id    id+ 走业务流程，返回ID、flag和Label 返回值形如： {'ID': 3, 'flag': 0, 'label': {'begin_time': ['2017-08-21'],
                #  'end_time': ['2017-08-21'], 'amount': ['200'], 'merchant': [], 'name': ['周杰伦'], 'action': [2],
                # 'type': []}}
                ques_operation = ENRoperation(str(NewQuery))
                answer_value = ques_operation.ENR(operationID, flag, label)
                print(answer_value['ID'])
                if '人工接管' in NewQuery or '人工' in NewQuery:
                    answer_value['flag'] = 3
                if answer_value['ID'] == 999:
                    if '人工接管' in NewQuery or '人工' in NewQuery:
                        answer_value = {'flag': 3}
                    else:
                        answer_value = {'flag': 0}
                    answer = QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw)
                    answer_value['answer_value'] = answer['answer_value']
                    answer_value['recommend_answer'] = answer['recommend_answer']
                    answer_value['recommend_question'] = answer['recommend_question']
                    answer_value['SO_pair'] = queryPair
                    return answer_value
                else:
                    return answer_value
            else:
                # 走问答流程，并且没有人工接管，返回一个推荐回答，5个推荐问题。
                # 返回值形如：
                # {'flag':0,
                # 'answer':'分期办理成功后，扣款金额将占用卡片的信用额度，您将不可以使用此部分占用的额度',
                # 'recommend':['信用卡手机银行网页版还款',
                # '储蓄卡换卡换号，会有什么影响',
                # '储蓄卡IC卡与磁条卡相比有哪些优势',
                # '开通个人版需要多少钱',
                # '查询基金费率']}
                if flag == 0:
                    answer_value = {}
                    if '人工接管' in NewQuery or '人工' in NewQuery:
                        answer_value = {'flag': 3,
                                        'recommend_question':
                                            QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw)[
                                                'recommend_question'],
                                        'SO_pair': queryPair}
                        return answer_value

                    # if len(history_so_pair) >= 10:
                    #     k = 0
                    #     for j in range(0,4):
                    #         print(history_so_pair[len(history_so_pair)-1-j][0])
                    #         print(history_so_pair[len(history_so_pair)-1-j][1])
                    #         if history_so_pair[len(history_so_pair)-1-j][0] is None and\
                    #                         history_so_pair[len(history_so_pair)-1-j][1] is None:
                    #             k = k+ 1
                    #     if k == 5:
                    #         answer_value['flag'] = 1
                    #         answer = QA_answer(session,stdstream,CorruptionFlag,SO_pair,simscore,Query_Raw)
                    #         answer_value['answer_value'] = answer['answer_value']
                    #         answer_value['recommend_answer'] = answer['recommend_answer']
                    #         answer_value['recommend_question'] = answer['recommend_question']
                    #         return answer_value
                    if float(simscore[0][1]) < 0.05:
                        answer_value['flag'] = 2
                        answer = QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw)
                        answer_value['answer_value'] = answer['answer_value']
                        answer_value['recommend_answer'] = answer['recommend_answer']
                        answer_value['recommend_question'] = answer['recommend_question']
                        answer_value['SO_pair'] = queryPair
                        return answer_value
                    answer_value['flag'] = 0
                    answer = QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw)
                    if answer != []:
                        answer_value['answer_value'] = answer['answer_value']
                    else:
                        answer_value['answer_value'] = ['请您再问的清楚一点']
                    answer_value['recommend_question'] = answer['recommend_question']
                    answer_value['recommend_answer'] = answer['recommend_answer']
                    answer_value['SO_pair'] = queryPair
                    return answer_value
                # 走问答流程，而且有人工接管，返回5个推荐答案。
                # 返回值形如：
                # {'flag':1,
                # 'recommend':['分期办理成功后，扣款金额将占用卡片的信用额度，您将不可以使用此部分占用的额度。信用卡可用额度将根据每期还款金额恢复。',
                # '请您拨打95588，根据语音提示选择“6信用卡服务-9人工服务”，即可针对符合条件的交易办理贷记卡消费分期哦~',
                # '当您使用贷记卡在POS机上刷卡消费后，小M会筛选您符合短信消费分期条件的交易向您发送分期邀请短信，请您按照短信内容回复至95588即可办理贷记卡消费分期哦~',
                # '请您登录手机银行“最爱-信用卡”功能，在页面中选择需要办理的信用卡，点击“分期付款-分期付款”，系统会自动筛选出符合条件的交易，您根据提示即可办理贷记卡消费分期哦~',
                # '请您登录手机银行，选择“信用卡-现金分期-申请现金分期”，即可根据页面提示办理贷记卡现金分期哦~']}
                if flag == 1:
                    answer_value = {'flag': 1,
                                    'recommend_question':
                                        QA_answer(session, NewQuery, stdstream, CorruptionFlag, SO_pair, simscore, Query_Raw)[
                                            'recommend_question'],
                                    'SO_pair': queryPair}
                    return answer_value
        for words in similarity_words.different_similarity:
            if words in NewQuery:
                answer_list = diff_ques(NewQuery)
                print(answer_list)
                # print(answer_list[0])
                if answer_list:
                    answer_value = {'answer_value':[]}
                    for sentence in answer_list:
                        result = success_answer(sentence, Query_Raw, stdstream, SO_pair, CorruptionFlag, Query_History)
                        if type(result['answer_value']).__name__ == 'list':
                            answer_value['answer_value'].append(result['answer_value'][0])
                        else:
                            answer_value['answer_value'].append(result['answer_value'])
                    print(answer_value['answer_value'])
                    answer_value['recommend_question'] = result['recommend_question']
                    answer_value['recommend_answer'] = result['recommend_answer']
                    answer_value['answer_value'] = '。'.join(answer_value['answer_value'])
                    answer_value['SO_pair'] = result['SO_pair']
                    return answer_value
                    break
        answer_value = success_answer(NewQuery, Query_Raw, stdstream, SO_pair, CorruptionFlag, Query_History)
        return answer_value


def maintf(ques, id, operationID=0, flag=0, label=None):
    with tf.Session(graph=vf.g2) as sess:
        saver = tf.train.Saver()
        saver.restore(sess, vf.model_path + "-" + str(vf.params['epoch']))
        res = run_QA(sess, ques, id, operationID, flag, label)
        return res


if __name__ == "__main__":
    que = '15'
    res = maintf("贷记卡和准贷记卡有什么区别", que, operationID=0, flag=0, label=[])
    print(res)
    res = maintf("信用卡", que)
    print(res)
    res = maintf('储蓄卡和信用卡有什么不同', que)
    print(res)
    res = maintf("金卡额度是多少", que)
    print(res)
    res = maintf("储蓄卡", que)
    print(res)
    res = maintf("贵金属", que)
    print(res)
    res = maintf("贷记卡和准贷记卡有什么区别", que)
    print(res)
    res = maintf("你好", que)
    print(res)