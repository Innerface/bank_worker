import sys
import jieba

class nianfei(object):
    def __init__(self):
        pass

    def Fee(self,ques):
        answer = None
        if (u'上海' in ques or u'北京' in ques or u'广州' in ques or u'深圳' in ques):
            answer = '请问您的描述，如果您的卡月均存款小于300元，没月将收取10元的管理费'
            return answer
        elif (u'谢' in ques or u'好的' in ques or u'好吧' in ques):
            answer = '感谢您的咨询，请您再咨询其他问题'
            return answer
        else:
            return answer
