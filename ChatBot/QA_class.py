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

from GrammarMatching import GrammarMathcing, synFilter, syn_dict
from QuestionAdj import QuestionAdj
from SOpair import buildSOpair, guidedinfoCompletion
from exceptionList import answer_exc
from firstLayerClassify import KeyWordLSIClassifier
from questionlistall import questionlist
from sklearn.externals import joblib



QA_base_version = '2017-08-18'
# Load QA base

file = open('QA_base/QA_with_pair_{}.pickle'.format(QA_base_version),'rb')
QA_base = pickle.load(file)
file.close()

print(list(QA_base))

# For LSI model loading
file = open(sys.path[0] +'/dictionary_and_corpus/split_resource.txt', 'r',encoding='utf-8')
corpus_ = file.readlines()
file = open(sys.path[0] +'/dictionary_and_corpus/resource_classify.txt', 'r',encoding='utf-8')
training_set = file.readlines()
file1 = open(sys.path[0] +'/dictionary_and_corpus/guashi_classify.txt', 'r',encoding='utf-8')
corpora_guashi = file1.readlines()
file2 = open(sys.path[0] +'/dictionary_and_corpus/chaxun_classify.txt', 'r',encoding='utf-8')
corpora_chaxun = file2.readlines()
file3 = open(sys.path[0] +'/dictionary_and_corpus/qita_classify.txt', 'r',encoding='utf-8')
corpora_qita = file3.readlines()

# Dictionary_0 is for crude classification with labels
dictionary_0 = corpora.Dictionary.load('model/model_0.dict')
corpus_0 = corpora.MmCorpus('model/model_0.mm')
lsi_0 = models.LsiModel.load('model/model_0.lsi')
index_0 = similarities.Similarity.load('model/model_0.index')

# Dictionary_1 is for searching over the whole QA base
dictionary_1 = corpora.Dictionary.load('model/model_1.dict')
corpus_1 = corpora.MmCorpus('model/model_1.mm')
lsi_1 = models.LsiModel.load('model/model_1.lsi')
index_1 = similarities.Similarity.load('model/model_1.index')

# For Keyword matching
kwf = open(sys.path[0] + '/dictionary_and_corpus/dic_former.txt', 'r',encoding='utf-8')
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

S_df = pd.read_csv('SO_dicts/Sdict_{}.csv'.format(QA_base_version),encoding='utf-8')
O_df = pd.read_csv('SO_dicts/Odict_{}.csv'.format(QA_base_version),encoding='utf-8')
M_df = pd.read_csv('SO_dicts/Mapping_{}.csv'.format(QA_base_version),encoding='utf-8')
L_dict = [(a,b) for a,b in zip(M_df['S_Side'],M_df['O_Side'])]


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

abcnn_model = ABCNN(s=params['max_len'], w=params["ws"], l2_reg=params['l2_reg'], model_type=params['model_type'],
              num_features=2, num_classes=2, num_layers=params['num_layers'])

model_path = build_path("ABCNN/model_ABCNN/", params['data_type'], params['model_type'], params['num_layers'])

clf_path = build_path("ABCNN/model_ABCNN/", params['data_type'], params['model_type'], params['num_layers'],
                          "-" + str(params['epoch']) + "-" + params['classifier'] + ".pkl")
clf = joblib.load(clf_path)
print(clf_path, "restored.")



# Should define some global parameters
tupu_type = False
dunnoTag = "小M还在业务学习中，请您多多包涵~~~"
Threshold_tfidf = 0.95
num_topics_ = 50

