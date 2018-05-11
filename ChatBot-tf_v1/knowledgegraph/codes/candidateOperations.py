# coding:utf-8

import sys
import importlib
importlib.reload(sys)
import jieba.posseg as pseg

def detect():
    setAll=set()
    with open('candidates2.txt','r') as f:
        for line in f:
            setAll.add(line.strip())
    setSpecial = set()
    with open('candidatesSmall.txt', 'r') as f:
        for line in f:
            setSpecial.add(line.strip())
    # with open('candidatesSmall.txt','w') as f:
    #     f.writelines([x+'\n' for x in setSpecial])
    print (len(setSpecial),len(setSpecial-setAll))


def candidates_process():
    """
    对实体候选词进行处理，得到符合条件的实体词词典。该词典同时用于jieba分词。
    :return:
    """
    exclude_list=[]
    with open(u'candidates_exclude.txt', 'r') as f:
        #将停用词排除出去
        for line in f:
            exclude_list.append(line.strip())
    words = set()
    with open(u'candidates2.txt', 'r') as f:
        #对候选实体列表进行初步筛选
        for line in f:
            words.add(line.strip().strip('#()').replace(' ','').replace('"','').replace('*','').lower())
    words=filter(lambda x:len(x)>3 and x not in exclude_list,words) #1个中文字符长度记为3
    words=filter(lambda x:is_legal_candidate(x),words)
    with open(u'candidates_add.txt', 'r') as f:
        #将人工指定一定是实体的词加入列表
        for line in f:
            retain_word=line.strip()
            if retain_word not in words:
                words.append(retain_word)
    with open(u'candidatesAll.txt','w') as f:
        f.writelines([x+'\n' for x in words])

def is_legal_candidate(sen):
    tmp = list(pseg.cut(sen))
    return tmp[-1].flag in ['l','Ng','n','nr','ns','nt','nz','vn','x'] #当前认定只要词组最后一个词为名词性，即保留成为实体可能


if __name__ == "__main__":
    # detect()
    candidates_process()
    print ("done")