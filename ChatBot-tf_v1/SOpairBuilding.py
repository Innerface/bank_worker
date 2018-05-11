import pandas as pd
import pickle
from datetime import datetime
import jieba
import jieba.posseg as pseg
import re
from collections import Counter
import itertools
import pprint
import Levenshtein
from wordCalibration import sentencetree
from SOpair import buildSOpair,transfertoSO

'''
This script is GODDAMNED CRUCIAL
For SO-pair building, both with reference dictionaries created with pre-specified domain knowledge
Assisted with 3rd party search engine results to produce semantic synonyms
Currently Baidu is used
'''

jieba.load_userdict('dictionary_and_corpus/dic_for_jieba.txt')



'''
print(matchedresults.count(None),len(matchedresults))
with open('QA_parsed_new_{}.pickle'.format(str(datetime.today()).split()[0]), mode='wb') as f:
    pickle.dump(QA_base, f)
'''


def textFilter(q):
    # First remove white spaces
    q = re.sub(r"\s+", "", q, flags=re.UNICODE)
    if ('-' in q) or ('_' in q):
        # Baidu results contains a lot of 'source information' using '-' or '_' as marks,
        # Remove source info by extracting contents before the occurence of these signs
        q = re.match("(.*?)(-|_)", q).group().rstrip('_|-')
    qseg = list(pseg.cut(q))
    qfinal = []
    for w, pos in qseg:
        # Lots of words with no keyword meanings could be discarded
        # Currently POS tagging set is not strictly the ICTPOS3.0 set as listed in
        # https://gist.github.com/luw2007/6016931
        # but confined to the internal? setting in jieba
        # and further adjustments are possible were segmentation tool changed
        if not (pos.startswith(('r', 'u', 'p', 't','c','d','y')) or (pos in ['m', 'x','f']) or (w in ['是', '有'])):
            # POS tag is important for SO pair reordering, so combination of word and POS tag is performed
            qfinal.append('|'.join([w,pos]))
    return qfinal

#For recursive list unpacking
def is_iterable(i,packlist = False):
    '''
    Only unpack list
    '''
    if packlist:
        return hasattr(i, '__iter__') & (type(i).__name__ != 'str')
    else:
        return hasattr(i, '__iter__') & (type(i).__name__ == 'list')


def iterative_flatten(List,packlist=False):
    for item in List:
        if is_iterable(item,packlist):
            for sub_item in iterative_flatten(item,packlist):
                yield sub_item
        else:
            yield item

def flatten_iterable(to_flatten,packlist = False):
    return list(iterative_flatten(to_flatten,packlist))

def counterNormailzation(c,denom,Num):
    '''
    Input should be a Counter
    This normalization takes into account that words and their POS tags are concatenated
    So one word would have multiple potential POS tags, i.e.
    存款|n and 存款|v
    And current solution to such phenomenon is to compress all the word counts to its
    POS tags with most occurrence, no perfect, but reasonable
    '''
    #assert type(c).__name__ == 'Counter','Input should be a Counter!'
    result = []
    ref = []
    for w,ct in c:
        if w.split('|')[0] not in ref:
            result.append([w,ct])
            ref.append(w.split('|')[0])
        else:
            result[ref.index(w.split('|')[0])][1] += ct
    if Num == None:
        return {w: c / denom for w, c in result}
    else:
        return {w:c/denom for w,c in result[:Num]}

def naiveInOP(fun):
    def inOP(a,b):
        return a in b.keys()
    return inOP

@naiveInOP
def sim_Levenshtein(w,l,threshold = 0.95):
    '''
    This module should be taken EXTREME care
    Lots of corner cases resides inside
    And if threshold is not controlled at a rather high level
    You will never exhaust what the FUCK fucks you
    '''
    assert type(l).__name__ == 'dict','Input should be a dictionary!!!'
    include = False
    for ll in l.keys():
        score = Levenshtein.jaro_winkler(w,ll)
        if score > threshold:
            include = True
            if score < 1 and w not in l.keys():
                l[w] = l.pop(ll)
            break
    return include



