from multiprocessing import Pool
from multiprocessing_logging import install_mp_handler
import MySQLdb
import json
from kafka import KafkaConsumer
from persistence import Persistence
import logging

class HackathonPersistence(Persistence):
	'''Hackathon data persistence'''
	
	def __init__(self, consumer_id):
		'''Initialize through Persistence'''
		
		Persistence.__init__(self, consumer_id, 'hackathon_persistent')
		logging.info("Consumer %d - initialized", self._id)
		
	def persist_item(self, item):
		'''Save project to database'''
		
		try:
			sql = 'DELETE FROM hackathon_test WHERE hackathon_alias = "' + item["hackathon_alias"] + '"' 
			self._cursor.execute(sql)
			self._db.commit()
			sql = 'INSERT INTO hackathon_test (hackathon_alias, title, judges, start_date, end_date) VALUES ("' + item["hackathon_alias"] + '", "' + item["title"] + '", "' + str(item["judge_list"]) + '", "' + str(item["startdate"]) + '", "' + str(item["enddate"]) + '")'
			self._cursor.execute(sql)
			self._db.commit()
			
		except MySQLdb.Error as e:
			try:
				logging.error("MySQL Error [%d]: %s; Error SQL: %s", e.args[0], e.args[1], sql)
			except IndexError:
				logging.error("MySQL Error %s", str(e))
	
def consumer_pool(consumer_id):
	consumer = HackathonPersistence(consumer_id)
	consumer.start_consumer()

def main():
	logging.basicConfig(filename='hackathon_persistence.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	install_mp_handler()

	nprocess = 1
	pool = Pool(nprocess)
	results = pool.map(consumer_pool, range(1, nprocess + 1))

if __name__ == '__main__':
	main()