# -*- coding=utf-8 -*-
import sys

import importlib
importlib.reload(sys)
import pickle as cPickle
import docx
import re
import os
import globalFuncsVariables as gf


class docnode:
    def __init__(self, va=None, ch=None, co=None):
        self.value = va
        self.childs = ch
        self.content = co


def findtext(str):
    for i in range(0, len(paras)):
        p = paras[i]
        if str in p.text:
            return int(i)
    return -1


def getatt(para):
    if pi < 0:
        return 0
    line = para.text
    if re.match(u'第.+章', line):
        return 1
    if re.match(u'\d\.\d(?=[^\.])', line) or re.match(u'\d\. \d(?=[^\.])', line) or re.match(u'\d\d\.\d(?=[^\.])',
                                                                                             line):
        return 2
    if re.match(u"\d.+?\d.+?\d", line) or re.match(u"\d\. \d \.\d", line):
        return 3
    return 10


def dfs(root, pre):
    global pa
    pa = getnext()

    while getatt(pa) == 10:
        if root.content == None:
            root.content = []
        root.content.append(pa.text)
        pa = getnext()
    while getatt(pa) > pre:
        new = docnode(pa.text, None, None)
        if root.childs == None:
            root.childs = []
        root.childs.append(new)
        dfs(root.childs[-1], pre + 1)
    else:
        return


def getnext():
    global pi
    pi += 1
    if pi == end:
        pi = -10
    p = paras[pi]
    if p.text != '':
        return p
    else:
        return getnext()


def bfsTree_rearrangeContentSentence(root):
    """

    """
    # search title and sub title
    queue = []
    queue.append(root)
    # search content
    index = 0
    while (index < len(queue)):
        cur = queue[index]
        index += 1
        if not cur:         #判断cur是否为空，为空则continue，不为空，执行下面语句。
            continue
        if cur.content is not None and len(cur.content) > 0:
            contentAllStr = ''.join(cur.content)
            cur.content = map(lambda sentence: sentence + '。', re.split(u"。|？|!|\?|！", contentAllStr.strip()))
        if cur.childs:
            queue.extend(cur.childs)


def process_docxs(baseRebuild, incrementUpdateDocx=None):
    '''
    对docx格式的语料进行处理，解析文档树。

    totalRebuild: 是否对所有电子书都重新解析
    '''
    dirName = os.path.join(gf.baseDir, 'rawbooks')
    oDirName = os.path.join(gf.baseDir, 'bookpkls')
    count = 0
    rawbooks = os.listdir(dirName)
    if incrementUpdateDocx is not None: rawbooks.append(incrementUpdateDocx)
    for i, fName in enumerate(rawbooks):
        if fName.endswith('.docx'):
            try:
                print (fName)
                count += 1
                doc = docx.Document(os.path.join(dirName, fName))
                fName2 = fName[:-5]
                ofileName = os.path.join(oDirName, fName2 + '.pkl')
                if baseRebuild == False and os.path.exists(ofileName) and i != len(rawbooks) - 1:
                    continue
                global paras, pi, end
                paras = doc.paragraphs
                t = []
                book = docnode()
                book.value = fName2
                pi = 0
                end = min(4279, len(paras) - 1)
                pt = paras[1]
                dfs(book, 0)
                # bfsTree_rearrangeContentSentence(book)
                file = open(ofileName, 'wb')
                cPickle.dump(book, file, protocol=0)
                del doc
                del book
                print (fName, 'loaded')
            except RuntimeError as e:
                print (e)
            except IndexError as e:
                file = open(ofileName, 'wb')
                cPickle.dump(book, file, protocol=0)
                del doc
                del book
                print (fName, 'loaded')


def process_doc2paratext():
    '''
    对docx文档进行处理，抽取出段落。这是为solr问答引擎准备的原始数据。
    将生成的txt文件放到solr引擎目录下，import进去。默认使用jieba分词进行索引和查询。
    :return:
    '''
    dirName = os.path.join(gf.baseDir, 'bookpkls')
    books = []
    for fName in os.listdir(dirName):
        with open(os.path.join(dirName, fName), 'r') as f:
            try:
                books.append(cPickle.load(f))
            except:
                pass
    for i, book in enumerate(books):
        book_title = book.value if book.value is not None else 'NoBookTitle'
        queue = []
        queue.append(book)
        # search content
        index = 0
        while (index < len(queue)):
            cur = queue[index]
            index += 1
            if not cur:
                continue
            if cur.content is not None and len(cur.content) > 0:
                paraText = ''.join(cur.content).strip()
                with open(os.path.join(gf.baseDir, 'solrTxts', book_title + '_' + str(i) + '_' + str(index) + '.txt'),
                          'wb') as f:
                    f.write(paraText)
            if cur.childs:
                queue.extend(cur.childs)


if __name__ == "__main__":
    incrementUpdateDocx = u'manualAddBook.docx'
    process_docxs(baseRebuild=True, incrementUpdateDocx=incrementUpdateDocx)
    # process_doc2paratext()
    print ('here')

