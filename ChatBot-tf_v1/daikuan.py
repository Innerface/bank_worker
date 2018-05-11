import sys
import jieba
import os

class daikuan(object):
    def __init__(self):
        pass

    def Loan(self,ques):
        answer = None
        if (u'利率低' in ques or u'利率不高' in ques or u'风险低' in ques) and (u'三个月' in ques or u'二个月' in ques or u'一个月' in ques):
            answer = '根据您的需求，推荐您申请诚意贷，诚意贷利率低，按日计算，还款灵活'
            return answer
        elif (u'利率高' in ques or u'利率比较高' in ques or u'风险高' in ques) and (u'三个月' in ques or u'二个月' in ques or u'一个月' in ques):
            answer = '根据您的需求，推荐您申请随意贷，诚意贷利率高，但是风险会大一些'
            return answer
        elif (u'怎么' in ques or u'如何' in ques) and (u'申请' in ques or u'办理' in ques):
            answer = '请您登陆我行官网，点击诚意贷申请入口，按照提示办理即可'
            return answer
        elif (u'申请一下' in ques) or (u'申请吧' in ques) or u'办一下' in ques or u'办理一下' in ques or u'怎么办' in ques:
            answer = '请您登陆我行官网，点击短期贷款申请入口，按照提示办理即可'
            return answer
        elif (u'谢' in ques or u'好的' in ques or u'好吧' in ques):
            answer = '感谢您的咨询，请您再咨询其他问题'
            return answer
        else:
            return answer


