# coding:utf-8
import jieba
import sys
from gensim import corpora, models
import pickle
import pymysql
import stop_words
import VariableFunction as vf

# localPath = '/Users/wgh/PycharmProjects/test.py/data'

def update_tfidf():
    cor_t_q = vf.localPath + '/dictionary_and_corpus/cor_t_q'
    cor_t_a = vf.localPath + '/dictionary_and_corpus/cor_t_a'
    cor_auto_q = vf.localPath + '/dictionary_and_corpus/cor_auto_q'
    cor_auto_a = vf.localPath + '/dictionary_and_corpus/cor_auto_a'
    origin_cor_t_q = vf.localPath + '/dictionary_and_corpus/origin_cor_t_q'
    origin_cor_auto_q = vf.localPath + '/dictionary_and_corpus/origin_cor_auto_q'
    datapath_t = vf.localPath + '/dictionary_and_corpus/origin_cor_t_q'
    datapath_auto = vf.localPath + '/dictionary_and_corpus/origin_cor_auto_q'
    cor_text_a = vf.localPath + '/dictionary_and_corpus/cor_auto_q'
    cor_text = vf.localPath + '/dictionary_and_corpus/cor_t_q'
    conn = None
    try:
        conn = pymysql.connect(host='211.159.153.216',
                               user='xq',
                               db='xiaoqing',
                               passwd='123456',
                               port=3306,
                               charset='utf8')
    except Exception as e:
        print (e)
    result = None
    with conn.cursor() as cursor:
        sql = "select question,answer from xiaoqing.question_t"
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
        except Exception as e:
            print (e)

    # 问题整理

    # cor_text = [','.join(line).replace('\r','') for line in result]
    # cor_text = [str(line).replace('\r','') for line in result]

    with open(cor_t_q, 'w+', encoding='utf-8') as cor:
        for sen in result:
            cor.write(sen[0])
            cor.write('\r')

    with open(cor_t_a, 'w+', encoding='utf-8') as cora:
        for sen in result:
            cora.write(sen[1])
            # cora.write('\r')

    try:
        conn = pymysql.connect(host='211.159.153.216',
                               user='xq',
                               db='xiaoqing',
                               passwd='123456',
                               port=3306,
                               charset='utf8')
    except Exception as e:
        print (e)
    result_auto = None
    with conn.cursor() as cursor:
        sql = "select question,answer from xiaoqing.question_auto"
        try:
            cursor.execute(sql)
            result_auto = cursor.fetchall()
        except Exception as e:
            print (e)
    # print(result_auto)
    # cor_text_auto = [str(line).replace('\r','') for line in result_auto]
    # cor_text_auto = [str(line).replace('\n','') for line in cor_text_auto]

    with open(cor_auto_q, 'w+', encoding='utf-8') as cor:
        for sen in result_auto:
            cor.write(sen[0])
            cor.write('\r')

    with open(cor_auto_a, 'w+', encoding='utf-8') as cora:
        for sen in result_auto:
            cora.write(sen[1])
            # cora.write('\r')

    cor_text_list = list(open(cor_text, "r", encoding='utf-8').readlines())
    # jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')

    cor_seg = [list(jieba.cut(item, cut_all=False)) for item in cor_text_list]
    for sen_seg in cor_seg:
        for word in sen_seg:
            if word in stop_words.CHINESE_STOP_WORDS:
                sen_seg.remove(word)
        for label in stop_words.CHINESE_STOP_WORDS:
            if label in sen_seg:
                sen_seg.remove(label)

    cor_final = [' '.join(item) for item in cor_seg]
    with open(origin_cor_t_q, 'w+' , encoding = 'utf-8') as origin_cor:
        for words in cor_final:
            origin_cor.write(words)

    cor_text_list_a = list(open(cor_text_a, "r", encoding='utf-8').readlines())

    cor_seg_a = [list(jieba.cut(item, cut_all=False)) for item in cor_text_list_a]
    for sen_seg in cor_seg_a:
        for word in sen_seg:
            if word in stop_words.CHINESE_STOP_WORDS:
                sen_seg.remove(word)
        for label in stop_words.CHINESE_STOP_WORDS:
            if label in sen_seg:
                sen_seg.remove(label)

    cor_final_a = [' '.join(item) for item in cor_seg_a]
    with open(origin_cor_auto_q, 'w+' , encoding = 'utf-8') as origin_cor:
        for words in cor_final_a:
            origin_cor.write(words)


    def similarity(datapath):
        class MyCorpus(object):
            def __iter__(self):
                for line in open(datapath,'r',encoding='utf-8'):
                    yield line.split()

        Corp = MyCorpus()
        dictionary = corpora.Dictionary(Corp)
        output = open(vf.localPath + '/dictionary_and_corpus/dictionary_cor_t_q.pkl', 'wb')
        pickle.dump(dictionary, output)
        output.close()
        corpus = [dictionary.doc2bow(text) for text in Corp]

        tfidf = models.TfidfModel(corpus)
        output = open(vf.localPath + '/dictionary_and_corpus/tfidf_cor_t_q.pkl', 'wb')
        pickle.dump(tfidf, output)
        output.close()
        corpus_tfidf = tfidf[corpus]
        output = open(vf.localPath + '/dictionary_and_corpus/corpus_tfidf_cor_t_q.pkl', 'wb')
        pickle.dump(corpus_tfidf, output)
        output.close()

    similarity(datapath_t)

    def similarity1(datapath):
        class MyCorpus(object):
            def __iter__(self):
                for line in open(datapath,'r',encoding='utf-8'):
                    yield line.split()

        Corp = MyCorpus()
        dictionary = corpora.Dictionary(Corp)
        output = open(vf.localPath + '/dictionary_and_corpus/dictionary_cor_auto_q.pkl', 'wb')
        pickle.dump(dictionary, output)
        output.close()
        corpus = [dictionary.doc2bow(text) for text in Corp]

        tfidf = models.TfidfModel(corpus)
        output = open(vf.localPath + '/dictionary_and_corpus/tfidf_cor_auto_q.pkl', 'wb')
        pickle.dump(tfidf, output)
        output.close()
        corpus_tfidf = tfidf[corpus]
        output = open(vf.localPath + '/dictionary_and_corpus/corpus_tfidf_cor_auto_q.pkl', 'wb')
        pickle.dump(corpus_tfidf, output)
        output.close()

    similarity1(datapath_auto)

if __name__ == '__main__':
    update_tfidf()
