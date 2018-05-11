#!/usr/bin/python
# -*- coding:utf-8 -*-

import jieba
import re
import sys
from gensim.similarities import Similarity
from gensim import corpora, models, similarities
import numpy as np
from numpy import linalg as LA

import pymysql.cursors


def build_model(text_list,num_topics_):
    names = locals()
    for i,texts in enumerate(text_list):
        names['dictionary_%s' % i]= corpora.Dictionary(texts)
        names['corpus_%s' % i] =[names['dictionary_%s' % i].doc2bow(text) for text in texts]
        names['dictionary_%s' % i].save('model/model_'+str(i)+'.dict')
        corpora.MmCorpus.serialize('model/model_'+str(i)+'.mm', names['corpus_%s' % i])
        names['tfidf_%s' % i]=models.TfidfModel(names['corpus_%s' % i])
        names['corpus_tfidf_%s' % i]=names['tfidf_%s' % i][names['corpus_%s' % i]]
        names['lsi_%s' % i] = models.LsiModel(names['corpus_tfidf_%s' % i],id2word=names['dictionary_%s' % i],num_topics=num_topics_)
        names['corpus_lsi_%s' % i] = names['lsi_%s' % i][names['corpus_tfidf_%s' % i]]
        names['index_%s' % i] = Similarity('-Similarity-index'+str(i),names['corpus_lsi_%s' % i],num_features=num_topics_)
        names['lsi_%s' % i].save('model/model_'+str(i)+'.lsi')
        names['index_%s' % i].save('model/model_'+str(i)+'.index')



def KeywordMatching(newq_seg, question_seg, ImportantDic):
    kw_Score = []
    for q in question_seg:
        keyWord = str(q).split('|')
        i = 0
        for word in keyWord:
            if word in newq_seg:
                i += 1
            if word in newq_seg and word in ImportantDic:
                i += 2
        kw_Score.append(i)
    return kw_Score


def combineScore(lsi_Score, kw_Score, weight):
    kw_Score = np.array(kw_Score)
    sn_L2norm = LA.norm(kw_Score)
    if sn_L2norm > 0:
        kw_Score = kw_Score / sn_L2norm
    finalscore = [weight * s1 + (1 - weight) * s2 for s1, s2 in zip(kw_Score, lsi_Score)]
    return finalscore


def KeyWordLSIClassifier(index_train, lsi_train, dictionary_train,
                         index_question, lsi_question, dictionary_question,
                         question, question_seg, test_str,
                         corpora_guashi, corpora_chaxun, corpora_qita,
                         ImportantDic, topNum):
    '''
    Combinatioin of Keyword matching and tf-idf+LSI
    '''
    test_str = list(jieba.cut(test_str))
    # Keyword matching step
    score_KW = KeywordMatching(test_str, question_seg, ImportantDic)
    # Lsi Step
    test_corpus_train = lsi_train[dictionary_train.doc2bow(test_str)]
    sims_train = index_train[test_corpus_train]
    sims_train = sorted(enumerate(sims_train), key=lambda item: -item[1])
    test_corpus_question = lsi_question[dictionary_question.doc2bow(test_str)]
    sims_question = index_question[test_corpus_question]
    score_LSI = sims_question
    # Label determination
    lineNum = str(sims_train[0][0])
    for line in corpora_guashi:
        if (line.startswith(lineNum)) or ('挂失' in test_str):
            class_ = '挂失'
    for line in corpora_chaxun:
        if (line.startswith(lineNum)) or ('查询' in test_str):
            class_ = '查询'
    for line in corpora_qita:
        if line.startswith(lineNum):
            class_ = '其他'
    # Pooling scores together
    final_score = combineScore(score_LSI, score_KW, weight=0.3)
    sims_question = [x for (y, x) in sorted(zip(final_score, enumerate(sims_question)), key=lambda pair: -pair[0])]
    simscore_index = sims_question[:topNum]
    most_similar_questions = [question[j] for j in [sims_question[i][0] for i in range(topNum)]]
    return class_, simscore_index, most_similar_questions


def main():
    try:
        conn = pymysql.connect(host='202.97.222.21',
                               user='xq',
                               db='xiaoqing',
                               passwd='B!gd4t4s',
                               port=3306,
                               charset='utf8')
    except Exception as inst:
        print(inst)

    with conn.cursor() as cursor:
        encodeC = "show variables like 'character%'"
        sql = 'select qid,question,answer,keyword_item from xiaoqing.question_t'
        cursor.execute(sql)
        result = cursor.fetchall()
        qid, question, answer, question_seg = [col for col in zip(*result)]

    file = open(sys.path[0] + '/dictionary_and_corpus/split_resource.txt', 'r', encoding='utf-8')
    corpus_ = file.readlines()
    file = open(sys.path[0] + '/dictionary_and_corpus/resource_classify.txt', 'r', encoding='utf-8')
    training_set = file.readlines()
    file1 = open(sys.path[0] + '/dictionary_and_corpus/guashi_classify.txt', 'r', encoding='utf-8')
    corpora_guashi = file1.readlines()
    file2 = open(sys.path[0] + '/dictionary_and_corpus/chaxun_classify.txt', 'r', encoding='utf-8')
    corpora_chaxun = file2.readlines()
    file3 = open(sys.path[0] + '/dictionary_and_corpus/qita_classify.txt', 'r', encoding='utf-8')
    corpora_qita = file3.readlines()

    f = open(sys.path[0] + '/dictionary_and_corpus/dic_former.txt', 'r', encoding='utf-8')
    # dic is for Keyword matching
    dic = []
    #################
    for res in f:
        res = str(res).split(' ')
        dic.append(res[0])
    f.close()

    stoplist = set(' '.split())
    texts_training=[[word for word in list(jieba.cut(training_set[i][:-1])) if word not in stoplist]
          for i in range(len(training_set))]
    texts_question=[[word for word in list(jieba.cut(question[i])) if word not in stoplist]
                    for i in range(len(question))]


    names = locals()
    num_topics_ = 150
    text_list=[texts_training,texts_question]
    build_model(text_list,num_topics_)


    dictionary_0 = corpora.Dictionary.load('model/model_0.dict')
    corpus_0 = corpora.MmCorpus('model/model_0.mm')
    lsi_0 = models.LsiModel.load('model/model_0.lsi')
    index_0 = similarities.Similarity.load('model/model_0.index')

    dictionary_1 = corpora.Dictionary.load('model/model_1.dict')
    corpus_1 = corpora.MmCorpus('model/model_1.mm')
    lsi_1 = models.LsiModel.load('model/model_1.lsi')
    index_1 = similarities.Similarity.load('model/model_1.index')

    # test
    string = '定期存款'
    label, score, sentence = KeyWordLSIClassifier(index_0, lsi_0, dictionary_0, index_1, lsi_1, dictionary_1,
                                                  question, question_seg,
                                                  string, corpora_guashi, corpora_chaxun, corpora_qita,
                                                  ImportantDic=dic, topNum=5)
    print(label, score, sentence)


if __name__ == '__main__':
    main()