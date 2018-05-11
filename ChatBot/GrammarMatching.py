from jpype import *
import pandas as pd
import numpy as np
import pickle
import VariableFunction as vf
# startJVM(getDefaultJVMPath(), "-Djava.class.path=/Users/ruofanwu/Beijing_Project/HanLP/hanlp-1.3.4.jar:/Users/ruofanwu/Beijing_Project/HanLP", "-Xms1g",
#          "-Xmx1g")
if not isJVMStarted():
    path1 = vf.localPath + '/hanlp-1.3.4-release/hanlp-1.3.4.jar'
    path2 = vf.localPath + '/hanlp-1.3.4-release'
    startJVM(getDefaultJVMPath(), "-Djava.class.path=%s:%s"%(path1,path2), "-Xms512m",
             "-Xmx512m")
HanLP = JClass('com.hankcs.hanlp.HanLP')

# For synonym
synonym_file = vf.localPath+'/dictionary_and_corpus/synonym_0809.txt'
with open(synonym_file,'r',encoding='utf-8') as syn:
    rawlist = [line.strip().split() for line in syn]
syn_dict = {str(item[0]):item[1:] for item in rawlist}

def sentence_segmetation(sentence):
    sentence_seg = str(HanLP.segment(sentence))
    seg_string = sentence_seg[1:-1].split(',')
    seg_word = [seg_string[i].rpartition('/')[0] for i in range(len(seg_string))]
    return seg_word


def tag_segmetation(sentence):
    sentence_seg = str(HanLP.segment(sentence))
    seg_string = sentence_seg[1:-1].split(',')
    seg_tag = [seg_string[i].rpartition('/')[2] for i in range(len(seg_string))]
    return seg_tag


# this function for delete same sentences in corpus, tol_list is tolerance list(for example:tol_list=[['的'],[' '],['”', '“'],['/']])
def delete_samequestion(corpus, tol_list):
    same_list = []
    for i in range(len(corpus) - 1):
        for j in range(i + 1, len(corpus)):
            seg_1 = sentence_segmetation(corpus[i])
            seg_2 = sentence_segmetation(corpus[j])
            if (list(set(seg_1) ^ set(seg_2)) in tol_list):
                same_list.append(corpus[j])
    new_question = list(set(corpus) ^ set(same_list))
    return new_question


# input sentence
# output parsing result and store it in dataframe
def sentence_parse_df(sentence):
    parse_list = str(HanLP.parseDependency(sentence))[:-1].split('\n')
    parse_row = [parse_list[i].split('\t') for i in range(len(parse_list))]
    parsing_df = pd.DataFrame(parse_row)
    parsing_df_1 = parsing_df[[0, 1, 6, 7]]
    column_name = ['序号', '分词', '词间关系', '标签']
    parsing_df_1.columns = column_name
    return parsing_df_1


# # transfer sentence to dictionary with desired grammer part
# def sentence_to_dic(sentence,label_type,type_list):
#     sentence=sentence.replace('（','(')
#     sentence=sentence.replace('）',')')
#     sentence_2=''
#     if('(' in sentence):
#         sentence_2=sentence.split('(')[1].split(')')[0]
#         sentence=sentence.split('(')[0]+sentence.split(')')[1]
#     parsing_table=sentence_parse_df(sentence)
#     label_list=parsing_table['标签'].values.tolist()
#     word_list_general=[]
#     for label_type_ in label_type:
#         word_list=[]
#         for label_type__ in label_type_:
#             for i,a in enumerate(label_list):
#                 if(a==label_type__):
#                     word_list.append(parsing_table.ix[i]['分词'])
#         word_list_general.append(word_list)
#     structure_dict=dict(zip(type_list,word_list_general))
#     if(len(sentence_2)>0):
#         structure_dict['a'].append(sentence_2)
#     return structure_dict

def sentence_to_dic(sentence, label_type, type_list, adv_list, synonym_dict):
    sentence = sentence.replace('（', '(')
    sentence = sentence.replace('）', ')')
    adv_case_ = []
    sentence_2 = ''
    if ('(' in sentence):
        sentence_2 = sentence.split('(')[1].split(')')[0]
        sentence = sentence.split('(')[0] + sentence.split(')')[1]
    for a in sum(synonym_dict.values(), []):
        if a in sentence:
            for key_ in synonym_dict.keys():
                if (a in synonym_dict[key_]):
                    adv_case_.append(key_)
                    sentence = sentence.replace(a, '')
    sentence_seg = sentence_segmetation(sentence)
    tag_seg = tag_segmetation(sentence)
    no_case = [i for i, a in enumerate(sentence_seg) if a == '不']
    # pronoun_case=[i for i,a in enumerate(tag_seg) if a in pronoun_list]
    adv_case_ = adv_case_ + [a for a in sentence_seg if a in adv_list]
    parsing_table = sentence_parse_df(sentence)
    label_list = parsing_table['标签'].values.tolist()
    word_list_general = []
    for label_type_ in label_type:
        word_list = []
        for label_type__ in label_type_:
            for i, a in enumerate(label_list):
                if (a == label_type__):
                    word_list.append(parsing_table.ix[i]['分词'])
        word_list_general.append(word_list)
    word_list_general.append(adv_case_)
    structure_dict = dict(zip(type_list, word_list_general))
    if (len(sentence_2) > 0):
        structure_dict['a'].append(sentence_2)
    for i in no_case:
        if (tag_seg[i + 1] == 'v'):
            structure_dict['a'].append('不')
            # for i in pronoun_case:
            # do something here
    # i=i
    return structure_dict


