import pickle
import sys

import jieba
import pandas as pd
from gensim import corpora, models, similarities

# For Deep Learning block
from ABCNN.scorrer_test import ABCNN_Score
from ABCNN.ABCNN import ABCNN
from ABCNN.preprocess import Word2Vec
from ABCNN.utils import build_path
import tensorflow as tf
import MySQLConn as Mysql


# from GrammarMatching import GrammarMathcing, synFilter, syn_dict
# from QuestionAdj import QuestionAdj
# from SOpair import buildSOpair, guidedinfoCompletion
# from exceptionList import answer_exc
# from firstLayerClassify import KeyWordLSIClassifier
# from questionlistall import questionlist
from sklearn.externals import joblib

localPath = '/data/webapp/deploy/ChatBot-tf_v1'
# localPath = '/Users/wgh/Downloads/ChatBot/'

QA_base_version = '2017-08-18'
# Load QA base

file = open(localPath+'/QA_base/QA_with_pair_{}.pickle'.format(QA_base_version), 'rb')
QA_base = pickle.load(file)
file.close()

print(list(QA_base))

# For LSI model loading
file = open(localPath + '/dictionary_and_corpus/split_resource.txt', 'r', encoding='utf-8')
corpus_ = file.readlines()
file = open(localPath + '/dictionary_and_corpus/resource_classify.txt', 'r', encoding='utf-8')
training_set = file.readlines()
file1 = open(localPath + '/dictionary_and_corpus/guashi_classify.txt', 'r', encoding='utf-8')
corpora_guashi = file1.readlines()
file2 = open(localPath + '/dictionary_and_corpus/chaxun_classify.txt', 'r', encoding='utf-8')
corpora_chaxun = file2.readlines()
file3 = open(localPath + '/dictionary_and_corpus/qita_classify.txt', 'r', encoding='utf-8')
corpora_qita = file3.readlines()
file4 = open(localPath + '/dictionary_and_corpus/QA.txt', 'r', encoding='utf-8')
corpora_QA = file4.readlines()

# Dictionary_0 is for crude classification with labels
dictionary_0 = corpora.Dictionary.load(localPath+'/model/model_0.dict')
corpus_0 = corpora.MmCorpus(localPath+'/model/model_0.mm')
lsi_0 = models.LsiModel.load(localPath+'/model/model_0.lsi')
index_0 = similarities.Similarity.load(localPath+'/model/model_0.index')

# Dictionary_1 is for searching over the whole QA base
dictionary_1 = corpora.Dictionary.load(localPath+'/model/model_1.dict')
corpus_1 = corpora.MmCorpus(localPath+'/model/model_1.mm')
lsi_1 = models.LsiModel.load(localPath+'/model/model_1.lsi')
index_1 = similarities.Similarity.load(localPath+'/model/model_1.index')


dictionary_file_t = open(localPath + '/dictionary_and_corpus/dictionary_cor_t_q.pkl', 'rb')
dictionary_t = pickle.load(dictionary_file_t)

dictionary_file_auto = open(localPath + '/dictionary_and_corpus/dictionary_cor_auto_q.pkl', 'rb')
dictionary_auto = pickle.load(dictionary_file_auto)

tfidf_file_t = open(localPath + '/dictionary_and_corpus/tfidf_cor_t_q.pkl', 'rb')
tfidf_t = pickle.load(tfidf_file_t)

tfidf_file_auto = open(localPath + '/dictionary_and_corpus/tfidf_cor_auto_q.pkl', 'rb')
tfidf_auto = pickle.load(tfidf_file_auto)

corpus_tfidf_file_t = open(localPath + '/dictionary_and_corpus/corpus_tfidf_cor_t_q.pkl', 'rb')
corpus_tfidf_t = pickle.load(corpus_tfidf_file_t)

corpus_tfidf_file_auto = open(localPath + '/dictionary_and_corpus/corpus_tfidf_cor_auto_q.pkl', 'rb')
corpus_tfidf_auto = pickle.load(corpus_tfidf_file_auto)

