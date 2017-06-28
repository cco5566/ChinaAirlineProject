# -*- coding: utf-8 -*-
import yaml
import sys
from imp import reload
reload(sys)
from sklearn.model_selection import train_test_split
import multiprocessing
import numpy as np
from gensim.models.word2vec import Word2Vec
from gensim.corpora.dictionary import Dictionary
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Dropout,Activation
from keras.models import model_from_yaml
np.random.seed(1337)  # For Reproducibility
import jieba
import pandas as pd
import sys
sys.setrecursionlimit(1000000)
# set parameters:
vocab_dim = 100
maxlen = 600
n_iterations = 5  # ideally more..
n_exposures = 3 #字典最小詞頻
window_size = 5
batch_size = 16
epochs = 20
input_length = 600
cpu_count = multiprocessing.cpu_count()


#加载训练文件
# def loadfile():
# 	neg=pd.read_excel('data/neg.xls',header=None,index=None)
# 	pos=pd.read_excel('data/pos.xls',header=None,index=None)
#
# 	combined=np.concatenate((pos[0], neg[0]))
# 	y = np.concatenate((np.ones(len(pos),dtype=int), np.zeros(len(neg),dtype=int)))
#
# 	return combined,y
def loadfile():
    posWords = []
    negWords = []

    with open('test_data/pos_tw.txt', 'r', encoding='utf-8') as items:
        for item in items:
            posWords.append(item)
    with open('test_data/neg_tw.txt', 'r', encoding='utf-8') as items:
        for item in items:
            negWords.append(item)

    pos = np.array(posWords)
    neg = np.array(negWords)

    combined=np.concatenate((pos, neg))
    y = np.concatenate((np.ones(len(pos),dtype=int), np.zeros(len(neg),dtype=int)))
    return combined,y

#对句子经行分词，并去掉换行符
def tokenizer(text):
	''' Simple Parser converting each document to lower-case, then
		removing the breaks for new lines and finally splitting on the
		whitespace
	'''
	text = [jieba.lcut(document.replace('\n', '')) for document in text]
	return text

#创建词语字典，并返回每个词语的索引，词向量，以及每个句子所对应的词语索引
def create_dictionaries(model=None,
						combined=None):
	''' Function does are number of Jobs:
		1- Creates a word to index mapping
		2- Creates a word to vector mapping
		3- Transforms the Training and Testing Dictionaries

	'''
	if (combined is not None) and (model is not None):
		gensim_dict = Dictionary()
		gensim_dict.doc2bow(model.vocab.keys(),
							allow_update=True)
		w2indx = {v: k+1 for k, v in gensim_dict.items()}#所有频数超过10的词语的索引
		w2vec = {word: model[word] for word in w2indx.keys()}#所有频数超过10的词语的词向量

		def parse_dataset(combined):
			''' Words become integers
			'''
			data=[]
			for sentence in combined:
				new_txt = []
				for word in sentence:
					try:
						new_txt.append(w2indx[word])
					except:
						new_txt.append(0)
				data.append(new_txt)
			return data
		combined=parse_dataset(combined)
		combined= sequence.pad_sequences(combined, maxlen=maxlen)#每个句子所含词语对应的索引，所以句子中含有频数小于10的词语，索引为0
		return w2indx, w2vec,combined
	else:
		print('No data provided...')

#创建词语字典，并返回每个词语的索引，词向量，以及每个句子所对应的词语索引
def word2vec_train(combined):

	model = Word2Vec(size=vocab_dim,
					 min_count=n_exposures,
					 window=window_size,
					 workers=cpu_count,
					 iter=n_iterations)
	model.build_vocab(combined)
	model.train(combined, total_examples=model.corpus_count)
	model.save('lstm_data/Word2vec_model.pkl')
	index_dict, word_vectors,combined = create_dictionaries(model=model,combined=combined)
	return   index_dict, word_vectors,combined

def get_data(index_dict,word_vectors,combined,y):

	n_symbols = len(index_dict) + 1  # 所有单词的索引数，频数小于10的词语索引为0，所以加1
	embedding_weights = np.zeros((n_symbols, vocab_dim))#索引为0的词语，词向量全为0
	for word, index in index_dict.items():#从索引为1的词语开始，对每个词语对应其词向量
		embedding_weights[index, :] = word_vectors[word]
	x_train, x_test, y_train, y_test = train_test_split(combined, y, test_size=0.2)
	return n_symbols,embedding_weights,x_train,y_train,x_test,y_test

