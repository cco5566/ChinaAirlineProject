#coding:utf-8
from bs4 import BeautifulSoup as bs4
import requests
import json

class LTNSpider:
	URLList = []
	ARTICLE_List = []
	NEWS_Lists = []
	def __init__(self):
		self.URLList = LTNSpider.URLList
		self.ARTICLE_List = LTNSpider.ARTICLE_List
		self.NEWS_Lists = LTNSpider.NEWS_Lists

	#Get real-time news url
	def getURL(self):
		for page in range(1,2):
			#Real-time news pages
			URL = 'http://news.ltn.com.tw/list/BreakingNews?page='+str(page)
			self.URLList.append(URL)
		#Get articles url from real-time news pages
		for URL in self.URLList:
			r = requests.get(URL)
			soup = bs4(r.text, 'html.parser')
			articles = soup.find_all('a', {'class' : 'picword'})
			for article in articles:
				articleURL = article.get('href')
				self.ARTICLE_List.append(articleURL)
		return self.ARTICLE_List

	# def checkUpdate():
	# 	pass

	#Get Content from article
	def getContent(self):
		for article in self.ARTICLE_List:
			r = requests.get(article)
			soup = bs4(r.text, 'html.parser')
			news = soup.find(class_ = 'content')
			content = ""
			newsList = []
			try:
				title = str(news.find('h1').contents[0])
			except Exception as e:
				continue
			newsText = news.find('div', {'id':'newstext'})
			try:
				time = newsText.span.text
			except:
				continue
			newsSoup = bs4(str(newsText), 'html.parser')
			newsSoup.ul.decompose()
			try:
				article = newsSoup.findAll('p')
			except:
				pass
			print('新聞標題 : ' + title)
			print('------------------------------')
			print(time)
			print('------------------------------')
			for contents in article:
				content +=  str(contents.text)
			print(content)
			print('------------------------------')
			self.NEWS_Lists.append([title,time,content])
		return self.NEWS_Lists