def findorderdPair(sen,pairset):
    '''
    This is for intersecting sentence with specific pair
    WITH ORDER PRESERVATION!!!!!!!
    '''
    result = []
    # There are weird cases like
    # ('谷歌|nr', '谷歌|n')
    # Which is rather funny...
    pairdict = {p.split('|')[0]: p.split('|')[1] for p in pairset}
    ##########################
    #In case debug is needed
    #print(pairdict,sen)
    for s in sen:
        if sim_Levenshtein(s,pairdict) and s not in result:
            result.append(s)
            # This operation should be treated WITH CAUTION
            if len(result) == 2:break
    # If a noun is misplaced in the second entry, just pop it up
    ##########################
    # In case debug is needed
    #print(pairdict)
    if pairdict[result[0]] != pairdict[result[1]]:
        if pairdict[result[1]].startswith('n'):
            result = result[::-1]
    return tuple(result)

def normalizeAsPD(c):
    '''
    This is for normalizing a counter when one sentence has multiple potential pairs
    Could treat the output as a probability distribution over potential pairs
    '''
    if len(c) > 1:
        denom = sum([num for pair, num in c])
        return sorted([[pair, ct / denom] for pair, ct in c], key=lambda pair: -pair[1])
    else:
        return [c[0][0],1]



#print(QA_base.loc[0])

#print(QA_base['question_seg'][2907])

def buildPairFromQ(QA_base,baidu_dict,topNum = None):
    '''
    Both QA_base and baidu_dict are required to be a pandas dataframe
    '''
    j = 0
    qlen = len(baidu_dict.index)
    keywRaw = []
    # Stores 2-combination pairs of whole intersection
    keywIntersect = []
    keywFreq = []
    for i in QA_base.index:
        # Counter generation phase
        w_tobe_c = []
        k = 0
        while baidu_dict['question'][j] == QA_base['question'][i]:
            # print(j)
            q = textFilter(baidu_dict['title'][j])
            w_tobe_c.append(q)
            if j == qlen - 1:
                break
            else:
                j += 1
            k += 1
        # In case there would be missing from baidu results
        if k == 0:
            keywIntersect.append([])
            keywFreq.append(0)
            continue
        w_Counter = Counter(flatten_iterable(w_tobe_c)).most_common()
        w_Counter = counterNormailzation(w_Counter, k, topNum)
        tmpq = QA_base['question_seg'][i].split('|')[:-1]
        # Some specific words with appear as part of the combined word phrases
        # which serves as keyword in the target question, are scattered in the
        # Search results, needs to do some calibration w.r.t. word frequencies
        qTree = sentencetree(tmpq)
        w_Counter, _ = qTree.calibrate(w_Counter, lt=None)
        keywRaw.append(w_Counter)
        '''
        # These are past used solutions, OUTDATED
        tmpset1 = set(tmpq)
        tmpset2 = set([w.split('|')[0] for w,c in w_Counter.items()])
        tmpref = zip([w.split('|')[0] for w,c in w_Counter.items()],[w for w,c in w_Counter.items()])
        intersection_12 = tmpset1.intersection(tmpset2)
        interwithpos = set([w1 for w,w1 in tmpref if w in intersection_12])
        '''
        interwithpos = set(w_Counter.keys())
        candiPairs = list(itertools.combinations(interwithpos, 2))
        if len(candiPairs) > 0:
            localkeyw = []
            for pair in candiPairs:
                #if len(findorderdPair(tmpq, pair)) > 2: print(tmpq, pair, '\n', findorderdPair(tmpq, pair))
                localkeyw.append(findorderdPair(tmpq, pair))
            keywIntersect.append(localkeyw)
            keywFreq.append(len(interwithpos))
        else:
            keywIntersect.append([])
            keywFreq.append(0)
        i += 1
    return keywIntersect,keywFreq