corpus_seg_t = list(open(localPath + '/dictionary_and_corpus/origin_cor_t_q', 'r', encoding='utf-8').readlines())
corpus_seg_auto = list(open(localPath + '/dictionary_and_corpus/origin_cor_auto_q', 'r', encoding='utf-8').readlines())

corpus_t = list(open(localPath + '/dictionary_and_corpus/cor_t_q', 'r', encoding='utf-8').readlines())
corpus_auto = list(open(localPath + '/dictionary_and_corpus/cor_auto_q', 'r', encoding='utf-8').readlines())

# For Keyword matching
kwf = open(localPath + '/dictionary_and_corpus/dic.txt', 'r', encoding='utf-8')
kwdic = [str(res).split(' ')[0] for res in kwf]
kwf.close()

# For syntactic parsing and grammar matching step
# label_type is results we want from parsing
label_type = [['主谓关系'], ['核心关系'], ['定中关系'], ['动宾关系', '前置宾语', '间宾关系']]
# type_list is types we want corresponding label_type
type_list = ['s', 'v', 'a', 'o', 'f']
# synonym_dict is set of synonym
synonym_dict = {'能否': ['是否可以']}
adv_list = ['如何', '何时', '能否', '网上', '明细', '综合']
parsecolumn = 'question_parsing'

# For SO pair building
'''
# Naive solution provided by predefined pairs
S_df = pd.read_csv('Scenario.csv',encoding='utf-8')
S_df.columns = ['Node']
S_df['FatherNode'] = ['ROOT' for i in S_df['Node']]
O_df = pd.read_csv('Operation.csv',encoding='utf-8')
O_df.columns = ['Node']
O_df['FatherNode'] = ['ROOT' for i in O_df['Node']]
M_df = pd.read_csv('SO_Mapping.csv',encoding='utf-8')
L_dict = [(a,b) for a,b in zip(M_df['场景'],M_df['业务'])]
'''

S_df = pd.read_csv(localPath+'/SO_dicts/Sdict_{}.csv'.format(QA_base_version), encoding='utf-8')
S_df = S_df[S_df['Node'] != S_df['FatherNode']]
O_df = pd.read_csv(localPath+'/SO_dicts/Odict_{}.csv'.format(QA_base_version), encoding='utf-8')
M_df = pd.read_csv(localPath+'/SO_dicts/Mapping_{}.csv'.format(QA_base_version), encoding='utf-8')
L_dict = [(a, b) for a, b in zip(M_df['S_Side'], M_df['O_Side'])]

# Deep learning parameter loading
params = {
    "ws": 2,
    "l2_reg": 0.0004,
    "epoch": 50,
    "max_len": 31,
    "model_type": "ABCNN3",
    "num_layers": 3,
    "data_type": "MSRP",
    "classifier": "LR",
    "word2vec": Word2Vec()
}

tf.reset_default_graph()

g2 = tf.Graph()
with g2.as_default() as g:
    with g.name_scope( "g2" ) as g2_scope:
        abcnn_model = ABCNN(s=params['max_len'], w=params["ws"], l2_reg=params['l2_reg'],
                            model_type=params['model_type'],
                            num_features=2, num_classes=2, num_layers=params['num_layers'])

        model_path = build_path(localPath + "/ABCNN/model_ABCNN/", params['data_type'], params['model_type'],
                                params['num_layers'])

        clf_path = build_path(localPath + "/ABCNN/model_ABCNN/", params['data_type'], params['model_type'],
                              params['num_layers'],
                              "-" + str(params['epoch']) + "-" + params['classifier'] + ".pkl")
        clf = joblib.load(clf_path)
        print(clf_path, "restored.")

# Should define some global parameters
tupu_type = False
dunnoTag = "小M还在业务学习中，请您多多包涵~~~"
Threshold_tfidf = 0.95
num_topics_ = 50
mysql = Mysql.Mysql()
sql = 'select SO_pair from question_t'
Mysql_SO_pair = mysql.getAll(sql)

