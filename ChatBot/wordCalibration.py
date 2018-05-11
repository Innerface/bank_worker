class sentencetree(object):
    def __init__(self,sen):
        '''
        Initialization using left-to-right scheme
        For multiple occurrence of the same word
        Put it in the deepest position
        '''
        buffer = {}
        for i in range(len(sen)):
            if sen[i] in buffer.keys(): continue
            elif len(buffer) == 0:
                buffer[sen[i]] = 1
            else:
                deplist = []
                for j in range(len(buffer)):
                    comp = list(buffer.keys())[j]
                    if sen[i] in comp:
                        buffer[comp] += 1
                        buffer[sen[i]] = 1
                        deplist.append(buffer[sen[i]])
                    elif comp in sen[i]:
                        buffer[sen[i]] = buffer[comp] + 1
                        deplist.append(buffer[sen[i]])
                    else:
                        buffer[sen[i]] = 1
                        deplist.append(buffer[sen[i]])
                buffer[sen[i]] = max(deplist)
        self.tree = buffer
        inv_tree = {}
        for k, v in buffer.items():
            inv_tree[v] = inv_tree.get(v,[])
            inv_tree[v].append(k)
        self.inv_tree = inv_tree
        self.depth = max(buffer.values())

    def calibrate(self,counter,lt,adjForSep = True):
        '''
        Using sentence tree to calibrate a counter
        inv_tree is better at iterating over layers
        Counter should be a dictionary
        '''
        new_counter = {}
        wstatus =[]
        if adjForSep:
            wordkey = [w.split('|')[0] for w in counter.keys()]
        else:
            wordkey = counter.keys()
        for d in range(self.depth):
            for word in self.inv_tree[d+1]:
                buffer = word
                fraction = 0
                complete = False
                if word in wordkey:
                    word_ = list(counter.keys())[wordkey.index(word)]
                else:
                    word_ = '|'.join([word,'n'])
                new_counter[word_] = 0
                for w in wordkey:
                    if len(buffer) == 0:
                        complete = True
                        break
                    elif w in buffer:
                        cind = list(counter.keys())[wordkey.index(w)]
                        buffer = buffer.replace(w,'')
                        new_counter[word_] = max(counter[cind],new_counter[word_])
                        fraction += 1
                        if len(buffer) == 0:
                            complete = True
                            break
                wstatus.append([complete,fraction])
        new_counter = {k:v for k,v in new_counter.items() if v > 0}
        return new_counter,wstatus

    def __str__(self):
        return str(self.tree)




if __name__ == '__main__':
    # Test sentencetree class
    test = sentencetree(['有','抵押贷款','什么','贷款','质押贷款','特殊质押贷款','区别','有什么','有什么了','质押贷款'])
    print(test)
    test = sentencetree(['有', '什么','有什么', '质押贷款','种类'])
    #print(test.tree, test.inv_tree, test.depth)
    testcounter = {'贷款|n':15,'质押|r':3,'种类|n':5}
    print(test.calibrate(testcounter,None))
