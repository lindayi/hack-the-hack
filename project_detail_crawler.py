import requests
import json
import logging
from multiprocessing import Pool
from multiprocessing_logging import install_mp_handler
from util import str_escape
from kafka import KafkaProducer, KafkaConsumer
from bs4 import BeautifulSoup
import configparser

class ProjectDetailCrawler():
	'''Creating consumer pool to fill in missing details of projects'''
	
	def __init__(self, consumer_id):
		'''Initialization'''
		
		config = configparser.ConfigParser()
		config.read("hth.properties")
		
		self.__id = consumer_id
		self.__producer = KafkaProducer(bootstrap_servers=config.get('KafkaConfig', 'bootstrap_servers'), value_serializer=lambda m: json.dumps(m).encode('utf-8'))
		self.__consumer = KafkaConsumer('project_list_test', group_id='project_list_consumer', bootstrap_servers=config.get('KafkaConfig', 'bootstrap_servers'), 
										auto_offset_reset='earliest', value_deserializer=lambda m: json.loads(m.decode('utf-8')))
		self.__project = None
		logging.info("Consumer %d - initialized", self.__id)
		
	def crawl_project_detail(self):
		'''Crawl project details'''
		
		logging.info("Consumer %d - start project %s", self.__id, self.__project["slug"])
		init_url = "https://devpost.com/software/"
		html_doc = requests.get(init_url + self.__project["slug"])
		page = BeautifulSoup(html_doc.text, "lxml")
		try:
			self.__project["description"] = str_escape(page.find(id="app-details-left").find('div', class_ = None, id = None).get_text().strip())

			try:
				self.__project["hackathon_alias"] = str_escape(page.find(class_="software-list-content").p.a["href"][8:][:-13])
			except:
				self.__project["hackathon_alias"] = ""
				
			logging.info("Consumer %d - finished crawling project %s", self.__id, self.__project["slug"])
			
			self.__producer.send('project_persistent', self.__project)
			self.__producer.flush()
			
			logging.info("Consumer %d - finished sending project %s: %s", self.__id, self.__project["slug"], json.dumps(self.__project))
			
		except Exception as e:
			logging.error("Unknown error for project %s", self.__project["slug"], exc_info=True)
	
	def start_consumer(self):
		'''Consume project list in Kafka'''
		
		for msg in self.__consumer:
			self.__project = msg.value
			self.crawl_project_detail()
	
	def __del__(self):
		'''Closing Kafka connections'''
		
		self.__producer.close()
		self.__consumer.close()

def consumer_pool(consumer_id):
	crawler = ProjectDetailCrawler(consumer_id)
	crawler.start_consumer()

def main():
	logging.basicConfig(filename='crawler_project_detail.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	install_mp_handler()

	nprocess = 16
	pool = Pool(nprocess)
	results = pool.map(consumer_pool, range(1, nprocess + 1))

if __name__ == '__main__':
	main()