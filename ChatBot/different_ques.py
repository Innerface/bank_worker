# coding:utf-8
import jieba
import pandas as pd
import VariableFunction as vf

# 不同城市的卡看到的理财产品是否一样
# 封闭式基金是否可以像开放式基金一样，选择“分红方式”？
# 贷记卡与准贷记卡的主要区别
# 信用卡小M贷和信用卡分期付款的业务区别
# 付款类保函和履约保函的区别
# 保函有种类区别？
# 交行Ⅰ、Ⅱ、Ⅲ类账户有何区别

# localPath = '/Users/wgh/PycharmProjects/test.py'
jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')
different_similarity = ['的区别', '有什么不同', '哪里不一样', '有什么不一样', '一样吗', '是否一样', '有哪些区别', '的不同',
                        '的主要区别', '有什么区别', '有啥区别', '有啥不同']
operation_ques = pd.read_excel(vf.localPath + '/pairdic.xlsx', header=None)
dic1 = []
dic2 = []
for i in [1,2,3,4]:
    for words in operation_ques[i]:
        dic1.append(words)
for words in operation_ques[5]:
    dic2.append(words)
dic1 = set(dic1)
dic2 = set(dic2)
with open(vf.localPath + '/dic1.txt', 'w+', encoding='utf-8') as dic:
    for words in dic1:
        dic.write(str(words))
        dic.write('\r')
with open(vf.localPath + '/dic2.txt', 'w+', encoding='utf-8') as dic:
    for words in dic2:
        dic.write(str(words))
        dic.write('\r')

def diff_ques(question):
    sen_seg = list(jieba.cut(question, cut_all=False))
    list_senario = []
    list_operation = []
    for item in dic1:
        if str(item) in sen_seg:
            list_senario.append(str(item))
            sen_seg.remove(str(item))
    for item in dic2:
        if str(item) in sen_seg:
            list_operation.append(str(item))
            sen_seg.remove(str(item))
    question_list = []
    if list_senario and list_operation:
        for word_senario in list_senario:
            for word_operation in list_operation:
                question_list.append('%s的%s是什么'%(str(word_senario), str(word_operation)))
    elif list_operation:
        for word_operation in list_operation:
            question_list.append('%s是什么' % str(word_operation))
    elif list_senario:
        for word_senario in list_senario:
            question_list.append('%s是什么' % str(word_senario))
    print (question_list)
    return question_list

if __name__ == '__main__':
    ques = '协定存款和个人贷款的区别是什么'
    diff_ques(ques)
    ques = '封闭式基金是否可以像开放式基金一样，选择“分红方式”？'
    diff_ques(ques)
    ques = '金卡、普卡和白金卡的额度一样吗'
    diff_ques(ques)
    ques = '信用卡小M贷和信用卡分期付款的业务区别'
    diff_ques(ques)
    ques = '付款类保函和履约保函的区别'
    diff_ques(ques)
    ques = '信用卡和储蓄卡的区别是什么'
    diff_ques(ques)
    ques = '贷记卡和准贷记卡的区别是什么'
    diff_ques(ques)

