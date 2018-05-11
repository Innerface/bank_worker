## JVM地址修改

GrammerMatching.py 与 operationAnalysis.py 文件中，将相应代码：
'''
    path1 = sys.path[0] + '/hanlp-1.3.4-release/hanlp-1.3.4.jar'
    path2 = sys.path[0] + '/hanlp-1.3.4-release'
'''
中的 path1 与 path2 改为绝对路径。

## property路径修改

将/hanlp-1.3.4-release 下的文件 hanlp.properties 打开，并找到第3行：
'''
root=/Users/wgh/Downloads/ChatBot/hanlp-1.3.4-release/data-for-1.3.3
'''
将此路径改为 /data 所在的路径。

##redis 路径修改
在 mainNLP.py 下的代码：
'''
redis_nodes = [{'host': '211.159.153.216', 'port': 7000},
               {'host': '211.159.153.216', 'port': 7001},
               {'host': '211.159.153.216', 'port': 7002},
               {'host': '211.159.153.216', 'port': 7003},
               {'host': '211.159.153.216', 'port': 7004},
               {'host': '211.159.153.216', 'port': 7005}
               ]
'''
改为相应的redis集群ip地址。

## knowledgegraph 配置路径修改

将 /knowledgegraph/codes/globalFuncVariables.py 打开，并将代码：
'''
baseDir='/Users/wgh/Documents/ChatBot/knowledgegraph'
'''
修改为 /knowledgegraph 所在的绝对路径。


将路径 ：
'''
baseIp='211.159.153.216'
'''
修改为服务器ip地址

将路径：
'
solrCoreIp='http://211.159.153.216:8090/solr/docimportcore'
'
修改为相应的提供solr core服务的机器IP

## VariableFunction.py文件修改localpath为本机路径
## 安装Python包

```
# 可能需要root权限
# Python版本为3.6
pip3.6 install -i https://pypi.tuna.tsinghua.edu.cn/simple  jieba --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  pandas --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  jpype1 --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  gensim --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  redis-py-cluster --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  pymysql --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  py2neo --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  neo4j-driver --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  tensorflow --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  selenium --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  bs4 --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  sklearn --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  nltk --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  DBUtils --upgrade --ignore-installed
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple  python-docx --upgrade --ignore-installed
```

## 安装mongoDB
安装mongoDB后，执行以下命令，启动mongoDB

```
mongod --dbpath /data/db
```

## Django建表

```
python manange.py makemigrations exchange query report
python manange.py migrate
```

## 启动NLP，Service后台

```
# 在manage.py同目录下，执行以下命令
# 在8081端口启动后台
python manage.py runserver 0.0.0.0:8081
```

## End
NLP Service后台启动成功