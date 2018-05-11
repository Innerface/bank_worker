from questionlistall import questionlist
from daikuan import daikuan
from nianfei import nianfei

def answer_exc(QA_std):
    assert type(QA_std).__name__ == 'questionlist','Input should be of questionlist type!'
    flag_to_return,answer_to_return = QA_std.stdanswer()
    if flag_to_return == 'std':
        return flag_to_return,answer_to_return
    elif flag_to_return == 'daikuan':
        loan = daikuan()
        return flag_to_return,loan.Loan(QA_std.question)
    elif flag_to_return == 'nianfei':
        fee = nianfei()
        return flag_to_return,fee.Fee(QA_std.question)
    else:
        return flag_to_return,answer_to_return


