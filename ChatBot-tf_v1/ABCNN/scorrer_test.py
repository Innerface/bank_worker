import pickle
import sys
from datetime import datetime

import numpy as np
import tensorflow as tf
from sklearn.externals import joblib

from ABCNN.ABCNN import ABCNN
from ABCNN.utils import build_path
from ABCNN.preprocess import Word2Vec, MSRP, WikiQA
import sys


def ABCNN_Score(tfSession, model, clf, w, l2_reg, epoch, max_len, model_type, num_layers, data_type, classifier,
                word2vec, num_classes=2,
                Query=None, QA_base=None):
    """
    :param tfSession:
    :param model:
    :param clf:
    :param w:
    :param l2_reg:
    :param epoch:
    :param max_len:
    :param model_type:
    :param num_layers:
    :param data_type:
    :param classifier:
    :param word2vec:
    :param num_classes:
    :param Query:
    :param QA_base:
    :return:
    """

    if data_type == "WikiQA":
        test_data = WikiQA(word2vec=word2vec, max_len=max_len)
    else:
        test_data = MSRP(word2vec=word2vec, max_len=max_len)

    test_data.open_file(mode='testing', Query=Query, QA_base=QA_base)
    # tf.reset_default_graph()
    '''
    model = ABCNN(s=max_len, w=w, l2_reg=l2_reg, model_type=model_type,
                  num_features=test_data.num_features, num_classes=num_classes, num_layers=num_layers)
    '''

    # model_path = build_path("ABCNN/model_ABCNN/", data_type, model_type, num_layers)
    # MAPs, MRRs = [], []

    print("=" * 50)
    print("test data size:", test_data.data_size)

    # Due to GTX 970 memory issues
    # gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.7)

    for e in range(epoch, epoch + 1):
        start = datetime.now()

        test_data.reset_index()
        '''
        #with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
        with tf.Session() as sess:
            saver = tf.train.Saver()
            saver.restore(sess, model_path + "-" + str(e))
            print(model_path + "-" + str(e), "restored.")

            if classifier == "LR" or classifier == "SVM":
                clf_path = build_path("ABCNN/model_ABCNN/", data_type, model_type, num_layers,
                                      "-" + str(e) + "-" + classifier + ".pkl")
                clf = joblib.load(clf_path)
                print(clf_path, "restored.")

            QA_pairs = {}
            #s1s, s2s, labels, features = test_data.next_batch(batch_size=test_data.data_size)
            s1s, s2s, features = test_data.next_batch(batch_size=test_data.data_size,mode='testing')

            for i in range(test_data.data_size):
                pred, clf_input = sess.run([model.prediction, model.output_features],
                                           feed_dict={model.x1: np.expand_dims(s1s[i], axis=0),
                                                      model.x2: np.expand_dims(s2s[i], axis=0),
                                                      #model.y: np.expand_dims(labels[i], axis=0),
                                                      model.features: np.expand_dims(features[i], axis=0)})

                if classifier == "LR":
                    clf_pred = clf.predict_proba(clf_input)[:, 1]
                    pred = clf_pred
                elif classifier == "SVM":
                    clf_pred = clf.decision_function(clf_input)
                    pred = clf_pred

                s1 = " ".join(test_data.s1s[i])
                s2 = " ".join(test_data.s2s[i])

                if s1 in QA_pairs:
                    #QA_pairs[s1].append((s2, labels[i], np.asscalar(pred)))
                    QA_pairs[s1].append((s2, np.asscalar(pred)))

                else:
                    #QA_pairs[s1] = [(s2, labels[i], np.asscalar(pred))]
                    QA_pairs[s1] = [(s2,  np.asscalar(pred))]


            #acc=0
            for s1 in QA_pairs.keys():
                QA_pairs[s1] = sorted(enumerate(QA_pairs[s1]), key=lambda x: x[1][-1], reverse=True)[:5]
                #print("s1:",s1)
                #print(QA_pairs[s1])
            sess.close()
            '''
        QA_pairs = {}
        # s1s, s2s, labels, features = test_data.next_batch(batch_size=test_data.data_size)
        s1s, s2s, features = test_data.next_batch(batch_size=test_data.data_size, mode='testing')
        for i in range(test_data.data_size):
            pred, clf_input = tfSession.run([model.prediction, model.output_features],
                                            feed_dict={model.x1: np.expand_dims(s1s[i], axis=0),
                                                       model.x2: np.expand_dims(s2s[i], axis=0),
                                                       # model.y: np.expand_dims(labels[i], axis=0),
                                                       model.features: np.expand_dims(features[i], axis=0)})

            if classifier == "LR":
                clf_pred = clf.predict_proba(clf_input)[:, 1]
                pred = clf_pred
            elif classifier == "SVM":
                clf_pred = clf.decision_function(clf_input)
                pred = clf_pred

            s1 = " ".join(test_data.s1s[i])
            s2 = " ".join(test_data.s2s[i])

            if s1 in QA_pairs:
                # QA_pairs[s1].append((s2, labels[i], np.asscalar(pred)))
                QA_pairs[s1].append((s2, np.asscalar(pred)))

            else:
                # QA_pairs[s1] = [(s2, labels[i], np.asscalar(pred))]
                QA_pairs[s1] = [(s2, np.asscalar(pred))]

        # acc=0
        for s1 in QA_pairs.keys():
            QA_pairs[s1] = sorted(enumerate(QA_pairs[s1]), key=lambda x: x[1][-1], reverse=True)[:5]
            # print("s1:",s1)
            # print(QA_pairs[s1])
        simscore = QA_pairs[s1][0][1][1]
        mostsimilarindex = [ii[0] for ii in QA_pairs[s1]]
        mostsimilarsentence = [ii[1][0] for ii in QA_pairs[s1]]
        end = datetime.now()
        print("Elapsed Time:", end - start)
        return simscore, mostsimilarindex, mostsimilarsentence
        """
                for idx, (s2, label, prob) in enumerate(QA_pairs[s1]):
                    if(prob>0.5) & (int(label)-1==0):
                        acc+=1
                    elif(prob<0.5) & (int(label)-0==0):
                        acc+=1
            precision=acc/test_data.data_size
            print("[Epoch " + str(e) + "] precision:", precision)
        """

        """
            # Calculate MAP and MRR for comparing performance
            MAP, MRR = 0, 0
            for s1 in QA_pairs.keys():
                
                p, AP = 0, 0
                MRR_check = False

                QA_pairs[s1] = sorted(QA_pairs[s1], key=lambda x: x[-1], reverse=True)
                

                for idx, (s2, label, prob) in enumerate(QA_pairs[s1]):
                    if label == 1:
                        if not MRR_check:
                            MRR += 1 / (idx + 1)
                            MRR_check = True

                        p += 1
                        AP += p / (idx + 1)


                AP /= p
                MAP += AP

            num_questions = len(QA_pairs.keys())
            MAP /= num_questions
            MRR /= num_questions

            MAPs.append(MAP)
            MRRs.append(MRR)
            print("[Epoch " + str(e) + "] MAP:", MAP, "/ MRR:", MRR)
    
    print("=" * 50)
    print("max MAP:", max(MAPs), "max MRR:", max(MRRs))
    print("=" * 50)

    exp_path = build_path("./experiments/", data_type, model_type, num_layers, "-" + classifier + ".txt")
    with open(exp_path, "w", encoding="utf-8") as f:
        print("Epoch\tMAP\tMRR", file=f)
        for i in range(e):
            print(str(i + 1) + "\t" + str(MAPs[i]) + "\t" + str(MRRs[i]), file=f)
"""


