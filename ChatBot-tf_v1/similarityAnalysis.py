import jieba
import jieba.posseg as pseg
import sys
import re
import time,datetime
import Levenshtein

# print Levenshtein.distance('信用类贷款'.decode('utf-8'),'信用合同贷款'.decode('utf-8'))
# print Levenshtein.jaro_winkler('信用类贷款'.decode('utf-8'),'信用合同贷款'.decode('utf-8'))

def similarityOperation(ques):

    dic = open(sys.path[0] + '/dic_former.txt', 'r', encoding='utf-8')

    ques_segment = jieba.cut(ques, cut_all= False)
    ques_segment_all = []
    for word_segment in ques_segment:
        print(word_segment)
        ques_segment_all.append(word_segment)

    answer_value = {}
    answer_value['label'] = []

    standardWord = []
    for word in dic:
        # print word
        word_list = word.split(' ')
        # print word_list
        standardWord.append(word_list[0])
        # print word_list[0]

    ##基于jaro距离计算ques中每个词与词库中的词的距离，当
    similarity_word_list = {}
    i = 1
    for word_dic in standardWord:
        word_similarity = []
        for word_ques in ques:
            if word_ques == word_dic:
                answer_value['label'].append(word_dic)
            elif Levenshtein.jaro_winkler(word_dic, word_ques) > 0.8:
                similarity_word_list[i] = [word_dic, word_ques]
                i +=1
                answer_value['label'].append(word_dic)

    if i == 1:
        for word_dic in standardWord:
            word_dic_segment = jieba.cut(word_dic, cut_all = False)
            word_dic_segment_list = []
            for word_dic_part in word_dic_segment:
                word_dic_segment_list.append(word_dic_part)

            len_word_dic_seg = len(word_dic_segment_list)

            intersect_list = list((set(ques_segment_all).union(set(word_dic_segment_list))) ^ (set(ques_segment_all) ^ set(word_dic_segment_list)))

            if float(len(intersect_list))/float(len_word_dic_seg) >= 0.6:
                answer_value['label'].append(word_dic)

    answer_value['similarity'] = similarity_word_list

    return answer_value

ques1 = '我想办理人房屋抵押消费贷款'
ques2 = '个人房屋抵押综合消费贷款'
ques3 = ' '
result = similarityOperation(ques1)
print(Levenshtein.jaro_winkler('我是一个人','我是一条狗'))
print(result['label'][0])
fenci = jieba.cut('个人房屋抵押综合消费贷款')
for word in fenci:
    print(word)









