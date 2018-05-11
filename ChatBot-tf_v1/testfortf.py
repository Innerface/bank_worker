from LRclassifier import lr_classifier,sen_vector
import pandas as pd
import jieba
import VariableFunction as vf
jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic_former.txt')
input = '我要查余额'
columns_names = ['feature%s' % num for num in range(1, 101)]
input_sen_vec = sen_vector(input)
input_feature = pd.DataFrame([input_sen_vec], columns=columns_names)
classify_result = lr_classifier.predict(input_feature)[0]
print(classify_result)