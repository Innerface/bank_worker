# coding=utf-8
import re
import jieba
import os
import threading
import time
import sys
import pymysql
from time import ctime,sleep
import jieba.posseg as pseg
import multiprocessing
import xlrd
import pandas as pd
import numpy as np
import pickle
import VariableFunction as vf
class extractSOPair():
	"""
	新的产品目录需要重新分词
	"""
	def __init__(self):
		self.refTreeLevel = 5
		self.loadRefTreeDB()
		'''
		匹配率
		'''
		self.rate = {}
		self.rate[1] = 0.99
		self.rate[2] = 0.51
		self.rate[3] = 2/3
		self.rate[4] = 3/4
		self.rate[5] = 3/5
		self.rate[6] = 4/6
		self.rate[7] = 4/7
		self.rate[8] = 5/8
		self.rate[9] = 7/9
		self.rate[10] = 0.72
		self.rate[11] = 0.73
		self.rate[12] = 0.74
		self.rate[13] = 0.74
		self.rate[14] = 0.74
		self.rate[15] = 0.74
		self.rate[16] = 0.74

		'''
		self.ref : {originQ:(元素,Q分词,元素分词)} 索引
		'''

		self.ref = []
		# self.loadRefTree()
		'''
		self.data : [(id,originQ,BaiduResult)]
		'''
		self.data = self.loadQuestionFormDB()
		'''
		self.homoionymList [[]] 同义词库
		self.homoionymR {} 同义词与词典的关系
		'''
		self.homoionymList = []
		self.homoionymR = {}
		self.loadHomoiony()
		# self.runTree(self.data,'0914')
		return
		# 多进程处理加速
		start = time.clock()
		try:
			p1 = multiprocessing.Process(target=self.runTree, args=(self.data1,1))
			p2 = multiprocessing.Process(target=self.runTree, args=(self.data2,2))
			p3 = multiprocessing.Process(target=self.runTree, args=(self.data3,3))
			p1.start()
			p2.start()
			p3.start()
			p1.join()
			p2.join()
			p3.join()
		except Exception as e:
			print(str(e))
		end = time.clock()
		print(end - start)

	def markOneQ(self,q):
		'''
		单个问题打标
		for 国华
		:param q: 问题 str类型
		:return: 打标列表
		'''
		d = {}
		d[q] = [(q,q)]
		result = self.runTree(d,'aaa',saveOption=False)
		res_list = []
		for key,value in result[q].items():
			res_list.append(key)
		return res_list

	def pkl2DB(self):
		f = open('tree_withAttr.pkl', 'rb')
		tree = pickle.load(f)
		f.close()
		db = pymysql.connect(
			host='211.159.153.216',
			port=3306,
			user='root',
			passwd='ibm@1q2w#E$R',
			db='xiaoqing',
			charset='utf8'
		)
		cursor = db.cursor()
		for inde, row in tree.iterrows():
			level = row['Level']
			Node = row['Node']
			FN = row['FatherNode']
			if level == str(0):
				sql = "INSERT INTO product (level,name) VALUES ('%s','%s')" % (level,Node)
				cursor.execute(sql)
			elif int(level) < self.refTreeLevel:
				sql = "select * from product where name = '%s'" % (FN)
				cursor.execute(sql)
				db.commit()
				res = cursor.fetchone()
				print(res)
				sql = "INSERT INTO product (level,name,parent_id) VALUES ('%s','%s','%s')" % (level, Node,res[0])
				cursor.execute(sql)
			else:
				sql = "select * from product where name = '%s'" % (FN)
				cursor.execute(sql)
				db.commit()
				res = cursor.fetchone()
				print(res)
				sql = "INSERT INTO product_attribute (name,product_id) VALUES ('%s','%s')" % (Node, res[0])
				cursor.execute(sql)
			db.commit()

		cursor.close()
		db.close()

	'''
	读取第一次爬取的百度数据
	'''
	def firstVer(self):
		try:
			data = xlrd.open_workbook('question_t完全版本1.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'title5')  # 通过名称获取
		nrows = table.nrows
		info = {}
		pattern = re.compile('\-|_')
		for i in range(nrows):
			if i == 0:
				continue
			word = pattern.split(table.cell(i,2).value)
			if table.cell(i,1).value in info:
				info[table.cell(i,1).value].append((table.cell(i,1).value, table.cell(i,2).value))
			else:
				info[table.cell(i, 1).value] = [(table.cell(i, 1).value, table.cell(i, 1).value)]
				info[table.cell(i, 1).value].append((table.cell(i, 1).value, table.cell(i,2).value))
		return info
	'''
	读取第二次爬取的百度数据
	'''
	def secVer(self):
		try:
			data = xlrd.open_workbook(vf.localPath + '/dictionary_and_corpus/baiduTitle2.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'baiduTitle2')  # 通过名称获取
		nrows = table.nrows
		info = {}
		#pattern = re.compile('\-|_')
		for i in range(nrows):
			if i == 0:
				continue
			# word = pattern.split(table.cell(i,2).value)
			if table.cell(i,1).value in info:
				info[table.cell(i, 1).value].append((table.cell(i,1).value, table.cell(i,2).value))
			else:
				info[table.cell(i, 1).value] = [(table.cell(i, 1).value, table.cell(i, 1).value)]
				info[table.cell(i, 1).value].append((table.cell(i, 1).value, table.cell(i,2).value))
		return info
	'''
	读取第三次爬取的百度数据
	'''
	def ThrVer(self):
		try:
			data = xlrd.open_workbook(vf.localPath + '/dictionary_and_corpus/娇娇整合_百度结果.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'娇娇整合')  # 通过名称获取
		nrows = table.nrows
		info = {}
		pattern = re.compile('\-|_')
		for i in range(nrows):
			if i == 0:
				continue
			word = pattern.split(table.cell(i, 1).value)
			if table.cell(i,0).value in info:
				info[table.cell(i, 0).value].append((table.cell(i,0).value, table.cell(i,1).value))
			else:
				info[table.cell(i, 0).value] = [(table.cell(i, 0).value, table.cell(i, 0).value)]
				info[table.cell(i, 0).value].append((table.cell(i, 0).value, table.cell(i,1).value))
		return info
	def loadQuestionFormDB(self):
		db = pymysql.connect(
			host='211.159.153.216',
			port=3306,
			user='root',
			passwd='ibm@1q2w#E$R',
			db='xiaoqing',
			charset='utf8'
		)
		cursor = db.cursor()
		aa = cursor.execute("SELECT * from question_t")
		data = cursor.fetchmany(aa)
		info = {}
		for inf in data:
			if not inf[1] in data:
				info[inf[1]] = []
			info[inf[1]].append((inf[1],inf[1],inf[2],inf[3],inf[4]))
		db.commit()
		cursor.close()
		db.close()
		return info
	'''
	读取银行提供的索引 生成业务树
	'''
	def loadRefTree(self):
		try:
			data = xlrd.open_workbook('产品属性整理_全分词0912.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'产品属性')  # 通过名称获取
		nrows = table.nrows
		root = {} # root {{{}}{{{}}}}
		unique = {}
		for i in range(nrows):
			if i == 0:
				continue # 跳过标题行
			temp_root = root # {}
			if table.cell(i, 0).value == '':
				continue
			for j in range(self.refTreeLevel):
				value = table.cell(i, j).value
				# 以防中间断层
				if value == '':
					value = 'null'
				# 创建新节点
				if not value in temp_root:
					temp_root[value] = {}
				temp_root = temp_root[value]
				temp_root['level'] = j # level 代表对应key在树中的深度
				if j == self.refTreeLevel-1 :
					# 记录下属性
					temp_root[table.cell(i,self.refTreeLevel).value] = 1
			if not table.cell(i,self.refTreeLevel).value in unique:
				unique[table.cell(i,self.refTreeLevel).value] = []
			lastv = ''
			for j in range(self.refTreeLevel):
				q = self.refTreeLevel - j - 1
				if table.cell(i,q).value != '':
					lastv = table.cell(i,q).value
					break
			unique[table.cell(i,self.refTreeLevel).value].append(lastv)
		uniquee = {}
		for key, v_list in unique.items():
			if len(v_list) == 1:
				uniquee[key] = v_list[0]
				# print(key)
				# print(v_list[0])
				# print('')
		self.unique = uniquee
		self.refTree = root
	def _fenci(self,word):
		d_f = ''
		result = pseg.cut(word)
		for res in result:
			d_f += res.word + '|'
		return d_f
	def loadRefTreeDB(self):
		'''
		从数据库中读取业务树
		:return:
		'''
		root = {}
		db = pymysql.connect(
			host='211.159.153.216',
			port=3306,
			user='root',
			passwd='ibm@1q2w#E$R',
			db='xiaoqing',
			charset='utf8'
		)
		cursor = db.cursor()
		sql = 'SELECT * FROM product'
		a = cursor.execute(sql)
		info = cursor.fetchmany(a)
		sql = 'SELECT * FROM product_attribute'
		a = cursor.execute(sql)
		info2 = cursor.fetchmany(a)
		# 构建业务树
		for i in info:
			temp_root = root
			if i[3] == None and i[2]==0:
				# 树根
				d_f= self._fenci(i[1])
				temp_root[d_f] = {}
				temp_root = temp_root[d_f]
				temp_root['level'] = i[2]
			else:
				#树中间 需要找到FatherNode
				for ii in info:
					if i[3] == ii[0]:
						iiv = self._fenci(ii[1]) # FatherNode 的 name
						break
				try:
					visited = {}
					stack = []
					stack.append(('root', temp_root))
					while len(stack) > 0:
						(key, temp_root) = stack[-1]
						if key == iiv:
							# 找到FatherNode
							# 创建新节点
							d_f = self._fenci(i[1])
							if not d_f in temp_root:
								temp_root[d_f] = {}
							temp_root = temp_root[d_f]
							temp_root['level'] = i[2]  # level 代表对应key在树中的深度
							break
						if not key in visited:
							visited[key] = 1
							for tKey, tDic in temp_root.items():
								if tKey == 'level':
									continue
								else:
									if type(tDic) == type({}):
										stack.append((tKey, tDic))
						stack.pop()

				except Exception as e:
					print(str(e))
					raise e
		# 加入业务元素
		for i in info2:
			temp_root = root
			visited = {}
			stack = []
			stack.append(('root', temp_root))
			for ii in info:
				if ii[0] == i[2]:
					iiv = self._fenci(ii[1])
					break
			while len(stack) > 0:
				(key, temp_root) = stack[-1]
				if key == iiv:
					# 找到FatherNode
					# 创建新节点
					d_f = self._fenci(i[1])
					if not d_f in temp_root:
						temp_root[d_f] = 1
					temp_root['level'] = self.refTreeLevel  # level 代表对应key在树中的深度
					break
				if not key in visited:
					visited[key] = 1
					for tKey, tDic in temp_root.items():
						if tKey == 'level':
							continue
						else:
							if type(tDic) == type({}):
								stack.append((tKey, tDic))

				stack.pop()
		self.refTree = root
		unique = {}
		for i in info2:
			i1 = self._fenci(i[1])
			for ii in info:
				if i[2] == ii[0]:
					i2 = self._fenci(ii[1])
					break
			if not (i1,i2) in unique:
				unique[(i1,i2)] = []

			unique[(i1,i2)].append(i2)
		uniquee = {}
		for uni_key, uni_value in unique.items():
			if len(uni_value) == 1:
				uniquee[uni_key[0]] = uni_value[0]
		# for uk,uv in uniquee.items():
		# 	print(uk)
		# 	print(uv)
		# 	print('')
		self.unique = uniquee
		cursor.close()
		db.close()

	'''
	
	'''
	def loadRefTreeList(self):
		try:
			data = xlrd.open_workbook('产品属性整理_v0.10912.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'产品属性')  # 通过名称获取
		nrows = table.nrows
		tree = pd.DataFrame()
		for i in range(nrows):
			preNode = ''
			if i == 0:
				continue # 跳过标题行
			for j in range(self.refTreeLevel + 1):
				value = table.cell(i, j).value
				# 以防中间断层
				if value == '':
					continue
				# 创建新节点
				if preNode == '':
					# 最大的父节点 父节点为root
					node = pd.DataFrame({"Node": value, "Level": str(j), "FatherNode": 'root'}, index=['0'])
				else:
					# 父节点为preNode
					node = pd.DataFrame({"Node": value, "Level": str(j), "FatherNode": preNode}, index=['0'])
				tree = tree.append(node, ignore_index=True)
				preNode = value
		# se = pd.Series(tree['Node'])
		# print(type(se.str.contains('贷款')))
		tree = tree.drop_duplicates()
		tree.sort_values(by=['Level'],inplace=True,ascending=1)
		f = open('tree_withAttr.pkl', 'wb')
		pickle.dump(tree, f)
		f.close()
		self.refTreeList = tree
	'''
	读取业务元素
	'''
	def loadAttr(self):
		try:
			data = xlrd.open_workbook('产品属性整理_v0.1.xlsx')
		except Exception as e:
			print(str(e))
		table = data.sheet_by_name(u'产品属性')  # 通过名称获取
		nrows = table.nrows
		tree = pd.DataFrame()
		values = {}
		for i in range(nrows):
			preNode = ''
			if i == 0:
				continue # 跳过标题行

			value = table.cell(i, 5).value
			if not value in values:
				values[value] = 1
		for value, aaa in values.items():
			node = pd.DataFrame({"Node": value, "Level": str(5), "FatherNode": 'root'}, index=['0'])
			tree = tree.append(node, ignore_index=True)
		tree = tree.drop_duplicates()
		f = open('attr.pkl', 'wb')
		pickle.dump(tree, f)
		f.close()
	'''
	读取同义词
	'''
	def loadHomoiony(self):
		f = open(vf.localPath + '/dictionary_and_corpus/simword0912.txt', 'rb')
		try:
			lines = f.readlines()
		except Exception as e:
			print(str(e))
		f.close()
		index = 0
		for line in lines:
			line = line.decode('utf8')
			line = line.replace('\n', '')
			line = line.replace('\r', '')
			grp = line.split(' ')
			self.homoionymList.append(grp)
			for gr in grp:
				if gr == '':
					continue
				self.homoionymR[gr] = index
			index += 1
	'''
	业务元素匹配
	'''
	def findQ(self,d,Q):
		res = []
		for rQ in Q:
			rfQ = rQ[2].split('|')
			tol = len(rfQ) - 1
			if tol == 0:
				continue
			count = 0
			for refQ in rfQ:
				if refQ == '':
					continue
				if not refQ in d:
					# 没有找到 进行同义词替换
					if refQ in self.homoionymR:
						index = self.homoionymR[refQ]
						for ho1 in self.homoionymList[index]:
							if ho1 == refQ or ho1 == '':
								continue
							refQ_rep = refQ.replace(refQ, ho1)
							if refQ_rep in d:
								count += 1
								break
				else:
					# 找到了可以抽取
					count += 1
			rate = count/tol
			if rate >= self.rate[tol]:
				# if d == '（）能够办理哪些业务':
				# 	print(rate)
				res.append(rQ[0])
		return res
	'''
	判断两个字匹不匹配
	
	返回匹配中的字符的列表
	'''
	def judgeWord2Word(self, d, yw):
		if yw == 'null':
			return None
		refS = yw.split('|')
		rWord = []
		count = 0
		tol = len(refS) - 1
		if tol == 0:
			return None
		for S_part in refS:
			if S_part == '':
				continue
			if not S_part in d:
				# 针对S_part进行同义词替换
				if S_part in self.homoionymR:
					index = self.homoionymR[S_part]
					for ho1 in self.homoionymList[index]:
						if ho1 == S_part or ho1 == '':
							continue
						refS_rep = S_part.replace(S_part, ho1)
						if refS_rep in d:
							count += 1
							rWord.append(ho1)######
							break
			else:
				count += 1
				rWord.append(S_part)
		rate = count/tol
		if rate >= self.rate[tol]:
			return rWord
		else:
			return None

	'''
	返回此节点下的所有树叶
	'''
	def getLeave(self, root):
		dic = {}
		stack = []
		stack.append(root)
		while len(stack)>0:
			temp_root = stack.pop()
			try:
				for tKey, tDic in temp_root.items():
					if tKey == 'level':
						continue
					if type(tDic) != type({}):
						if not tKey in dic:
							dic[tKey] = 1
					else:
						stack.append(tDic)
					# self.judgeWord2Word(d, tKey)
			except Exception as e:
				print(temp_root)
		list = []
		for dd,rr in dic.items():
			list.append((dd.replace('|',''),'',dd))
		return list
	'''
	业务树场景匹配
	'''
	def entityTreeMatch(self,d):
		try:
			visited = {}
			stack = []
			stack.append(('root',self.refTree))
			while len(stack) > 0:
				(key,temp_root) = stack[-1]
				if not key in visited:
					visited[key] = 1
					for tKey, tDic in temp_root.items():
						if tKey == 'level':
							continue
						else:
							if type(tDic) == type({}):
								stack.append((tKey,tDic))
				else:
					for tKey, tDic in temp_root.items():
						if type(tDic) != type({}):
							continue

						result = self.judgeWord2Word(d, tKey)
						if result != None:
							remainWord = d
							for k in result:
								remainWord = remainWord.replace(k, '')
							return tKey.replace('|',''), remainWord, self.getLeave(tDic)
					stack.pop()

		except Exception as e:
			print(str(e))
			raise e
		return None,None,None
	'''
	返回节点（列表）下的所有树叶
	'''
	def getListLeave(self,root,level):
		stack = []
		stack.append(root)
		visited = {}
		ans = []
		while len(stack) > 0:
			preNode = stack.pop()
			df = self.refTreeList[self.refTreeList['FatherNode'] == str(preNode)]
			for inde, row in df.iterrows():
				clevel = row['Level']
				Node = row['Node']
				if clevel == str(self.refTreeLevel):
					if not Node in ans:
						ans.append((Node.replace('|', ''),'',Node))
					continue
				if not Node in stack and not Node in visited:
					stack.append(Node)
					visited[Node] = 1
		return ans


	'''
	业务树（列表）场景匹配
	'''
	def entityTreeListMatch(self, d):
		try:
			for i in range(self.refTreeLevel):
				index = self.refTreeLevel - i - 1
				df = self.refTreeList[self.refTreeList['Level'] == str(index)]
				for inde, row in df.iterrows():
					tKey = row['Node']
					level = row['Level']
					result = self.judgeWord2Word(d, tKey)
					if result != None:
						remainWord = d
						for k in result:
							remainWord = remainWord.replace(k, '')
						sss = self.getListLeave(tKey, level)
						return tKey.replace('|', ''), remainWord, sss
		except Exception as e:
			print(str(e))
			raise e
		return None,None,None
	def entityTreeListMatchSet(self, d):
		try:
			visited = {}
			for inde, row in self.refTreeList.iterrows():
				Node = row['Node']
				level = row['Level']
				if level == str(self.refTreeLevel) or Node in visited:
					continue
				visited[Node] = 1
				start = time.clock()
				result = self.judgeWord2Word(d, Node)
				end = time.clock()
				# print(end - start)
				if result != None:
					remainWord = d
					for k in result:
						remainWord = remainWord.replace(k, '')
					sss = self.getListLeave(Node, level)
					return Node.replace('|', ''), remainWord, sss
		except Exception as e:
			print(str(e))
			raise e
		return None,None,None
	'''
	对元组进行选择
	'''
	def judgeResult(self, originProblem, resultSet):
		matchTuple = []
		for tuple, num in resultSet.items():
			matchEntity = 0 # 实体匹配
			matchAttr = 0 # 元素匹配
			if tuple[0] in originProblem:
				matchEntity = 1
			else:
				# 同义词替换
				if tuple[0] in self.homoionymR:
					index = self.homoionymR[tuple[0]]
					for ho1 in self.homoionymList[index]:
						if ho1 == tuple[0] or ho1 == '':
							continue
						if ho1 in tuple[0]:
							matchEntity = 1
							break
			# 元素匹配
			if tuple[1] in originProblem:
				matchAttr = 1
			else:
				# 同义词替换
				if tuple[1] in self.homoionymR:
					index = self.homoionymR[tuple[1]]
					for ho1 in self.homoionymList[index]:
						if ho1 == tuple[1] or ho1 == '':
							continue
						if ho1 in tuple[1]:
							matchAttr = 1
							break
			if matchEntity == 1 and matchAttr == 1:
				matchTuple.append((tuple[0],tuple[1],num))
		if len(matchTuple) > 0:
			# 取字符串最长的那个
			matchTuple = sorted(matchTuple, key=lambda d:len(d[1]), reverse=True)
			return matchTuple[0]
		else:
			# 取元组数量最多的那个
			result = sorted(resultSet.items(), key=lambda d:d[1], reverse=True)
			return (result[0][0][0],result[0][0][1], result[0][1])
	'''
	按照业务树匹配（列表的树结构）
	'''
	def runTreeList(self, data , name):
		res = {}
		for od, da in data.items():
			# od : QA原问题 da：0：原问题 1：百度爬取的结果 list

			d_res = {}
			for d in da:
				# 针对每一个记录匹配矫正
				try:
					start = time.clock()
					refSS, result, Q = self.entityTreeListMatch(d[1])
					end = time.clock()
					# print(end - start)
					if refSS == None:
						continue
					q_list = self.findQ(result, Q)
					if len(q_list) > 0:
						if refSS in d_res:
							d_res[refSS].extend(q_list)
						else:
							d_res[refSS] = []
							d_res[refSS].extend(q_list)
				except Exception as e:
					print(str(e))
					raise e
			if len(d_res) > 0:
				if not d[0] in res:
					res[d[0]] = {}
				for dk, dr in d_res.items():
					for ddr in dr:
						if (dk, ddr) in res[d[0]]:
							res[d[0]][(dk, ddr)] += 1
						else:
							res[d[0]][(dk, ddr)] = 1
			if not d[0] in res:
				res[d[0]] = {}
		self.save2Excel(res,name)
	'''
	d[0:1] question d[2] Answer d[3] keyword_item d[4] Pair
	从question_t
	存储成pickle的函数
	'''
	def runTreeP(self, data, name):
		print('start ' + str(name))
		print(len(data))
		res = pd.DataFrame()
		count = 0
		total = 0
		for od, da in data.items():
			# od : QA原问题 da：0：原问题 1：百度爬取的结果 list
			d_res = {}
			for d in da:
				# 针对每一个记录匹配矫正
				try:
					refSS, result, Q = self.entityTreeMatch(d[1])
					total += 1
					if refSS == None:
						res = res.append({'question': d[0], 'answer': d[2], "keyword_item": d[3], "source": d[4],'SOPair': ('', '')}, ignore_index=True)
						continue
					q_list = self.findQ(result, Q)
					if len(q_list) > 0:
						count += 1
						for ql in q_list:
							res = res.append({'question':d[0],'answer':d[2],"keyword_item":d[3],"source":d[4],'SOPair':(refSS,ql)},ignore_index=True)
					else:
						res = res.append({'question':d[0],'answer':d[2],"keyword_item":d[3],"source":d[4],'SOPair':('','')},ignore_index=True)
				except Exception as e:
					print(str(e))
					raise e
		print(res)
		print(count/total)
		self.save2Pickle(res, 'SOPair')
		df = res['SOPair']
		res = pd.DataFrame()
		res['SOPair'] = df
		res = res.drop_duplicates()
		self.save2Pickle(res, 'Pair')
	'''
	按照业务树匹配
	'''
	def runTree(self, data, name, saveOption):
		res = {}
		for od, da in data.items():
			# od : QA原问题 da：0：原问题 1：百度爬取的结果 list
			d_res = {}
			for d in da:
				# 针对每一个记录匹配矫正
				try:
					refSS, result, Q = self.entityTreeMatch(d[1])
					if refSS == None:
						continue

					q_list = self.findQ(result, Q)
					if len(q_list) > 0:
						if refSS in d_res:
							d_res[refSS].extend(q_list)
						else:
							d_res[refSS] = []
							d_res[refSS].extend(q_list)
				except Exception as e:
					print(str(e))
					raise e
				try:
					# 匹配单有元素
					for uniKey,uniValue in self.unique.items():
						result =  self.judgeWord2Word(d[1],uniKey)
						if result != None:
							refSS = uniValue.replace('|','')
							value = uniKey.replace('|','')
							if len(value) <= 1:
								continue
							if not refSS in d_res:
								d_res[refSS] = []
							d_res[refSS].append(value)
				except Exception as e:
					raise e
			if len(d_res) > 0:
				if not d[0] in res:
					res[d[0]] = {}
				for dk,dr in d_res.items():
					for ddr in dr:
						if (dk, ddr) in res[d[0]]:
							res[d[0]][(dk, ddr)] += 1
						else:
							res[d[0]][(dk, ddr)] = 1
			if not d[0] in res:
				res[d[0]] = {}
		if saveOption:
			self.save2Excel(res, name)
		return res

	'''
	保存成pickle
	'''
	def save2Pickle(self,res,name):
		try:
			f = open(str(name)+'.pkl','wb')
			pickle.dump(res,f)
			f.close()
		except Exception as e:
			print(str(e))
			f.close()
			return

if __name__ == '__main__':
	ex = extractSOPair()
	print(ex.markOneQ('怎信用卡和储蓄卡'))
	print(ex.markOneQ('贷款是利率多少'))
	print(ex.markOneQ('贷款是利率多少'))