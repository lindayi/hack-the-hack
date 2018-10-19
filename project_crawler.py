import requests
import json
import logging
from multiprocessing import Pool
from multiprocessing_logging import install_mp_handler
import math
from util import str_escape
from kafka import KafkaProducer
import configparser

def fetch_page_num():
	"""Fetching how many projects are available"""
	
	try:
		init_url = "https://devpost.com/software/search?page=1"
		html_doc = requests.get(init_url)
		response_json = json.loads(html_doc.text)
		return int(math.ceil(response_json["total_count"] / len(response_json["software"])))
	except:
		raise RuntimeError("Failed to get total number of pages")

def fetch_single_page(page_num):
	"""Fetching projects on a single page and send it to Kafka"""
	
	config = configparser.ConfigParser()
	config.read("hth.properties")
	
	try:
		producer = KafkaProducer(bootstrap_servers=config.get('KafkaConfig', 'bootstrap_servers'), value_serializer=lambda m: json.dumps(m).encode('utf-8'))
		
		init_url = "https://devpost.com/software/search?page="
		html_doc = requests.get(init_url + str(page_num))
		response_json = json.loads(html_doc.text)
		
		if (len(response_json["software"]) > 0):
			for project in response_json["software"]:
				tmp_project = {}
				tmp_project["slug"] = project["slug"]
				tmp_project["url"] = project["url"]
				tmp_project["title"] = str_escape(project["name"])
				tmp_project["winner"] = str(int(project["winner"]))
				tmp_project["tagline"] = "" if project["tagline"] is None else str_escape(project["tagline"])
				tmp_project["teamsize"] = "0" if project["members"] is None else str(len(project["members"]))
				tmp_project["technique"] = "[]" if project["tags"] is None else str_escape(str(project["tags"]))
				
				producer.send('project_list_test', tmp_project)
				producer.flush()
			
			logging.info("Finished page %d", page_num)
			
	except Exception as e:
		logging.error("Unknown error on page %d", page_num, exc_info=True)
	
def main():
	logging.basicConfig(filename='crawler_project.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	install_mp_handler()

	nprocess = 16
	pool = Pool(nprocess)
	results = pool.map(fetch_single_page, range(1, fetch_page_num()))

if __name__ == '__main__':
	main()