class QAstream(object):
    def __init__(self,Query):
        '''
        Initialization phase, triggered by first customer query
        '''
        # Optional: store parsed result of the raw query, in case future adjustments on
        # segmentator may influence performance
        self.Query_Parsed = synFilter(list(jieba.cut(Query,cut_all=False)),syn_dict)
        # First layer classifier outputs a query attribute flag, temporarily only
        # 'OP','QR','TBD', and TBD points to QA procedure
        # modification 2017-08-08: merge second stage into first one
        # (cont'd) jointly output query attribute flag+most similar questions
        self.Query_Raw = ''.join(self.Query_Parsed)
        self.stdstream = questionlist(self.Query_Parsed)
        self.Query_attr,self.simscore,self.mostsimilarQuestions \
            = KeyWordLSIClassifier(index_0,lsi_0,dictionary_0,index_1,lsi_1,dictionary_1,
                                   QA_base['question'],QA_base['question_seg'],
                                   self.Query_Raw,corpora_guashi,corpora_chaxun,corpora_qita,
                                   ImportantDic=kwdic,topNum=5)
        # Build SCENARIO-OPERATION pair
        self.SO_pair,self.CorruptionFlag = buildSOpair(self.Query_Parsed, Sdict=S_df, Odict=O_df, Ldict=L_dict)
        self.Query_History = [self.Query_Raw]


    def update(self,NewQuery):
        '''
        For Multi-round QA scenarios, update attribute and SO pair to get prepaired for next answer
        Note: cases are that the current multi-round is essentially information completion, so input
        could be corrupted, i.e. self.SO_pair may include None.
        '''
        if self.Query_Raw == NewQuery: pass
        NewQuery_Parsed = synFilter(list(jieba.cut(NewQuery,cut_all=False)),syn_dict)
        self.Query_Parsed = NewQuery_Parsed
        self.stdstream.update(NewQuery_Parsed)
        SO_pair_new,CorruptionFlag = buildSOpair(NewQuery_Parsed, Sdict=S_df, Odict=O_df, Ldict=L_dict)
        # Question completion phase in multi-round QA
        if CorruptionFlag:
            # Entering this phase indicating current SO is Corrupted
            # Be careful! SO_pair_new may be ['No Source Matching']
            self.Query_Parsed,self.SO_pair,CorruptionFlag = QuestionAdj(self.SO_pair, self.CorruptionFlag,
                                                                        SO_pair_new, NewQuery, Ldict=L_dict)
        else:
            self.SO_pair = SO_pair_new
        self.Query_Raw = ''.join(self.Query_Parsed)
        self.Query_attr, self.simscore, self.mostsimilarQuestions \
            = KeyWordLSIClassifier(index_0, lsi_0, dictionary_0, index_1, lsi_1, dictionary_1,
                                   QA_base['question'], QA_base['question_seg'],
                                   self.Query_Raw, corpora_guashi, corpora_chaxun, corpora_qita,
                                   ImportantDic=kwdic, topNum=5)
        self.CorruptionFlag = CorruptionFlag
        self.Query_History.append(NewQuery)

    def answer(self,session):
        '''
        Answer phase
        '''
        # Step 1: Examine the attribute: if is of operation type, go straightly to operation handler
        # Check exceptional cases
        exc_flag,exc_answer = answer_exc(self.stdstream)
        if exc_flag != 'non_std': return exc_answer
        if self.CorruptionFlag:
            return guidedinfoCompletion(self.SO_pair)
        # If we reach this phase here, indicating w/ high probability that the question is a pure QA
        # First get a Keyword Matching + tf-idf Scoring based result for rough screening
        # simQlist should be stored in some specific data structure
        # Optional: A too small (LSA)-based similarity score indicates hardness of the question, and tries to get
        # into the knowledge base
        if self.simscore[0][1] < 0.1:
            '''
            answer_KB = query_neo4j(self.Query_Raw, tupu_type)['stdAnswer']
            return (answer_KB if answer_KB != '' else dunnoTag)
            '''
            return dunnoTag
        elif self.simscore[0][1] > Threshold_tfidf:
        # Answer phase
            return QA_base['answer'][self.simscore[0][0]]
        # Otherwise proceed to Grammer level
        # If SO_pair table is complete, hash to local SO region
        # local_QA_base = QA_base[QA_base['so'] == self.SO_pair]
        else:
            QA_local = QA_base[QA_base['Guessed_SO_Pair'] == tuple(self.SO_pair)]
            QA_local.index = list(range(len(QA_local.index)))

            self.simscore,mostsimilarIndex, self.mostsimilarQuestions = \
                ABCNN_Score(tfSession=session,clf=clf,model=abcnn_model,
                            w=int(params["ws"]), l2_reg=float(params["l2_reg"]), epoch=int(params["epoch"]),
                            max_len=int(params["max_len"]), model_type=params["model_type"],
                            num_layers=int(params["num_layers"]), data_type=params["data_type"],
                            classifier=params["classifier"], word2vec=params["word2vec"],
                            Query=self.Query_Raw,QA_base=QA_local)
            if self.simscore > .01:
                return [QA_local['answer'][i] for i in mostsimilarIndex]

            print('Reached Grammar Phase, Answer maybe rather funny...')
            mostsimilarIndex = GrammarMathcing(self.Query_Raw, QA_local, label_type, type_list, synonym_dict, adv_list, parsecolumn)
            print('Estimated question:',[QA_local['question'][i] for i in mostsimilarIndex])
            return [QA_local['answer'][i] for i in mostsimilarIndex]

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

if __name__=='__main__':
    with tf.Session() as sess:
        saver = tf.train.Saver()
        saver.restore(sess, model_path + "-" + str(params['epoch']))
        print(model_path + "-" + str(params['epoch']), "restored.")
        run_QA(sess)



