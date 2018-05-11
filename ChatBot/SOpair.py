import pandas as pd
import pickle
import itertools
import random

def getchildList(Node,DF):
    tmplayer = list(DF['Node'][DF['FatherNode'] == Node])
    if len(tmplayer) == 0:
        yield None
    for node in tmplayer:
        yield node
        for item in getchildList(node,DF):
            yield item

def getfatherList(Node,DF):
    tmp = DF['FatherNode'][DF['Node'] == Node]
    for node in tmp:
        yield node
        for item in getfatherList(node,DF):
            yield item

def buildSOpair(Question,Sdict,Odict,Ldict,RD = True):
    '''
    First, identify operation/service item, than the scenario and build the SOpair or throw ambiguity corruption
    Currently both scenario and operation allows to possess a fused structure
    '''
    # Question query should be segmented, get raw pair via EXACT keyword matching
    Scand = set(Question).intersection(Sdict['Node'])
    Ocand = set(Question).intersection(Odict['Node'])
    # Having only one key is completable in multi-round scenarios
    if not (len(Scand) > 0) & (len(Ocand) > 0):
        Corruption = True
        Schoice = random.choice(list(Scand)) if len(Scand) > 0 else None
        Ochoice = random.choice(list(Ocand)) if len(Ocand) > 0 else None
        return [Schoice,Ochoice],Corruption
    ExactMatch,VagueMatch = [],[]
    for s,o in itertools.product(Scand,Ocand):
        if (s,o) in Ldict:
            ExactMatch.append((s,o))
        else:
            SChild = set(filter(None.__ne__, getchildList(s,Sdict)))
            Sfather = set(filter(lambda x: x != 'ROOT', getfatherList(s,Sdict)))
            OChild = set(filter(None.__ne__, getchildList(o,Odict)))
            Ofather = set(filter(lambda x: x != 'ROOT', getfatherList(o,Odict)))
            for S,O in itertools.product(set(SChild).union(Sfather),set(OChild).union(Ofather)):
                if (S,O) in Ldict:
                    VagueMatch.append((S,O))
    if len(ExactMatch) > 0:
        Corruption = False
        if RD:
            return list(random.choice(ExactMatch)), Corruption
        else:
            return ExactMatch,Corruption
    elif len(VagueMatch) == 1:
        Corruption = False
        return VagueMatch,Corruption
    elif len(VagueMatch) > 0:
        Corruption = True
        return VagueMatch, Corruption
    else:
        Corruption = True
        # This module should be implemented a probablistic classification model to infer the "Hidden" intentions
        # To be constructed in further iterations




        return ['No Source matching'],Corruption
        # return [Scand[0],None],Corruption

def guidedinfoCompletion(SO_pair):
    '''
    Currently the solution is purely based on SO_pair, and no side info about query is used
    '''
    if SO_pair == ['No Source matching']:
        return '您的问题不在我们的业务范围内:)'
    if SO_pair.count(None) == 2:
        return '请您再问清楚一点'
    missing_Index = SO_pair.index(None)
    if missing_Index == 0:
        return '您是想问哪一种产品的{}相关业务'.format(SO_pair[1])
    else:
        return '您是想问{}的哪一种业务'.format(SO_pair[0])

def transfertoSO(rawdict):
    '''
    Input should be a DataFrame
    With its inclusion relation defined as right \subset left
    Default 3-column table is used
    '''
    result = pd.DataFrame(columns=['Node','Depth','FatherNode'])
    clist = list(rawdict)
    level = []
    for _ in range(len(clist)):
        level.append([])
    for i in rawdict.index:
        # Remove empty entries and pop to the left
        nodes = ' '.join(list(rawdict.loc[i])).split()
        c = 0
        for node in nodes:
            if node not in level[c]:
                level[c].append(node)
                if c == 0:
                    result = result.append(pd.DataFrame([[node,1,'ROOT']],columns=['Node','Depth','FatherNode']),
                                           ignore_index=True)
                else:
                    result = result.append(pd.DataFrame([[node, c+1, node_last]], columns=['Node', 'Depth', 'FatherNode']),
                                           ignore_index=True)
                node_last = node
            c += 1
    return result,level