'''
def buildPairFromR(QA_base,baidu_dict,topNum = 10):
    ''''''
    Both QA_base and baidu_dict are required to be a pandas dataframe
    ''''''
    j = 0
    qlen = len(baidu_dict.index)
    keywRaw = []
    # Stores 2-combination pairs of whole intersection
    keywIntersect = []
    keywFreq = []
    for i in QA_base.index:
        # Counter generation phase
        w_tobe_c = []
        k = 0
        while baidu_dict['question'][j] == QA_base['question'][i]:
            # print(j)
            q = textFilter(baidu_dict['title'][j])
            w_tobe_c.append(q)
            if j == qlen - 1:
                break
            else:
                j += 1
            k += 1
        w_Counter = Counter(flatten_iterable(w_tobe_c)).most_common()
        w_Counter = counterNormailzation(w_Counter, k, topNum)
        tmpq = QA_base['question_seg'][i].split('|')[:-1]
        # Some specific words with appear as part of the combined word phrases
        # which serves as keyword in the target question, are scattered in the
        # Search results, needs to do some calibration w.r.t. word frequencies
        qTree = sentencetree(tmpq)
        w_Counter, _ = qTree.calibrate(w_Counter, lt=None)
        keywRaw.append(w_Counter)
        ''''''
        # These are past used solutions, OUTDATED
        tmpset1 = set(tmpq)
        tmpset2 = set([w.split('|')[0] for w,c in w_Counter.items()])
        tmpref = zip([w.split('|')[0] for w,c in w_Counter.items()],[w for w,c in w_Counter.items()])
        intersection_12 = tmpset1.intersection(tmpset2)
        interwithpos = set([w1 for w,w1 in tmpref if w in intersection_12])
        ''''''
        interwithpos = set(w_Counter.keys())
        candiPairs = list(itertools.combinations(interwithpos, 2))
        if len(candiPairs) > 0:
            localkeyw = []
            for pair in candiPairs:
                if len(findorderdPair(tmpq, pair)) > 2: print(tmpq, pair, '\n', findorderdPair(tmpq, pair))
                localkeyw.append(findorderdPair(tmpq, pair))
            keywIntersect.append(localkeyw)
            keywFreq.append(len(interwithpos))
        else:
            keywIntersect.append([])
            keywFreq.append(0)
        i += 1
    return keywIntersect,keywFreq
'''

#print(Counter(keywFreq))
#keywFlat = flatten_iterable(keywIntersect)

#keywCounter = Counter(keywFlat)
#pp.pprint(keywCounter)


#ItemSet = set(flatten_iterable(keywIntersect,packlist=True))
#pp.pprint(keywIntersect)
#pp.pprint(ItemSet)

def countAndReorder(keywIntersect):
    keywFlat = flatten_iterable(keywIntersect)
    # This counter is a base for output a probability distribution over multiple matched SO pairs
    keywCounter = Counter(keywFlat)
    del keywFlat
    ItemSet = set(flatten_iterable(keywIntersect, packlist=True))
    # OrderRule is a dictionary that contains order info of
    # SINGULAR WORDS
    OrderRule = {}
    for item in ItemSet:
        count = [0, 0]
        for keyw, keyc in dict(keywCounter).items():
            if item in keyw:
                count[keyw.index(item)] += keyc
        mind = count.index(max(count))
        OrderRule[item] = (mind, count)
    # Currently apply a rule of
    # UNIVERSALLY MOST TO THE LEFT
    keyw_Final = []
    for keywords in keywIntersect:
        local_Final = []
        if len(keywords) == 0:
            keyw_Final.append(None)
            continue
        for keyword in keywords:
            order_raw = flatten_iterable([[num for k, num in OrderRule.items() if k == item] for item in keyword])
            count_ = [c for w, c in dict(keywCounter).items() if set(keyword) == set(w)]
            if order_raw[0][0] > order_raw[1][0]:
                local_Final.append([keyword[::-1], count_[0]])
            elif order_raw[0][0] == order_raw[1][0]:
                if order_raw[0][1][order_raw[0][0]] < order_raw[1][1][order_raw[1][0]]:
                    local_Final.append([keyword[::-1], count_[0]])
                else:
                    local_Final.append([keyword, count_[0]])
            else:
                local_Final.append([keyword, count_[0]])
        keyw_Final.append(normalizeAsPD(local_Final))
    return keyw_Final

def itermatch(w,key):
    match = []
    matchlevel = []
    ind = 0
    for ww in w:
        for i in range(len(key)):
            if ww in key[i]:
                match.append(ind)
                matchlevel.append(i+1)
                break
        ind += 1
    return match,matchlevel

