from util import str_escape
import time
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing_logging import install_mp_handler
import MySQLdb
import json
from datetime import datetime
import re
import logging
from kafka import KafkaProducer
import configparser

class HackathonCrawler():
	'''Hackathon Crawler class'''
	
	def __init__(self):
		'''Initialization'''
		
		config = configparser.ConfigParser()
		config.read("hth.properties")
		
		self.__producer = KafkaProducer(bootstrap_servers=config.get('KafkaConfig', 'bootstrap_servers'), value_serializer=lambda m: json.dumps(m).encode('utf-8'))

	@staticmethod
	def date_convert(date_str):
		'''Parse Devpost datetime format'''
		try:
			tmp_date = re.search(".*(am|pm)", date_str).group(0)
			dateobj = datetime.strptime(tmp_date, "%Y %B %d at %I:%M%p")
			return dateobj
		except Exception as e:
			logging.error("Unknown error of date %s", tmp_date, exc_info=True)

	def crawl_hackathons(self, hackathon_alias):
		'''Crawl hackathons info'''

		init_url = "https://" + hackathon_alias + ".devpost.com/"
		html_doc = requests.get(init_url)
		page = BeautifulSoup(html_doc.text, "lxml")
		
		judge_list = []
		tmp_hackathon = {"hackathon_alias": hackathon_alias}
		
		try:
			# Extract hackathon title
			tmp_hackathon["title"] = page.find(property="og:site_name")["content"]
			
			# Extract judges
			judge_block = page.find_all(class_="challenge_judge")
			for judge in judge_block:
				judge_name = str_escape(judge.find("strong").get_text())
				judge_aff = str_escape(judge.find("i").get_text())
				judge_list.append({judge_name : judge_aff})
				
			tmp_hackathon["judge_list"] = judge_list
			
			# Extract start and end time
			year_text = page.find(class_="addthis_button_reddit")["addthis:url"]
			year_text = re.search("utm_campaign=.*\.([0-9]+).*utm_content", year_text).group(1)
			
			html_doc = requests.get(init_url + "details/dates")
			page = BeautifulSoup(html_doc.text, "lxml")
			
			date_list = page.find(class_="content-section").section.table.tbody.tr.find_all("td")
			startdate_text = date_list[1].get_text()
			enddate_text = date_list[2].get_text()
			
			tmp_hackathon["startdate"] = str(self.date_convert(year_text + " " + startdate_text))
			tmp_hackathon["enddate"] = str(self.date_convert(year_text + " " + enddate_text))
			
			# Send the hackathon to Kafka for persistence
			self.__producer.send('hackathon_persistent', tmp_hackathon)
			self.__producer.flush()

		except Exception as e:
			logging.error("Unknown error for hackathon %s", hackathon_alias, exc_info=True)
	
	def __del__(self):
		'''Closing Kafka connections'''
		
		self.__producer.close()

def producer_pool(hackathon_alias):
	crawler = HackathonCrawler()
	crawler.crawl_hackathons(hackathon_alias)

def main():
	# Read configs
	config = configparser.ConfigParser()
	config.read("hth.properties")
	
	db = MySQLdb.connect(config.get('DBConfig', 'db_server'), config.get('DBConfig', 'db_user'), config.get('DBConfig', 'db_pass'), config.get('DBConfig', 'db_database'))
	cursor = db.cursor()
	logging.basicConfig(filename='crawler_hackathon.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	install_mp_handler()
	
	# Get hackathon list
	hackathon_list = []

	sql = "SELECT DISTINCT hackathon_alias FROM project WHERE hackathon_alias != ''"
	cursor.execute(sql)
	results = cursor.fetchall()
	for row in results:
		hackathon_list.append(str(row[0]))

	# Start multiple processes as Hackathon Producer
	nprocess = 2
	pool = Pool(nprocess)
	results = pool.map(producer_pool, hackathon_list)

if __name__ == '__main__':
	main()