if __name__ == "__main__":

    # Paramters
    # --ws: window_size
    # --l2_reg: l2_reg modifier
    # --epoch: epoch
    # --max_len: max sentence length
    # --model_type: model type
    # --num_layers: number of convolution layers
    # --data_type: MSRP or WikiQA data
    # --classifier: Final layout classifier(model, LR, SVM)

    QA_base_version = '2017-08-18'
    # Load QA base

    file = open('QA_base/QA_with_pair_{}.pickle'.format(QA_base_version), 'rb')
    QA_base = pickle.load(file)
    file.close()

    # default parameters
    params = {
        "ws": 2,
        "l2_reg": 0.0004,
        "epoch": 50,
        "max_len": 31,
        "model_type": "ABCNN3",
        "num_layers": 3,
        "data_type": "MSRP",
        "classifier": "LR",
        "word2vec": Word2Vec()
    }

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            k = arg.split("=")[0][2:]
            v = arg.split("=")[1]
            params[k] = v

    result_score, result_index, resut_sen = ABCNN_Score(w=int(params["ws"]), l2_reg=float(params["l2_reg"]),
                                                        epoch=int(params["epoch"]),
                                                        max_len=int(params["max_len"]), model_type=params["model_type"],
                                                        num_layers=int(params["num_layers"]),
                                                        data_type=params["data_type"],
                                                        classifier=params["classifier"], word2vec=params["word2vec"],
                                                        Query='储蓄卡挂失', QA_base=QA_base)

    print(result_score, '\n', result_index, '\n', resut_sen)
