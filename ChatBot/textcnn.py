# coding:utf-8
import tensorflow as tf
import numpy as np
import data_helpers
import jieba
import stop_words
import train
from tensorflow.contrib import learn
import VariableFunction as vf


jieba.load_userdict(vf.localPath + '/dictionary_and_corpus/dic.txt')


def remove_stop_word(sentence):
    for words in sentence:
        if words in stop_words.CHINESE_STOP_WORDS:
            sentence.remove(words)
    for label in stop_words.CHINESE_STOP_WORDS:
        if label in sentence:
            sentence.remove(label)
    return sentence

def cnnclassifier(question):
    x_text, y = data_helpers.load_data_and_labels(vf.localPath + '/positive_feature_list',
                                                  vf.localPath + '/negative_feature_list')

    ques = question
    sen_seg = list(jieba.cut(ques, cut_all=False))
    sen_seg = [' '.join(remove_stop_word(sen_seg))]
    # Build vocabulary
    max_document_length = max([len(x.split(" ")) for x in x_text])
    vocab_processor = learn.preprocessing.VocabularyProcessor(max_document_length)
    ques_x = np.array(list(vocab_processor.fit_transform(sen_seg)))

    with tf.Session(graph=train.g2) as sess:
        saver = tf.train.Saver()  # 'Saver' misnomer! Better: Persister!
        saver.restore(sess, vf.localPath + "/checkpoint_all")
        result = sess.run(train.cnn.predictions, feed_dict={train.cnn.input_x: np.array([ques_x[0]]),
                                                            train.cnn.dropout_keep_prob: 1.0})
        return result[0]



if __name__ == '__main__':
    print(cnnclassifier('信用卡'))
    print(cnnclassifier('储蓄卡'))
    print(cnnclassifier('年费'))
    print(cnnclassifier('我要办理挂失'))
    print(cnnclassifier('什么是信用卡有效期'))
