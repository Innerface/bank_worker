# !/usr/bin/python
# -*-coding:utf-8-*-
import numpy as np
from gensim.models import Word2Vec
from gensim.models import word2vec
from sklearn.linear_model import LogisticRegression
import pandas as pd
import jieba
import stop_words
# from sklearn.externals import joblib
import VariableFunction as vf


# 去除停词函数
def remove_stop_word(sentence):
    for words in sentence:
        if words in stop_words.CHINESE_STOP_WORDS:
            sentence.remove(words)
    for label in stop_words.CHINESE_STOP_WORDS:
        if label in sentence:
            sentence.remove(label)
    return sentence


# 句向量函数
def sen_vector(sentence):
    sts_fea = 0
    num_count = 0
    sts_sg = list(jieba.cut(sentence, cut_all=False))
    sts_sg = remove_stop_word(sts_sg)
    for word_sen in sts_sg:
        try:
            sts_fea = sts_fea + model[word_sen]
            num_count = num_count + 1
        except:
            continue
    if num_count != 0:
        return sts_fea / num_count
    else:
        return np.linspace(0, 0, 100)


jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')
# 利用gensim构建词向量
min_count = 2
size = 100
window = 5
batch_words = 400
ite = 20
sentences = word2vec.Text8Corpus(vf.localPath + '/origin_cor')
model = Word2Vec(sentences, min_count=min_count, size=size, window=window, batch_words=batch_words, iter=ite)

# 正样本：办理业务的问题
columns_names = ['feature%s' % num for num in range(1, 101)]
operation_ques = pd.read_excel(vf.localPath + '/OperationQuestion.xlsx')
positive_feature_list = [sen_vector(sen) for sen in operation_ques['问题']]
zero_list_positive = [i for i, word in enumerate(positive_feature_list) if word.all() == 0]
if len(zero_list_positive) != 0:
    for i in range(len(zero_list_positive)):
        del positive_feature_list[len(zero_list_positive) - 1 - zero_list_positive[i]]
positive_feature_table = pd.DataFrame(positive_feature_list, columns=columns_names)
positive_flag_table = pd.DataFrame([1 for num in range(len(positive_feature_list))], columns=['flag'])
positive_feature_table_test = positive_feature_table[0:15]
positive_feature_table_train = positive_feature_table[15:(len(positive_feature_table) + 1)]
positive_flag_table_test = positive_flag_table[0:15]
positive_flag_table_train = positive_flag_table[15:(len(positive_flag_table) + 1)]
positive_all = pd.concat([positive_feature_table, positive_flag_table], axis=1)

# 负样本：问答类问题
answer_ques = pd.read_table(vf.localPath + '/170905stq.txt', header=None)
negative_feature_list = [sen_vector(sen) for sen in answer_ques[0]]
zero_list_negative = [i for i, word in enumerate(negative_feature_list) if word.all() == 0]
if len(zero_list_negative) != 0:
    for i in range(len(zero_list_negative)):
        del negative_feature_list[len(zero_list_negative) - 1 - zero_list_negative[i]]
negative_feature_table = pd.DataFrame(negative_feature_list, columns=columns_names)
negative_flag_table = pd.DataFrame([0 for num in range(len(negative_feature_list))], columns=['flag'])
negative_feature_table_test = negative_feature_table[0:15]
negative_feature_table_train = negative_feature_table[15:(len(negative_feature_table) + 1)]
negative_flag_table_test = negative_flag_table[0:15]
negative_flag_table_train = negative_flag_table[15:(len(negative_flag_table) + 1)]
negative_all = pd.concat([negative_feature_table, negative_flag_table], axis=1)

# 整个样本表
sample_train = pd.concat([positive_feature_table_train, negative_feature_table_train], axis=0)
sample_train_flag = pd.concat([positive_flag_table_train, negative_flag_table_train], axis=0)
sample_test = pd.concat([positive_feature_table_test, negative_feature_table_test], axis=0)
sample_test_flag = pd.concat([positive_flag_table_test, negative_flag_table_test], axis=0)

# 构建二分类模型
classifier = LogisticRegression(class_weight={0: 0.25, 1: 0.75})
lr_classifier = classifier.fit(sample_train, sample_train_flag)