##定义网络结构
def train_lstm(n_symbols,embedding_weights,x_train,y_train,x_test,y_test):
	print('Defining a Simple Keras Model...')
	model = Sequential()  # or Graph or whatever
	model.add(Embedding(output_dim=vocab_dim,
						input_dim=n_symbols,
						mask_zero=True,
						weights=[embedding_weights],
						input_length=input_length))  # Adding Input Length

	model.add(Dropout(0.2))
	model.add(LSTM(128))
	model.add(Dense(units=256,
					activation='relu'))
	model.add(Dropout(0.2))
	model.add(Dense(units=1, activation='sigmoid'))

	print('Compiling the Model...')
	model.compile(loss='binary_crossentropy',
				  optimizer='adam',metrics=['accuracy'])

	print("Train...")
	model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs,verbose=1, validation_data=(x_test, y_test))

	print("Evaluate...")
	score = model.evaluate(x_test, y_test, verbose=1, batch_size=batch_size)

	yaml_string = model.to_yaml()
	with open('lstm_data/lstm.yml', 'w') as outfile:
		outfile.write( yaml.dump(yaml_string, default_flow_style=True) )
	model.save_weights('lstm_data/lstm.h5')
	print('Test score:', score)


#训练模型，并保存
def train():
	print('Loading Data...')
	combined,y=loadfile()
	print(len(combined),len(y))
	print('Tokenising...')
	combined = tokenizer(combined)
	print('Training a Word2vec model...')
	index_dict, word_vectors,combined=word2vec_train(combined)
	print('Setting up Arrays for Keras Embedding Layer...')
	n_symbols,embedding_weights,x_train,y_train,x_test,y_test=get_data(index_dict, word_vectors,combined,y)
	print(x_train.shape,y_train.shape)
	train_lstm(n_symbols,embedding_weights,x_train,y_train,x_test,y_test)

def input_transform(string):
	words=jieba.lcut(string)
	words=np.array(words).reshape(1,-1)
	model=Word2Vec.load('lstm_data/Word2vec_model.pkl')
	_,_,combined=create_dictionaries(model,words)
	return combined

def lstm_predict(string):
	print('loading model......')
	with open('lstm_data/lstm.yml', 'r') as f:
		yaml_string = yaml.load(f)
	model = model_from_yaml(yaml_string)

	print('loading weights......')
	model.load_weights('lstm_data/lstm.h5')
	model.compile(loss='binary_crossentropy',
				  optimizer='adam',metrics=['accuracy'])
	data=input_transform(string)
	data.reshape(1,-1)
	#print data
	result=model.predict_classes(data)
	if result[0][0]==1:
		print(string,' positive')
	else:
		print(string,' negative')

if __name__=='__main__':
	train()
	#string='电池充完了电连手机都打不开.简直烂的要命.真是金玉其外,败絮其中!连5号电池都不如'
	#string='牛逼的手机，从3米高的地方摔下去都没坏，质量非常好'
	#string='酒店的环境非常好，价格也便宜，值得推荐'
	#string='手机质量太差了，傻逼店家，赚黑心钱，以后再也不会买了'
	#string='我是傻逼'
	#string='你是傻逼'
	#string='屏幕较差，拍照也很粗糙。'
	#string='质量不错，是正品 ，安装师傅也很好，才要了83元材料费'
	#string='东西非常不错，安装师傅很负责人，装的也很漂亮，精致，谢谢安装师傅！'
	string='航班準时,空服员亲切有礼,能给予我适合的服务,对於我的问题可以很清楚的答覆并解决,是我旅行传统航空得首选'
	string= '十分不好的飞行经验，飞机上居然没有乾净新的枕头和毛毯，所有东西都是之前旅客用过的，十分的糟糕，餐食普普通通'
	string='普普通通，可能我抱的期待太大了，之前時常在報章雜誌上看到長榮獲獎的新聞，心裡想這間航空公司一定很棒!但真正飛行過後覺得與外界所說的稍微有點出入，我想可能我抱的期待太大了吧?但不得不說硬體設備真的很優!不過餐點部分就見仁見智了，從台灣飛往泰國所提供的餐點我覺得普普，但是從泰國飛往荷蘭這段所提供的餐點我真的覺得很棒(雞肉飯非常香辣又很下飯!)去程時(泰國飛往荷蘭)的空服員都很親切，而且非常親民很像鄰家姐姐般!但是回程時，不知道是因為有乘客在機上購買大量免稅品(?)使得事務長太開心並大聲直呼感謝，總而言之和朋友睡覺睡一半就被"謝謝"給喚醒來了...(我坐的位置是在左邊靠窗處，而當時那位事務長所站的地方是在另一邊的安全門位置)最後想繼續睡也睡不著，那就乾脆享受機上的硬體設備吧!'
	lstm_predict(string)
