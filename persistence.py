from multiprocessing import Pool
import MySQLdb
import json
from kafka import KafkaConsumer
import configparser

class Persistence():
	'''Creating consumer pool to persist data'''
	
	def __init__(self, consumer_id, topics):
		'''Initialization'''
		
		config = configparser.ConfigParser()
		config.read("hth.properties")
		
		self._id = consumer_id
		self._consumer = KafkaConsumer(topics, group_id=topics+'_consumer', bootstrap_servers=config.get('KafkaConfig', 'bootstrap_servers'), 
										auto_offset_reset='earliest', value_deserializer=lambda m: json.loads(m.decode('utf-8')))

		self._db = MySQLdb.connect(config.get('DBConfig', 'db_server'), config.get('DBConfig', 'db_user'), config.get('DBConfig', 'db_pass'), config.get('DBConfig', 'db_database'))
		self._cursor = self._db.cursor()
	
	def persist_item(item):
		pass
	
	def start_consumer(self):
		'''Consume items in Kafka'''
		
		for msg in self._consumer:
			item = msg.value
			self.persist_item(item)
	
	def __del__(self):
		'''Closing Kafka connections'''
		
		self._consumer.close()