def filterAndReorder(keywIntersect,levelset):
    '''
    This is for situations where we've already had Scenario dictionary
    But want to get the services ourselves since matching issue is troublesome with human provided ones
    '''
    keyw_Final = []
    for keywords in keywIntersect:
        # Retain the deepest level finded
        max_level = 0
        localmatch = []
        for keyword in keywords:
            match,matchlevel = itermatch(keyword,levelset)
            if len(match) == 1:
                if matchlevel[0] < max_level:
                    continue
                if matchlevel[0] == max_level:
                    if match[0] == 0:
                        localmatch.append([keyword,matchlevel[0]])
                    else:
                        localmatch.append([keyword[::-1],matchlevel[0]])
                else:
                    max_level = matchlevel[0]
                    if match[0] == 0:
                        localmatch.append([keyword,matchlevel[0]])
                    else:
                        localmatch.append([keyword[::-1],matchlevel[0]])
        localmatch = [kw for kw,lv in localmatch if lv == max_level]
        keyw_Final.append(localmatch)
    keywFlat = flatten_iterable(keyw_Final)
    # This counter is a base for output a probability distribution over multiple matched SO pairs
    keywCounter = Counter(keywFlat)
    del keywFlat
    keyw_Output = []
    for keywords in keyw_Final:
        local_Final = []
        if len(keywords) == 0:
            keyw_Output.append(None)
            continue
        for keyword in keywords:
            count_ = [c for w, c in dict(keywCounter).items() if set(keyword) == set(w)]
            local_Final.append([keyword, count_[0]])
        keyw_Output.append(normalizeAsPD(local_Final))
    return keyw_Output




#print(OrderRule)
#print(OrderRule['手机'],OrderRule['信用卡'])

def ordermatching(cand,ref,cname):
    '''
    O(n^2) solution, kinda dumb
    '''
    pB = 0
    qlen = len(cand.index)
    rawind = set(cand.index)
    result = pd.DataFrame(columns=tuple(cand))
    for i in ref.index:
        buffer = set()
        for j in rawind:
            if j == 0: match_last = False
            else:match_last = cand[cname][j-1] == ref[cname][i]
            match_this = cand[cname][j] == ref[cname][i]
            if not match_this and match_last:
                break
            if match_this or match_last:
                result.loc[pB] = cand.loc[j]
                if j == qlen - 1:
                    break
                pB += 1
                buffer.add(j)
        rawind = rawind - buffer
        i += 1
    return result

def extractInfo(rawlist,InD):
    '''
    Helper for extract items from built So pairs
    '''
    outlist = []
    for ks in rawlist:
        if ks == None:
            continue
        elif type(ks[0]).__name__ == 'tuple':
            if len(ks[0][1]) > 1:
                if InD == None:
                    outlist.append(ks[0])
                else:
                    outlist.append(ks[0][InD])
        else:
            for k in ks:
                if len(k[0][1]) > 1:
                    if InD == None:
                        outlist.append(k[0])
                    else:
                        outlist.append(k[0][InD])
    return outlist

def calibrateSO(pref,keyw):
    for ks in keyw:
        if ks == None: continue
        elif type(ks[0]).__name__ == 'tuple':
            if ks[0] not in pref:
                _ = ks.pop()
                ks.append(None)
        else:
            for k in ks:
                if k[0] not in pref:
                    ks.remove(k)
            # Could add an additional normalization step later

def calibrateQAwithSO(QA_base,keyw,cname):
    '''
    QA_base: MUTABLE pandas dataframe!
    keyw: MUTABLE list
    '''
    pairName = cname[-1]
    outQA = pd.DataFrame()
    for i in range(len(keyw)):
        tmpdf = pd.DataFrame()
        if keyw[i] == None:
            tmpdf = tmpdf.append(QA_base.loc[i])
            tmpdf[pairName] = [None]
        elif type(keyw[i][0]).__name__ == 'tuple':
            tmpdf = tmpdf.append(QA_base.loc[i])
            tmpdf[pairName] = [keyw[i][0]]
        else:
            localkey = []
            for j in range(len(keyw[i])):
                tmpdf = tmpdf.append(QA_base.loc[i])
                localkey.append(keyw[i][j][0])
            tmpdf[pairName] = localkey
        outQA = outQA.append(tmpdf,ignore_index=True)
    return outQA

def calibrateSwithSO():
    pass

def calibrateOwithSO():
    pass

