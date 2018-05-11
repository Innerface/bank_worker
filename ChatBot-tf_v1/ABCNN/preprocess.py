import numpy as np
import nltk
import gensim
import jieba
import pandas as pd
import pickle
import VariableFunction as vf

'''
class Word2Vec():
    def __init__(self):
        # Load Google's pre-trained Word2Vec model.
        self.model = gensim.models.KeyedVectors.load_word2vec_format('./wiki.zh.vec',
                                                                     binary=False)
        self.unknowns = np.random.uniform(-0.01, 0.01, 300).astype("float32")

    def get(self, word):
        if word not in self.model.vocab:
            return self.unknowns
        else:
            return self.model.word_vec(word)
'''

class Word2Vec():
    def __init__(self):
        # Load Google's pre-trained Word2Vec model.
        with open(vf.localPath + '/word2vec/word_vector.pickle', 'rb') as f:
            wv = pickle.load(f)
        with open(vf.localPath + '/word2vec/word_dictionary.pickle', 'rb') as f:
            dictionary = pickle.load(f)
        self.model = wv
        self.dictionary = dictionary

    def get(self, word):
        if word not in self.dictionary.keys():
            return self.model[self.dictionary['UNK']]
        else:
            return self.model[self.dictionary[word]]


class Data():
    def __init__(self, word2vec, max_len=0):
        self.s1s, self.s2s, self.labels, self.features = [], [], [], []
        self.index, self.max_len, self.word2vec = 0, max_len, word2vec

    def open_file(self,mode):
        pass

    def is_available(self):
        if self.index < self.data_size:
            return True
        else:
            return False

    def reset_index(self):
        self.index = 0

    def next(self):
        if (self.is_available()):
            self.index += 1
            return self.data[self.index - 1]
        else:
            return

    def next_batch(self, batch_size, mode):
        batch_size = min(self.data_size - self.index, batch_size)
        s1_mats, s2_mats = [], []

        for i in range(batch_size):
            s1 = self.s1s[self.index + i]
            s2 = self.s2s[self.index + i]

            # [1, d0, s]
            s1_mats.append(np.expand_dims(np.pad(np.column_stack([self.word2vec.get(w) for w in s1]),
                                                 [[0, 0], [0, self.max_len - len(s1)]],
                                                 "constant"), axis=0))

            s2_mats.append(np.expand_dims(np.pad(np.column_stack([self.word2vec.get(w) for w in s2]),
                                                 [[0, 0], [0, self.max_len - len(s2)]],
                                                 "constant"), axis=0))

        # [batch_size, d0, s]
        batch_s1s = np.concatenate(s1_mats, axis=0)
        batch_s2s = np.concatenate(s2_mats, axis=0)
        if mode == 'training':
            batch_labels = self.labels[self.index:self.index + batch_size]
            batch_features = self.features[self.index:self.index + batch_size]
            self.index += batch_size
            return batch_s1s, batch_s2s, batch_labels, batch_features
        else:
            batch_features = self.features[self.index:self.index + batch_size]
            self.index += batch_size
            return batch_s1s, batch_s2s,  batch_features


class MSRP(Data):
    def open_file(self,mode,Query = None,QA_base = None):
        
        if(mode=='training'):       
            df = pd.read_pickle("./data/training_set")
            for i in range(len(df['pair'])):
                label=int(df['class'][i])
                s1 = list(jieba.cut(df['pair'][i][0]))
                s2 = list(jieba.cut(df['pair'][i][1]))
                self.s1s.append(s1)
                self.s2s.append(s2)
                self.features.append([len(s1), len(s2)])
                self.labels.append(label)
                local_max_len = max(len(s1), len(s2))
                if local_max_len > self.max_len:
                    self.max_len = local_max_len

        
        elif(mode=='testing'):
            # df is for storing QA_base, or localized QA_base
            df = QA_base['question_seg']
            s1 = list(jieba.cut(Query))
            for s2 in df:
                s2 = s2.split('|')[:-1]
                self.s2s.append(s2)
                self.s1s.append(s1)
                self.features.append([len(s1), len(s2)])
                local_max_len = max(len(s1), len(s2))
                if local_max_len > self.max_len:
                    self.max_len = local_max_len

        self.data_size = len(self.s1s)
        self.num_features = len(self.features[0])


class WikiQA(Data):
    def open_file(self, mode):
        with open("./WikiQA_Corpus/WikiQA-" + mode + ".txt", "r", encoding="utf-8") as f:
            stopwords = nltk.corpus.stopwords.words("english")

            for line in f:
                items = line[:-1].split("\t")

                s1 = items[0].lower().split()
                # truncate answers to 40 tokens.
                s2 = items[1].lower().split()[:40]
                label = int(items[2])

                self.s1s.append(s1)
                self.s2s.append(s2)
                self.labels.append(label)
                word_cnt = len([word for word in s1 if (word not in stopwords) and (word in s2)])
                self.features.append([len(s1), len(s2), word_cnt])

                local_max_len = max(len(s1), len(s2))
                if local_max_len > self.max_len:
                    self.max_len = local_max_len

        self.data_size = len(self.s1s)

        flatten = lambda l: [item for sublist in l for item in sublist]
        q_vocab = list(set(flatten(self.s1s)))
        idf = {}
        for w in q_vocab:
            idf[w] = np.log(self.data_size / len([1 for s1 in self.s1s if w in s1]))

        for i in range(self.data_size):
            wgt_word_cnt = sum([idf[word] for word in self.s1s[i] if (word not in stopwords) and (word in self.s2s[i])])
            self.features[i].append(wgt_word_cnt)

        self.num_features = len(self.features[0])
