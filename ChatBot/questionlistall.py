import sys

class questionlist(object):
    def __init__(self,question):
        if (u'挂失' in question or u'丢' in question or u'找不着' in question or u'找不到' in question or u'没了' in question or u'掉了' in question
                    or u'偷' in question) and u'怎么办' not in question and u'咋办' not in question:
            self.flag = 'report'
        if u'我要办理售汇' == question or u'我要办理结汇' == question or u'我要办理结售汇' == question:
            self.flag = 'exchange'
        if u"查" in question and (u"余额" in question or u"交易" in question):
            self.flag = 'query'
        if (u'短期贷款' in question or u'短期信用贷款' in question) and (u'办' in question or u'申请' in question):
            self.flag = 'daikuan'
        if (u'储蓄卡' in question) and (u'年费' in question):
            self.flag = 'nianfei'
        else:
            self.flag = 'non_std'
        self.question = question
        self.answer = None

    def update(self,question):
        if (u'挂失' in question or u'丢' in question or u'找不着' in question or u'找不到' in question or u'没了' in question or u'掉了' in question
                    or u'偷' in question) and u'怎么办' not in question and u'咋办' not in question:
            self.flag = 'report'
        if u'我要办理售汇' == question or u'我要办理结汇' == question or u'我要办理结售汇' == question:
            self.flag = 'exchange'
        if u"查" in question and (u"余额" in question or u"交易" in question):
            self.flag = 'query'
        if (u'短期贷款' in question or u'短期信用贷款' in question) and (u'办' in question or u'申请' in question):
            self.flag = 'daikuan'
        if (u'储蓄卡' in question) and (u'年费' in question):
            self.flag = 'nianfei'
        else:
            self.flag = 'non_std'
        self.question = question

    def stdanswer(self):
        ##想查一下余额##
        content = self.question
        contents = None
        if (content == '你好' or content == '您好' or content == '你好呀' or content =='您好呀' or content == '早上好' or content == '嗨'):
            contents = '您好，我是小M，很高兴能帮到您！'
            return contents

        if (content == '解决'):
            contents = '感谢您对小M的肯定，有问题可继续向我提问！'
            return contents

        if (contents == '未解决'):
            contents = '小M正在学习中，没能帮到您，请多多见谅'
            return  contents

        if ((u'查' in content or u'查询' in content or u'查一下' in content or u'查查' in content or u'查下' in content or u'看下' in content or u'看一下' in content or u'看看' in content or u'知道' in content) \
            and (u'余额' in content or u'有多少钱' in content or u'剩多少钱' in content)):
            contents = '您好，如果您想查询余额或是交易记录，请输入：我要查询交易记录，小M将为您查询，谢谢。'

        ##怎么查余额##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content) \
            and (u'卡' in content) and (u'查' in content or u'看' in content) \
            and (u'多少钱' in content or u'余额' in content)):
            contents = '您好，如果您想查询余额，请登录网上银行或手机银行进行查询，你也可以到附近的营业厅和ATM机进行查询。'

        ##怎么查进账记录##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content) \
            and (u'查' in content) \
            and (u'进账记录' in content or u'出账记录' in content or u'交易记录' in content)):
            contents = '您好，如果您想交易记录，请登录网上银行或手机银行进行查询，你也可以到附近的营业厅和ATM机进行查询。'

        ##怎么查余额##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content) \
            and (u'钱' in content or u'交易' in content or u'余额' in content) and u'查' in content):
            contents = '您好，如果您想查询余额，请登录网上银行或手机银行进行查询，你也可以到附近的营业厅和ATM机进行查询。'

        ##多了300块钱，怎么回事##
        if ((u'钱' in content or u'元' in content or u'块' in content) \
            and (u'多了' in content or u'少了' in content or u'刷' in content or u'取' in content or u'扣' in content or u'交易' in content or u'消费' in content)):
            contents = '您好，请您登录网上营业厅或手机银行进行交易记录的查询，您也可以到附近的营业厅或是ATM机进行查询。'


        ##能查多久的交易##
        if ((u'交易' in content or u'消费' in content) \
            and (u'查' in content or u'看' in content or u'存' in content) and (
            u'多久' in content or u'多长时间' in content)):
            contents = '目前中华人民共和国的《金融机构客户身份识别和客户身份资料及交易记录保存管理办法》第29条规定：金融机构应当按照下列期限保存客户身份资料和交易记录：第一、客户身份资料，自业务关系结束当年\r一次性交易记账当年计起至少保存5年。第二、交易记录，自交易记账当年计起至少保存5年。银行卡一年前的存取清单可以免费打印出来，超过部分就要缴纳一定费用了。'

        ##年费是啥##
        if ((u'什么' in content or u'啥' in content) and (u'年费' in content)):
            contents = '年费指的是银行卡的年费，每年都会收取。一般从开卡之后的第二年的第二个月收取（首年免年费）。除此之外，每3个月日均存款低于300元，每月收取1元的小额账户管理费。'

        ##卡里扣款了，但是没到账##
        if (u'卡' in content and u'扣款' in content and u'没到账'):
            contents = '一般到账要1个工作日的。'

        ##可用余额与账户余额有什么不同##
        if (u'可用余额' in content and u'账户余额' in content and (u'不等' in content or u'不一样' in content or u'不同' in content)):
            contents = '可用余额是可以使用的余额。 账户余额是账户上的实际余额。 如果您的借记卡上账户余额和可用余额不一样，说明您有业务未完成。 例如购买基金，不是在基金业务处理时间内操作的，会暂时把购买基金款冻结，在下一个基金营业时间内完成此业务。'

        ##没卡能不能查询余额##
        if ((u'没' in content or u'无' in content) \
            and (u'卡' in content) and (u'能不能' in content or u'能否' in content or u'是否可以' in content or u'可不可以' in content) \
            and (u'余额' in content or u'多少钱' in content)):
            contents = '查询交易或余额记录仅需提供卡号与密码。'

        ##怎么存款##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content) \
            and (u'存款' in content or u'存钱' in content or u'存点钱' in content)):
            contents = '您好，如需办理存款，请您携带好身份证件和需要存的金额到附近的营业厅开户办理。'

        ##怎么取款##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'怎样' in content or u'想' in content) \
            and (u'取款' in content or u'取钱' in content or u'取点钱' in content)):
            contents = '您好，如需办理取款，请您携带好银行卡或存折到附近的营业厅或ATM机进行办理。'


        #异地取款##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'怎样' in content or u'想' in content) \
            and (u'外地' in content or u'异地' in content) and u'取' in content):
            contents = '您好，异地取款时，请携带银行卡或存折到异地的银行营业厅或ATM机进行办理。'

        #ATM机跨行、异地取款手续费##
        if ('ATM' in content and (u'外地' in content or u'异地' in content) and (u'取款' in content or u'取钱' in content) and (u'手续费' in content or u'费用' in content)):
            contents = '您好，使用ATM机在同行异地取款时，不收取手续费。跨行取款时，会根据不同银行的政策进行手续费的收取。'

        if ('ATM' in content and (u'跨行' in content or u'不一家' in content or u'另一家' in content or u'别的' in content or u'其他' in content) \
            and (u'取款' in content or u'取钱' in content) and (u'手续费' in content or u'费用' in content)):
            contents = '您好，使用ATM机在同行异地取款时，不收取手续费。跨行取款时，会根据不同银行的政策进行手续费的收取。'

        ##ATM机存取款限额##
        if ('ATM' in content and (u'能' in content or u'可以' in content) and (u'取' in content or u'存' in content)):
            contents = '您好，使用ATM机在取款时，同一张卡在一天是有取款数额限制的，一般为人民币20000元，存款是没有限制的。'

        if ('ATM' in content and (u'限额' in content or u'额度' in content) and (u'取' in content or u'存' in content)):
            contents = '您好，使用ATM机在取款时，同一张卡在一天是有取款数额限制的，一般为人民币20000元，存款是没有限制的。'

        ##ATM无卡存取款##
        if ('ATM' in content and ( u'没卡' in content or u'无卡' in content or u'没有' in content or u'没带' in content or u'忘带' in content or u'忘拿' in content) \
            and (u'取' in content or u'存' in content)):
            contents = '您好，ATM机可以实现无卡取款和存款。无卡存款时，只需提供卡号即可存款，而且没有手续费。若需要无卡存款，请利用网上银行或手机银行进行预约，设定无卡取款的额度，便可实现在ATM机的无卡取款'

        ##怎么贷款##
        if (( u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content or u'咋办' in content) \
            and (u'贷款' in content or u'贷点钱' in content)):
            contents = '您好，如果您需要贷款，请准备好贷款申请书、身份证、收入证明、抵押物产权证（如果是抵押贷款）、信用记录（如果是无抵押贷款）等材料，到银行进行办理。如果客户通过了银行的资格审查，会与银行签订一系列法律合同，审批后，银行放款。'

        ##怎么房贷车贷##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content or u'咋办' in content) \
            and (u'房贷' in content)):
            contents = '您好，如果您需要办理房贷，请携带贷款申请书、个人有效证件、婚姻状况证明、收入证明材料、购房首付款证明、购房合同等银行需要的材料，到银行营业厅进行办理。银行会对贷款人的资格进行审批。通过审批的贷款人将会和银行签订贷款合同，并办理相关担保手续。'

        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content or u'咋办' in content) \
            and (u'车贷' in content or '汽车贷款' in content or u'汽车' in content)):
            contents = '您好，如果您需要办理汽车贷款，请携带贷款申请书、个人有效证件、收入证明材料、购车合同等银行需要的材料，到银行营业厅进行办理。银行会对贷款人的资格进行审批。通过审批的贷款人将会和银行签订贷款合同，并办理相关担保手续。'

        ##信用卡问题#####################

        ##信用卡额度查询及调整##
        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content or u'咋办' in content) \
            and (u'查' in content or u'查询' in content or u'看' in content) and u'额度' in content):
            contents = '您好，如果您需要查询信用卡额度，请致电信用卡官方热线或是登录信用卡网上营业厅查询。'

        if ((u'怎么' in content or u'如何' in content or u'咋' in content or u'想' in content or u'怎样' in content or u'咋办' in content) \
            and (u'调整' in content or u'提升' in content or u'提高' in content or u'调高' in content) and u'额度' in content):
            contents = '您好，如果您需要调整信用卡额度，请您致电信用卡官方热线进行申请，并提供相应的调整额度所需的材料。'

        ##信用卡延期##
        if ((u'信用卡' in content or u'卡' in content) and (u'到期' in content or u'有效期到了' in content)):
            contents = '您好，信用卡到期后，如果你想继续使用该信用卡，请致电信用卡服务热线，进行信用卡换卡延期申请。'

        if ((u'信用卡' in content or u'卡' in content) and (u'换' in content or u'更换' in content or u'换张卡' in content)):
            contents = '您好，如果您需要更换信用卡，请致电信用卡服务热线，进行信用卡换卡延期申请。'

        ##信用卡密码积分##
        if ((u'信用卡' in content or u'卡' in content) and (u'积分' in content)):
            contents = '您好，如果您需要查询、使用信用卡的积分，请登录信用卡官方网站或手机客户端，在信用卡界面进入积分服务入口，进行积分的查询和使用'

        if ((u'信用卡' in content or u'卡' in content) and (u'密码' in content) and (u'忘' in content or u'忘记' in content)):
            contents = '您好，如果您忘记了信用卡密码，请您致电信用卡官方热线或是登录信用卡网上营业厅，进行身份验证后，可以重新设置新的密码。'

        ##信用卡年费##
        if ((u'信用卡' in content or u'卡' in content) and (u'年费' in content or u'管理费' in content or u'费用' in content)):
            contents = '您好，信用卡的年费根据卡片的等级进行设置，若是一年有若干次刷卡记录后，会免除年费。'

        ##信用卡取现##
        if ((u'信用卡' in content or u'卡' in content) and (u'取钱' in content or u'取' in content or u'取现' in content)):
            contents = '您好，持卡人可以使用信用卡向银行提取现金，信用卡取现主要包括透支取现和溢缴款取现两种方式。透支取现是需要支付利息，并且是从你提取现金的当天就开始计算利息，而溢缴款取现则不需要支付利息，仅需支付部分手续费，具体视各银行规定。 '

        ##信用卡刷外币##
        if ((u'信用卡' in content or u'卡' in content) and (u'美元' in content or u'欧元' in content or u'日元' in content or u'外币' in content or u'其他货币' in content)):
            contents = '您好，只有Visa、MasterCard、AmericanExpress等信用卡可以刷外币，请您根据您持有的信用卡种类，通过信用卡客服热线进一步咨询。'

        if ((u'信用卡' in content or u'卡' in content) and ('国家' in content or '外国' in content or '国外' in content or u'别的国家' in content)):
            contents = '您好，当您在国外时，只要您使用信用卡的地方拥有您的支付接口，比如银联、Visa、MasterCard等，就可以使用您的信用卡。'

        if ((u'信用卡' in content or u'卡' in content) and (u'美国' in content or u'日本' in content or u'东南亚' in content or u'欧洲' in content or u'英国' in content or u'泰国' in content or u'韩国' in content or u'澳大利亚' in content or u'意大利' in content or u'德国' in content or u'法国' in content or u'希腊' in content or u'马尔代夫' in content)):
            contents = '您好，当您在国外时，只要您使用信用卡的地方拥有您的支付接口，比如银联、Visa、MasterCard等，就可以使用您的信用卡。'

        if ((u'信用卡' in content or u'卡' in content) and (u'还钱' in content or u'还款' in content) and (u'美元' in content or u'欧元' in content or u'日元' in content or u'外币' or u'其他货币' in content)):
            contents = '您好，当您使用人民币还外币时，系统通过自动购汇汇率进行折算，请您了解换款时的汇率。'

        ##信用卡透支##
        if ((u'信用卡' in content or u'卡' in content) and (u'透支' in content or u'欠款' in content or u'欠钱' in content)):
            contents = '您好，当您的信用卡出现透支的时候，如果实在还款日之前，则不收取利息，若是在还款日之后，则每天收取相应的利息。'

        if ((u'信用卡' in content or u'卡' in content) and (u'负数' in content or u'负的' in content)):
            contents = '您好，如果您的信用卡交易记录中有负数，说明这笔交易为还款交易；如果卡片历史账单显示为负数，说明该月信用卡不欠钱，无需还款。'

        ##信用卡状态##
        if ((u'信用卡' in content or u'卡' in content) and ((u'查' in content or u'查询' in content or u'查一下' in content or u'查查' in content or u'查下' in content or u'看下' in content or u'看一下' in content or u'看看' in content or u'知道' in content) and (u'状态' in content))):
            contents = '您好，您可以登录信用卡网上营业厅查询卡片的状态。信用卡的状态分为正常、冻结、止付、挂失、收卡、作废等，请根据卡片的不同状态。'
        if contents is not None:
            self.answer = contents
            self.flag = 'std'
            return self.flag,self.answer
        else:
            return self.flag,self.answer