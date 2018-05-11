from gensim import corpora,models,similarities

doc2load = open('toycopora.txt').read().split('\n')[:-1]
text = [[word for word in line.split()] for line in doc2load]
dictionary = corpora.Dictionary(text)
print(dictionary.token2id)
corpus = [dictionary.doc2bow(t) for t in text]
tfidf = models.TfidfModel(corpus)
lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=3)
query = tfidf[dictionary.doc2bow(['a','aa','aaa'])]
print(list(enumerate(tfidf[corpus])))
index = similarities.MatrixSimilarity(tfidf[corpus])
index_lsi = similarities.MatrixSimilarity(lsi[corpus])

sim = index[query]
sim_lsi = index_lsi[query]
print(list(enumerate(index)))
print(list(enumerate(sim)))
print(list(enumerate(sim_lsi)))