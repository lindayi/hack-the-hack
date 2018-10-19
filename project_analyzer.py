from multiprocessing import Pool, Queue
import MySQLdb
import json
from datetime import datetime
import re
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import nltk
from nltk.stem.porter import PorterStemmer
from stop_words import get_stop_words
import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import csv
import configparser
import logging

class ProjectAnalyzer():
	'''Analyzing projects'''
	
	def __init__(self):
		'''Initialization'''
		
		config = configparser.ConfigParser()
		config.read("hth.properties")

		self._db = MySQLdb.connect(config.get('DBConfig', 'db_server'), config.get('DBConfig', 'db_user'), config.get('DBConfig', 'db_pass'), config.get('DBConfig', 'db_database'))
		self._cursor = self._db.cursor()
	
	def keyword_extract():
		'''Extract keywords from tagline using tf-idf'''
		
		tagline_doc = []
		slug_list = []
		sql = "SELECT project_slug, tagline FROM project"
		self._cursor.execute(sql)
		results = self._cursor.fetchall()
		for row in results:
			tagline_doc.append(row[1])
			slug_list.append(row[0])
			
		vectorizer = TfidfVectorizer(stop_words = "english", max_features = 1000)
		response = vectorizer.fit_transform(tagline_doc)
		keyword_array = vectorizer.inverse_transform(response)
		
		for i in range(0, len(keyword_array), 1):
			try:
				sql = "UPDATE project SET keywords = '" + json.dumps(keyword_array[i].tolist()) + "' WHERE project_slug = '" + slug_list[i] + "'"
				self._cursor.execute(sql)
				self._db.commit()
			except MySQLdb.Error as e:
				try:
					logging.error("MySQL Error [%d]: %s; Error SQL: %s", e.args[0], e.args[1], sql)
				except IndexError:
					logging.error("MySQL Error %s", str(e))
	
	def top_technique():
		'''Extract top techniques used in hackathons'''
		
		tech = {}
		sql = "SELECT technique FROM project"
		self._cursor.execute(sql)
		results = self._cursor.fetchall()
		for row in results:
			tmp_list = ast.literal_eval(row[0])
			for tech_item in tmp_list:
				if tech_item in tech:
					tech[tech_item] += 1
				else:
					tech[tech_item] = 1
		return sorted(tech.iteritems(), key=(lambda k,v: v,k), reverse=True)

	def top_keyword():
		'''Extract top keywords in projects'''
		
		tech = {}
		sql = "SELECT keywords FROM project"
		self._cursor.execute(sql)
		results = self._cursor.fetchall()
		for row in results:
			tmp_list = ast.literal_eval(row[0])
			for tech_item in tmp_list:
				if tech_item in tech:
					tech[tech_item] += 1
				else:
					tech[tech_item] = 1
		return sorted(tech.iteritems(), key=lambda (k,v): (v,k), reverse=True)
				
	def top_judge():
		'''Extract judges with the most judged hackathons'''
		
		judge = {}
		sql = "SELECT judges FROM hackathon"
		self._cursor.execute(sql)
		results = self._cursor.fetchall()
		for row in results:
			tmp_list = ast.literal_eval(row[0])
			for judge_item in tmp_list:
				field, value = judge_item.items()[0]
				if field in judge:
					judge[field] += 1
				else:
					judge[field] = 1
		return sorted(judge.iteritems(), key=(lambda k,v: v,k), reverse=True)
		
	def data_preparation():
		'''Generate dataset'''
		stop_words = get_stop_words('en')
		p_stemmer = PorterStemmer()
		
		tagline_doc = []
		slug_list = []
		tagdoc_list = []
		teamsize_dict = {}
		winner_dict = {}
		sql = "SELECT project_slug, tagline, teamsize, winner FROM project"
		self._cursor.execute(sql)
		results = self._cursor.fetchall()
		for row in results:
			try:
				word_list = nltk.word_tokenize(row[1].strip().lower())
			except:
				continue
				
			try:
				filtered_sentence = [w for w in word_list if not w in stop_words]
			except:
				filtered_sentence = word_list
			
			try:
				filtered_sentence = [p_stemmer.stem(w) for w in filtered_sentence]
			except:
				filtered_sentence = word_list
			
			tagline_doc.append(filtered_sentence)
			slug_list.append(row[0])
			teamsize_dict[row[0]] = row[2]
			winner_dict[row[0]] = row[3]
		
			tagdoc_list.append(TaggedDocument(filtered_sentence, [row[0]]))
		
		model = Doc2Vec(tagdoc_list, workers=8)
		model.save('model.doc2vec')
		model.save_word2vec_format('data.doc2vec', doctag_vec=True, word_vec=False, binary=False)
		
		with open('data.doc2vec', 'r') as data_raw, open("data.csv", "w") as data_dest:
			col_name = "project_slug,"
			for _ in range(0,100):
				col_name += " ,"
			col_name += " teamsize, winner\n"
			data_dest.write(col_name)

			for line in data_raw:
				tmp_slug = line.split(" ")[0]
				new_line = line.replace(" ", " ,").replace("\n", "") + ", " + teamsize_dict[tmp_slug] + ", " + winner_dict[tmp_slug] + "\n"
				data_dest.write(new_line)
	
	def load_pred():
		'''Load prediction results to db'''
		
		with open('pred.output.csv', 'rb') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
			for row in csvreader:
				if row[1] == "pred":
					continue
				slug = row[0]
				pred = row[1]
				try:
					sql = "UPDATE project SET predict = " + pred + " WHERE project_slug = '" + slug + "'"
					self._cursor.execute(sql)
					self._db.commit()
				except MySQLdb.Error as e:
					try:
						logging.error("MySQL Error [%d]: %s; Error SQL: %s", e.args[0], e.args[1], sql)
					except IndexError:
						logging.error("MySQL Error %s", str(e))
					
	def infer_new_doc(tagline, project_slug):
		'''Create new vector for realtime prediction'''
		
		stop_words = get_stop_words('en')
		p_stemmer = PorterStemmer()
		
		word_list = nltk.word_tokenize(tagline.strip().lower())
		filtered_sentence = [w for w in word_list if not w in stop_words]
		filtered_sentence = [p_stemmer.stem(w) for w in filtered_sentence]
		model = Doc2Vec.load('model.doc2vec')
		vector = model.infer_vector(filtered_sentence)
		
		return vector
	
def main():
	logging.basicConfig(filename='project_analyzer.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

	analyzer = ProjectAnalyzer()
	analyzer.data_preparation()

if __name__ == '__main__':
	main()