#coding=utf-8
import jieba
import re
import sys
from gensim import corpora
from gensim.similarities import Similarity

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

class Doc:
    def __init__(self,before,after):
        self.before = before
        self.after = after


    def split_questionFile(self,before, after):
        i = 0
        f_all = open(before, 'r')
        lines = f_all.readlines()
        f_aftersplit = open(after, 'w+')
        l = []
        for line in lines:
            j = str(i)
            line = j+line
            seg_list = list(jieba.cut(line))
            l.append(seg_list)
            i = i + 1
            f_aftersplit.write(" ".join(seg_list))
        f_aftersplit.close()
        f_all.close()
        return l

    def docsim(self,corp,string):
        #生成字典
        dictionary = corpora.Dictionary(corp)
        #生成向量
        corpus = [dictionary.doc2bow(text) for text in corp]
        similarity = Similarity('-Similarity-index',corpus,num_features = 600)
        test_str = list(jieba.cut(string))
        test_corpus = dictionary.doc2bow(test_str)
        similarity.num_best = 1
        return similarity[test_corpus][0][0]

    def judgement(self,lineNum,string_test):
        for line in corpora_guashi:
            if(line.startswith(lineNum)) or ('挂失' in string_test):
                return 'guashi'
        for line in corpora_chaxun:
            if(line.startswith(lineNum)) or ('查询' in string_test):
                return 'chaxun'
        for line in corpora_qita:
            if line.startswith(lineNum):
                return 'qita'
