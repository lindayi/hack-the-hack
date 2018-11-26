from nltk.stem.porter import PorterStemmer
from stop_words import get_stop_words
import nltk
from gensim.models.doc2vec import Doc2Vec

def infer_new_doc(tagline, project_slug):
	stop_words = get_stop_words('en')
	p_stemmer = PorterStemmer()

	word_list = nltk.word_tokenize(tagline.strip().lower())
	filtered_sentence = [w for w in word_list if not w in stop_words]
	filtered_sentence = [p_stemmer.stem(w) for w in filtered_sentence]
	model = Doc2Vec.load('plumber/model.doc2vec')
	vector = model.infer_vector(filtered_sentence)

	return vector