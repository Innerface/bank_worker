# coding:utf-8
import jieba
import re

from gensim import corpora, models, similarities
import stop_words
import VariableFunction as vf


def remove_stop_word(sentence):
    for words in sentence:
        if words in stop_words.CHINESE_STOP_WORDS:
            sentence.remove(words)
    for label in stop_words.CHINESE_STOP_WORDS:
        if label in sentence:
            sentence.remove(label)
    return sentence

def sameNum(fenci, question_fenci, dic=vf.localPath + '/dictionary_and_corpus/dic.txt'):
    dic = list(open(dic, 'r', encoding='utf-8').readlines())
    dic = [item.split(' ')[0] for item in dic]
    samenum = []
    for fenci_result in question_fenci:
        keyWord = str(fenci_result).split(' ')
        i = 0
        for word in keyWord:
            if word in fenci:
                i = i + 1
            if word in fenci and word in dic:
                i += 2
        samenum.append(i)
    return samenum

def simlarity_tfidf(fenci, dictionary, tfidf, corpus_tfidf):
    vec_bow = dictionary.doc2bow(fenci)
    vec_tfidf = tfidf[vec_bow]
    index = similarities.MatrixSimilarity(corpus_tfidf)
    sims = index[vec_tfidf]
    similarity = list(sims)
    return (similarity)

def combine(similarity, samenum):
    dic = {}
    final = []
    kmax = float(max(samenum))
    samenum_1 = []
    if max(samenum) != 0:
        for item in samenum:
            ite = float(item / kmax)
            samenum_1.append(ite)
    else:
        for item in samenum:
            ite = float(item / (kmax + 1))
            samenum_1.append(ite)
    p = 0.7
    q = 1 - p
    for k in range(len(similarity)):
        final.append(p * samenum_1[k] + q * similarity[k])
    index = list(range(len(final)))
    index.sort(key=lambda i: -final[i])
    dic['index'] = index[0]
    dic['max'] = max(final)
    return dic

def tfidf_same_cls(ques, corpus_seg, dictionary, tfidf, corpus_tfidf):
    fenci = list(jieba.cut(ques, cut_all=False))
    fenci = remove_stop_word(fenci)
    samenum_t = sameNum(fenci, corpus_seg)
    tfidf_t = simlarity_tfidf(fenci, dictionary, tfidf, corpus_tfidf)
    dic_t = combine(tfidf_t, samenum_t)
    return dic_t

if __name__ == '__main__':
    input = '如何查询信用卡的额度'
    print(tfidf_same_cls(input, vf.corpus_seg_t, vf.dictionary_t, vf.tfidf_t, vf.corpus_tfidf_t))
    print(tfidf_same_cls(input, vf.corpus_seg_auto, vf.dictionary_auto, vf.tfidf_auto, vf.corpus_tfidf_auto))