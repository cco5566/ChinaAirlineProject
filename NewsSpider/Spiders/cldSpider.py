#coding:utf-8
from bs4 import BeautifulSoup as bs4
from selenium import webdriver
import requests
import json
import re
import time as t

class cldSpider:
	URLList = []
	ARTICLE_List = []
	NEWS_Lists = []
	def __init__(self):
		self.URLList = cldSpider.URLList
		self.ARTICLE_List = cldSpider.ARTICLE_List
		self.NEWS_Lists = cldSpider.NEWS_Lists

	#Get real-time news url
	def getURL(self):
		page = 0
		state = True
		while state:
			#Real-time news pages
			URL = 'http://www.coolloud.org.tw/story?page='+str(page)
			r = requests.get(URL)
			soup = bs4(r.text, 'html.parser')
			timeList = soup.findAll('span', {'class':'date-display-single'})
			for time in timeList:
				timeList[timeList.index(time)] = time.text
			print(URL)
			print(timeList)
			timeList = timeList[:-5]#filter hot news
			state = t.strftime('%Y/%m/%d', t.localtime()) in timeList
			if state:
				page += 1
				self.URLList.append(URL)
			else:
				page -= 1

		#Get articles url from real-time news pages
		for URL in self.URLList:
			r = requests.get(URL)
			soup = bs4(r.text, 'html.parser')
			articles = soup.findAll('div', {'class':'field-content pc-style'})
			for article in articles:
				articleURL = 'http://www.coolloud.org.tw'+ article.find('a').get('href')
				self.ARTICLE_List.append(articleURL)
				print(self.ARTICLE_List)
		return {'press':'cld', 'URLList':self.ARTICLE_List}

	#Get Content from article
	def getContent(self):
		articleIDList = []
		for article in self.ARTICLE_List:
			driver = webdriver.PhantomJS()
			r = driver.get(article)
			pageSource = driver.page_source
			soup = bs4(pageSource, 'html.parser')
			news = soup.find(class_ = 'main-container')
			content = ""
			title = str(news.find('p').text)
			time = re.split('/', news.find(class_ ='date-display-single').text)
			datetime = '/'.join(time[:3])+' 00:00'
			article = news.find(class_ = 'node node-post node-promoted clearfix').findAll('p')

			#filter fault news
			if t.strftime('%Y/%m/%d', t.localtime()) not in datetime:
				continue
			else:
				pass

			for contents in article:
				content +=  contents.text

			articleID = ''.join(time)+'00000'
			while articleID in articleIDList:
				articleID = str(int(articleID)+1)
			articleIDList.append(articleID)
			articleID = 'cld'+articleID
			for contents in article:
				content +=  contents.text
			self.NEWS_Lists.append([articleID, article, title, datetime, content])
		return self.NEWS_Lists