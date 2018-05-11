from jpype import *
import jieba.posseg as pseg
import numpy as np
import pickle
from datetime import datetime
from GrammarMatching import synFilter,syn_dict
import itertools

#For recursive list unpacking
def is_iterable(i):
    return hasattr(i,'__iter__') & (type(i).__name__ != 'str')

def iterative_flatten(List):
    for item in List:
        if is_iterable(item):
            for sub_item in iterative_flatten(item):
                yield sub_item
        else:
            yield item

def flatten_iterable(to_flatten):
    return list(iterative_flatten(to_flatten))

def QuestionAdj(old_SO, corruption_old, new_SO, new_Ques, Ldict):
    '''
    Using jieba module to make POS tagging, and taking only POS information to reform the sentence
    Situation here is rather involved:
    (i) previous SO established, current missing.
    (ii) previous SO includes missing, current nothing
    (iii) previous SO includes missing, current involving completion
    '''
    jointChange = False
    missing_Index = None
    words = list(pseg.cut(new_Ques))
    #print([w for w,pos in words])
    outwords, outpos = [], []
    if not corruption_old:
        if new_SO.count(None) == 1:
            missing_Index = new_SO.index(None)
            new_SO_tmp = list(new_SO)
            new_SO_tmp[missing_Index] = old_SO[missing_Index]
            new_SO = tuple(new_SO_tmp)
        else:
            new_SO = old_SO
            jointChange = True
        for w, pos in words:
            if jointChange:
                if pos in ['r', 'rz']:
                    outwords.append([new_SO[0],new_SO[1]])
                else:
                    outwords.append(w)
            else:
                if missing_Index == 0:
                    if pos in ['r', 'rz']:
                        outwords.append(new_SO[0])
                    else:
                        outwords.append(w)
                elif w == new_SO[0]:
                    outwords.append([w,new_SO[1]])
                else:
                    outwords.append(w)
            outpos.append(pos)
        outwords = flatten_iterable(outwords)
        Corruption = False
    elif old_SO.count(None) == 1:
        missing_Index_old = old_SO.index(None)
        if new_SO.count(None) == 1:
            missing_Index = new_SO.index(None)
            if missing_Index == missing_Index_old:
                Corruption = True
            else:
                new_SO = tuple([[b for b in a if b != None][0] for a in zip(old_SO, new_SO)])
                for w, pos in words:
                    if missing_Index == 0:
                        if pos in ['r', 'rz']:
                            outwords.append(new_SO[0])
                        else:
                            outwords.append(w)
                    elif w == new_SO[0]:
                        outwords.append(w + new_SO[1])
                    else:
                        outwords.append(w)
                    outpos.append(pos)
                Corruption = False
        else:
            Corruption = True
            new_SO = old_SO
    # Flawed solution of ['No Source matching']
    elif old_SO != ['No Source matching'] and new_SO == ['No Source matching']:
        Corruption = True
        new_SO = old_SO
    else:
        Corruption = True
    '''
    if tuple(new_SO) not in Ldict:
        Corruption = True
        return [w for w,pos in words],['No Source matching'],Corruption
    '''
    # Currently no grammar steps involved, just segmenting and POS tagging
    # By default replace pronouns into SCENARIOS
    if Corruption:
        return [w for w,pos in words],new_SO,Corruption
    elif tuple(new_SO) not in Ldict:
        Corruption = True
        return [w for w,pos in words],['No Source matching'],Corruption
    else:
        return synFilter(outwords, syn_dict), new_SO, Corruption

if __name__=='__main__':
    old = ('信用卡','手续费')
    new = (None,'有效期')
    Ldict = [('信用卡', '手续费'), ('信用卡', '有效期'), ('白金卡', '喜马拉雅年费')]
    testquery = '那它的有效期呢?'
    testresult,adj_SO,Corruption = QuestionAdj(old,False,new,testquery,Ldict)
    print('Adjusted Question:',testresult,'\n','adj_SO:',adj_SO,'\n',"Corruption:",Corruption)
    old = ('信用卡', '手续费')
    new = ('白金卡', None)
    Ldict = [('信用卡', '手续费'), ('信用卡', '有效期'), ('白金卡', '手续费')]
    testquery = '那白金卡呢?'
    testresult,adj_SO, Corruption = QuestionAdj(old,False, new, testquery, Ldict)
    print('Adjusted Question:', testresult, '\n','adj_SO:',adj_SO,'\n', "Corruption:", Corruption)

    old = ('白金卡', '手续费')
    new = (None, '有效期')
    testquery = '那它的有效期呢?'
    testresult,adj_SO, Corruption = QuestionAdj(old,False, new, testquery, Ldict)
    print('Adjusted Question:', testresult, '\n','adj_SO:',adj_SO,'\n', "Corruption:", Corruption)

    old = ('白金卡', '手续费')
    new = (None, None)
    testquery = '那它怎么计算?'
    testresult,adj_SO, Corruption = QuestionAdj(old,False, new, testquery, Ldict)
    print('Adjusted Question:', testresult, '\n','adj_SO:',adj_SO,'\n', "Corruption:", Corruption)