# calculate similarity between query and all_the_questions
# the score is got from sum of same(synonym) words number divided by sum of terms in query and question parsing dictionary
def similarity_score(questionpool, query_dict, synonym_dict, type_list, parsecolumn):
    distance_score = []
    for ii in questionpool.index:
        current_score = 0
        info = 0
        for parsingtype in type_list:
            info = info + len(set(questionpool[parsecolumn].ix[ii][parsingtype]) ^ set(query_dict[parsingtype]))
            current_score = current_score + len(
                set(questionpool[parsecolumn].ix[ii][parsingtype]).intersection(set(query_dict[parsingtype])))
            for i in range(len(query_dict[parsingtype])):
                if (query_dict[parsingtype][i] in synonym_dict):
                    for synonym in synonym_dict[query_dict[parsingtype][i]]:
                        if (synonym in questionpool[parsecolumn].ix[ii][parsingtype]):
                            current_score += 1
        current_score = current_score - info
        distance_score.append(current_score)
    #max_score = max(distance_score)
    questionpool2 = questionpool.copy()
    questionpool2['distance_score'] = distance_score
    questionpool2 = questionpool2.sort_values(by = 'distance_score',ascending=True)
    #max_index = [i for i, a in enumerate(distance_score) if a == max_score]
    max_index = questionpool2.index[:5]
    selected_list = [questionpool.index[a] for a in max_index]
    return selected_list

def GrammarMathcing(query, QA_base, label_type, type_list, synonym_dict, adv_list,parsecolumn):
    assert type(QA_base).__name__ == 'DataFrame','Input should be a pandas DataFrame!'
    query_dict = sentence_to_dic(query, label_type, type_list, adv_list, synonym_dict)
    return similarity_score(QA_base, query_dict, synonym_dict, type_list, parsecolumn)

def iden(string_raw,syn_dict):
    return string_raw

def disable(func):
    return iden

@disable
def synFilter(string_raw,syn_dict):
    string_syn = []
    for char_raw in string_raw:
        char_syn = [key for key, val in syn_dict.items() if char_raw in val]
        if char_raw != char_syn and len(char_syn) > 0:
            string_syn.append(char_syn[0])
        else:
            string_syn.append(char_raw)
    return string_syn

def main():
    '''
    a = pd.read_csv('datafile/new_question_list', sep='\t', encoding='utf-8')
    new_question_list = list(a['问题'][:5])
    question_all = pd.DataFrame(new_question_list)
    question_all.columns = ['问题']

    # read scenario list
    with open("datafile/dic_scenario.txt", 'r') as h:
        lines1 = h.readlines()
    product = []
    for i in range(len(lines1)):
        product.append(lines1[i].rpartition('\n')[0])

    # read service list
    with open("datafile/dic_service.txt", 'r') as h:
        lines = h.readlines()
    service = []
    for i in range(len(lines)):
        service.append(lines[i].rpartition('\n')[0])
    '''
    parsecolumn = 'question_parsing'
    # label_type is results we want from parsing
    label_type = [['主谓关系'], ['核心关系'], ['定中关系'], ['动宾关系', '前置宾语', '间宾关系']]
    # type_list is types we want corresponding label_type
    type_list = ['s', 'v', 'a', 'o', 'f']
    # synonym_dict is set of synonym
    synonym_dict = {'能否': ['是否可以']}

    adv_list = ['如何', '何时', '能否', '网上', '明细', '综合']
    # all parsing result to question_all table
    '''
    question_parsing_list = []
    for i in question_all.index:
        question_parsing_list.append(
            sentence_to_dic(question_all['问题'][i], label_type, type_list, adv_list, synonym_dict))
    question_all['解析'] = question_parsing_list
    '''
    # TEST PART

    # TEST all the original sentence
    QA_base_version = '2017-08-09'
    # Load QA base
    file = open('QA_parsed_new_{}.pickle'.format(QA_base_version),'rb')
    QA_base = pickle.load(file)
    new_question_list = list(QA_base['question'][:5])
    answer_list = []
    for i in range(len(new_question_list)):

        query = new_question_list[i]
        '''
        query_dict = sentence_to_dic(query, label_type, type_list, adv_list, synonym_dict)
        s = similarity_score(QA_base, query_dict, synonym_dict, type_list, parsecolumn='question_parsing')
        '''
        s = GrammarMathcing(query,QA_base,label_type, type_list, synonym_dict, adv_list, parsecolumn='question_parsing')
        answer_list.append(s)
    print(answer_list)
    a = 0
    ambiguous_list = []
    for i in range(len(answer_list)):
        if (len(answer_list[i]) > 1):
            a = a + 1
            ambiguous_list.append(answer_list[i])
    '''
    ambiguous_sentence_list = []
    for i in range(len(ambiguous_list)):
        ambiguous_sentence = []
        for j in range(len(ambiguous_list[i])):
            ambiguous_sentence.append(question_test1[ambiguous_list[i][j]])
        ambiguous_sentence_list.append(ambiguous_sentence)
    print(ambiguous_sentence_list)
    '''
    '''
    ss = pd.DataFrame(ambiguous_sentence_list)
    # a is number of ambiguous sentence, answer_list is query result, ambiguous_list is list of index of ambiguous sentence, ambiguous_sentence_list is list of pairs of ambiguous sentences
    with open('datafile/ambiguous_sentence_list.pickle', 'wb') as t:
        pickle.dump(ss, t)
    '''

if __name__ == '__main__':
    main()
