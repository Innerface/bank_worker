# import VariableFunction as vf
# import pandas as pd
# import MySQLConn as Mysql
# import extractSOPair
from SO_translator import decode_pair
import tensorflow as tf
# [('零售贷款', '办理'), ('跨境汇款', '操作'), ('外币账户', '开立'), ('协定存款', '申办')]
# [('贷款', '利率'), ('零售贷款', '利率'), ('零售贷款', '放款'), ('个人委托贷款业务', '贷款利率')]
# [('贷款', '利率'), ('零售贷款', '利率'), ('零售贷款', '放款'), ('个人委托贷款业务', '贷款利率')]
# answer
# qid
# question
# question_seg
# Guessed_SO_Pair

# 1 qid int 11 0 0   1 0 0
# 0 question varchar 256 0 0     0
# 0 answer varchar 1024 0 0     0
# 0 keyword_item varchar 256 0 1     0
# 0 source varchar 45 0 1     0
# 0 created_time datetime 0 0 1 CURRENT_TIMESTAMP  0
# 0 update_time datetime 0 0 1   1
# 0 so_pair varchar 255 0 1     0

# for item in vf.QA_base:
#     print(item)
# print(type(vf.QA_base))
# for item in vf.QA_base['question_parsing']:
#     print(item)

# a = {'a':[1,2],'b':[2,3]}
# b = pd.DataFrame(a)
# print(b)
# print(type(b))
#
# mysql = Mysql.Mysql()
# sql = 'select SO_pair from question_t'
# result = mysql.getAll(sql)
# print(len(result))
# ext = extractSOPair.extractSOPair()
#
# result_pair = ext.markOneQ('借记卡账户余额')
# print(result_pair)
#
#
# print(result[1]['SO_pair'].decode('utf-8'))
# result_new = result[1]['SO_pair'].decode('utf-8').split('|')
# print(result_new)
# print(result_new[0])
#
# print(list(result_pair[1]))
# print(result_new[0].split(','))
#
# if list(result_pair[1]) == result_new[0].split(','):
#     print('okkk')

#

print(decode_pair.decode_so_pair('贵金属'))
print(decode_pair.decode_so_pair('储蓄卡的有效期是多少'))