if __name__ == '__main__':
    # Some testing
    '''
    Dic1 = {'Node':['卡','储蓄卡','信用卡','普卡','金卡','白金卡'],
            'Depth':[1,2,2,3,3,3],
            'FatherNode':['ROOT','卡','卡','信用卡','信用卡','信用卡']}
    Dic1_df = pd.DataFrame(Dic1)
    Dic2 = {'Node': ['费用','年费','手续费','北京年费','上海年费','喜马拉雅年费'],
            'Depth': [1, 2, 2, 3, 3, 3],
            'FatherNode': ['ROOT', '费用', '费用', '年费', '年费', '年费']}
    Dic2_df = pd.DataFrame(Dic2)
    test = list(filter(None.__ne__, getchildList('卡',Dic1_df)))
    test2 = set(filter(lambda x:x!='ROOT',getfatherList('上海年费',Dic2_df)))
    print(test,test2)
    # Now test relationship matching
    Ldict = [('信用卡','手续费'),('金卡','北京年费'),('白金卡','喜马拉雅年费')]
    testQuery_0 = ['信用卡', '有', '手续费', '吗']
    result, Corruption = buildSOpair(testQuery_0, Sdict=Dic1_df, Odict=Dic2_df, Ldict=Ldict)
    print('Suspected pairs:', result, '\n', 'Corruption Flag:', Corruption)
    testQuery_1 = ['我','卡','年费','多少']
    result,Corruption = buildSOpair(testQuery_1,Sdict=Dic1_df,Odict=Dic2_df,Ldict=Ldict)
    print('Suspected pairs:',result,'\n','Corruption Flag:',Corruption)
    testQuery_2 = ['最近', '天气', '好热', '啊']
    result, Corruption = buildSOpair(testQuery_2, Sdict=Dic1_df, Odict=Dic2_df, Ldict=Ldict)
    print('Suspected pairs:', result, '\n', 'Corruption Flag:', Corruption)
    testQuery_3 = ['我','卡','没','了']
    result, Corruption = buildSOpair(testQuery_3, Sdict=Dic1_df, Odict=Dic2_df, Ldict=Ldict)
    print('Suspected pairs:', result, '\n', 'Corruption Flag:', Corruption)
    '''
    QA_base_version = '2017-08-18'
    S_df = pd.read_csv('SO_dicts/Sdict_{}.csv'.format(QA_base_version), encoding='utf-8')
    O_df = pd.read_csv('SO_dicts/Odict_{}.csv'.format(QA_base_version), encoding='utf-8')
    M_df = pd.read_csv('SO_dicts/Mapping_{}.csv'.format(QA_base_version), encoding='utf-8')
    L_dict = [(a, b) for a, b in zip(M_df['S_Side'], M_df['O_Side'])]
    #Script for building a Sdict from source
    '''
    Sdict = pd.read_csv('Sdict_0817.csv',encoding='utf-8').fillna('')
    Sdict,levelSet = transfertoSO(Sdict)
    print(levelSet[0])
    '''
    print(S_df[S_df['Node'] == '存款'])
    print(len(S_df))
    S_df = S_df[S_df['Node'] != S_df['FatherNode']]
    print(len(S_df))
    #print(O_df[O_df['Node'] == '利率'])
    #print(S_df[S_df['Node'] == '单位活期存款'])
    # testQuery_1 = ['存款', '利率', '是', '多少']
    testQuery_1 = ['白金卡', '金卡', '区别', '多少']
    #print(list(getfatherList('存款',S_df)))
    #print(list(getchildList('存款',S_df)))
    result, Corruption = buildSOpair(testQuery_1, Sdict=S_df, Odict=O_df, Ldict=L_dict)
    print(result)