if __name__ == '__main__':
    QA_base_version = '2017-08-17'
    pp = pprint.PrettyPrinter(indent=4)

    file = open('QA_base/QA_parsed_new_{}.pickle'.format(QA_base_version), 'rb')
    QA_base = pickle.load(file)
    print(QA_base.index)
    '''
    # Naive test phase, using predefined SO pair dictionary
    # Requires huge human effort
    SO_df = pd.read_csv('SOpair_candidates.csv', encoding='utf-8')
    SO_list = [(s, o) for s, o in zip(SO_df['场景'], SO_df['业务'])]

    S_df = pd.read_csv('Scenario.csv', encoding='utf-8')
    S_df.columns = ['Node']
    S_df['FatherNode'] = ['ROOT' for i in S_df['Node']]
    O_df = pd.read_csv('Operation.csv', encoding='utf-8')
    O_df.columns = ['Node']
    O_df['FatherNode'] = ['ROOT' for i in O_df['Node']]
    M_df = pd.read_csv('SO_Mapping.csv', encoding='utf-8')
    L_dict = [(a, b) for a, b in zip(M_df['场景'], M_df['业务'])]
    
    matchedresults = []
    for q in QA_base['question_seg']:
        q = q.split('|')[:-1]
        localmatch = []
        for so in L_dict:
            match = set(q).intersection(set(so))
            if len(match) == 2:
                localmatch.append(match)
        if len(localmatch) > 0:
            # print(q,'\n',localmatch)
            matchedresults.append(localmatch)
        else:
            matchedresults.append(None)

    QA_base['SO_pair_precise'] = matchedresults
    '''

    file = open('baidu_dict.pickle', 'rb')
    baidu_dict = pickle.load(file)


    '''
    # This part is for reading from raw baidu results and apply order calibration
    baidu_dict = pd.read_csv('from_baidu_0817.csv')
    #print(len(baidu_dict))
    #baidu_dict.to_csv('baidu_dict_ordered.csv', encoding='utf-8', sep=',', line_terminator='\n')
    tstart = datetime.now()
    baidu_dict = ordermatching(baidu_dict,QA_base,'question')
    with open('baidu_dict.pickle',mode='wb') as f:
        pickle.dump(baidu_dict,f)
    print('elapsed time: {}'.format(datetime.now() - tstart))
    '''

    keywIntersect, _ = buildPairFromQ(QA_base, baidu_dict)
    print('Build phase done')
    #QA_base['Guessed_SO_Pair'] = countAndReorder(keywIntersect)
    Sdict = pd.read_csv('SO_dicts/Sdict_raw_0817.csv', encoding='utf-8').fillna('')
    Sdict, levelSet = transfertoSO(Sdict)
    keyw_Final = filterAndReorder(keywIntersect,levelSet)
    print('Calibration: phase I done')
    # Extract service list from final version of SO pairs
    OpList = pd.DataFrame(flatten_iterable(extractInfo(keyw_Final,InD=1)),columns=['Op_1st_Level'])
    # pp.pprint(Counter(flatten_iterable(ServiceList)))

    Odict,_ = transfertoSO(OpList)
    pair_Final = set(extractInfo(keyw_Final,InD=None))
    calibrateSO(pair_Final,keyw_Final)
    print('Calibration: phase II done')
    # Final calibration of QA_base with SO pairs
    cname = list(QA_base)
    cname.append('Guessed_SO_Pair')
    QA_base = calibrateQAwithSO(QA_base,keyw_Final,cname)
    print('Calibration: phase III done')
    print(QA_base[:10],QA_base.index)
    SO_Mapping = pd.DataFrame()
    SO_Mapping['S_Side'] = [p[0] for p in pair_Final]
    SO_Mapping['O_Side'] = [p[1] for p in pair_Final]
    # Save SO pair info
    Sdict.to_csv('SO_dicts/Sdict_{}.csv'.format(str(datetime.today()).split()[0]),encoding='utf-8', index=False,
                 line_terminator='\n')
    Odict.to_csv('SO_dicts/Odict_{}.csv'.format(str(datetime.today()).split()[0]),encoding='utf-8',index=False, line_terminator='\n')
    SO_Mapping.to_csv('SO_dicts/Mapping_{}.csv'.format(str(datetime.today()).split()[0]),encoding='utf-8',index=False,
                      line_terminator='\n')
    #pp.pprint(Odict)
    del keywIntersect
    '''
    QA_base = QA_base.drop(['answer', 'question_parsing', 'SO_pair'], axis=1)
    QA_base.to_csv('Guessed_SO_Pair.csv', encoding='utf-8', sep=',', line_terminator='\n')
    '''
    with open('QA_base/QA_with_pair_{}.pickle'.format(str(datetime.today()).split()[0]),mode='wb') as f:
        pickle.dump(QA_base,f)

