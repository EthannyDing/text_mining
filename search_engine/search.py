import os, pandas as pd, codecs, tqdm, time
import pickle
import numpy as np
import nmslib
from configparser import ConfigParser
from rank_bm25 import BM25Okapi
from gensim.models.fasttext import FastText
from search_psql import SearchPSQL
import spacy

EN_SPACY_MODEL = 'en_core_web_lg'
FR_SPACY_MODEL = 'fr_core_news_lg'


class BuildSearchEngine:
    """This class is dedicated to build a text search engine by
        1. Building BM25 weighted document vectors for corpus documents.
        2. Given input query, calculate cosine similarity as score function and select n best matches."""

    def __init__(self, configPath):

        self.cp = ConfigParser()
        self.cp.read(configPath)

        self.lang = self.cp.get("Language", "source_lang")

        self.src_corpus_path = self.cp.get("Training", "src_corpus_path")
        self.tgt_corpus_path = self.cp.get("Training", "tgt_corpus_path")
        self.embedding_dim = self.cp.getint("Training", "embedding_dim")
        self.distance_fun = self.cp.get("Training", "distance_fun")
        self.train_epoch = self.cp.getint("Training", "train_epoch")

        self.fasttext_model_path = self.cp.get("Serialization", "fasttext_model_path")
        self.corpus_vector_path = self.cp.get("Serialization", "corpus_vector_path")
        self.index_path = self.cp.get("Serialization", "index_path")

        self.corpus = []
        self.ft_model = None
        self.bm25 = None
        self.corpus_vecs = []

        self.index = nmslib.init(method='hnsw', space=self.distance_fun)
        # self.check_pretrained()

    def check_pretrained(self):
        """Preload any pretrained models if any to avoid re-training/"""
        try:
            if os.path.exists(self.fasttext_model_path):
                self.reload_model(self.fasttext_model_path)

            if os.path.exists(self.corpus_vector_path):
                self.reload_corpus_vector(self.corpus_vector_path)
        except:
            pass

    def save_model(self, model_dir):
        """Save trained FastText model."""
        print("\nSaving fast text model...")
        self.ft_model.save(model_dir)

    def reload_model(self, model_dir):
        """Reload model from saved file"""
        print("Reloading FastText model...")
        self.ft_model = FastText.load(model_dir)

    def save_corpus_vector(self, vector_dir):
        """save weighted document vector"""
        print("\tChecking if each document is correctly converted into vector...")
        length = len(self.corpus_vecs)
        for i in range(length):
            try:
                if self.corpus_vecs[i].shape[0] != 100:
                    print("Index {} doesn't have 100D".format(i))
                    self.corpus_vecs[i] = np.zeros(100, dtype='float32')
            except:
                print("Index {} is nan".format(i))
                self.corpus_vecs[i] = np.zeros(100, dtype='float32')

        print("\nSaving weighted corpus vector...")
        with open(vector_dir, "wb") as pickleFile:
            pickle.dump(self.corpus_vecs, pickleFile)

    def reload_corpus_vector(self, vector_dir):
        """reload weighted document vector from local file"""
        print("Reloading coorpus vector...")
        with open(vector_dir, 'rb') as pickleFile:
            self.corpus_vecs = pickle.load(pickleFile)
        print("")

    def save_index(self, index_dir):
        """save nmslib search index"""
        self.index.saveIndex(index_dir, save_data=True)

    def reload_index(self, index_dir):
        """load index from local file"""
        print("Reloading Index...")
        self.index.loadIndex(index_dir, load_data=True)

    def preprocess_corpus(self):
        """Create a list of cleaned and tokenized words for each document in the corpus"""

        with codecs.open(self.src_corpus_path, 'r') as f:
            self.corpus = f.readlines()

        if self.lang == 'eng':
            spacy_model = EN_SPACY_MODEL
        elif self.lang == 'fra':
            spacy_model = FR_SPACY_MODEL
        else:
            raise Exception("No spacy model available for language: {}".format(self.lang))

        nlp = spacy.load(spacy_model)
        tokenized_corpus = []
        print("\tTokenizing corpus documents...")
        for doc in nlp.pipe(self.corpus, n_threads=2, disable=["tagger", "parser", "ner"]):
            tok = [t.text.lower() for t in doc if (t.is_ascii and not t.is_punct and not t.is_space)]
            tokenized_corpus.append(tok)

        print("\tTokenizating Done.")
        return tokenized_corpus

    def train_model(self, tokenized_corpus):
        """Build a FastText word embedding model using Gensim FastText."""
        self.ft_model = FastText(sg=1,  # use skip-gram: usually gives better results
                                 size=self.embedding_dim,  # embedding dimension (default)
                                 window=10,  # window size: 10 tokens before and 10 tokens after to get wider context
                                 min_count=5,  # only consider tokens with at least n occurrences in the corpus
                                 negative=15,  # negative subsampling: bigger than default to sample negative examples more
                                 min_n=2,  # min character n-gram
                                 max_n=5)  # max character n-gram

        print("\tBuilding vocabulary from corpus")
        self.ft_model.build_vocab(tokenized_corpus)  # tok_text is our tokenized input text - a list of lists relating to docs and tokens respectivley

        print("\tTraining word embedding model")
        self.ft_model.train(tokenized_corpus,
                            epochs=self.train_epoch,
                            total_examples=self.ft_model.corpus_count,
                            total_words=self.ft_model.corpus_total_words)

    # def bm25_embedding(self, word):
    #     """Use weighted word embedding using BM25 function"""
    #     vector = self.ft_model[word]
    #     tf = self.bm25.doc_freqs[i][word]
    #     weight = (self.bm25.idf[word] * ((self.bm25.k1 + 1.0) * tf)) / \
    #              (self.bm25.k1 * (1.0 - self.bm25.b + self.bm25.b * (self.bm25.doc_len[i] / self.bm25.avgdl)) + tf)
    #     weighted_vector = vector * weight

    def build_weighted_document_vector(self, tokenized_corpus):
        """Build BM25 weighted document vector"""

        print("\tBuilding BM25 weighted document vector")
        for i, doc in enumerate(tokenized_corpus):
            doc_vector = []
            try:
                for word in doc:
                    vector = self.ft_model[word]
                    tf = self.bm25.doc_freqs[i][word]
                    weight = (self.bm25.idf[word] * ((self.bm25.k1 + 1.0) * tf)) / \
                             (self.bm25.k1 * (1.0 - self.bm25.b + self.bm25.b * (self.bm25.doc_len[i] / self.bm25.avgdl)) + tf)
                    weighted_vector = vector * weight
                    doc_vector.append(weighted_vector)

                doc_vector_mean = np.mean(doc_vector, axis=0)
            except:
                print("------Document {} failed to generate weighted vector.".format(i))
                doc_vector_mean = np.zeros(self.embedding_dim, dtype='float32')

            self.corpus_vecs.append(doc_vector_mean)

    def fit(self):
        """Build BM25 weighted document vector for input corpus."""
        tokenized_corpus = self.preprocess_corpus()
        print("\tCreating BM25 ")
        self.bm25 = BM25Okapi(tokenized_corpus)

        self.check_pretrained()

        if not self.ft_model:
            self.train_model(tokenized_corpus)
            self.save_model(self.fasttext_model_path)

        if not self.corpus_vecs:
            self.build_weighted_document_vector(tokenized_corpus)
            self.save_corpus_vector(self.corpus_vector_path)

    def create_index(self):
        """Create search engine index using nmslib"""
        print("\n\tCreating search engine index")
        data = np.vstack(self.corpus_vecs)

        # initialize a new index, using a HNSW index on Cosine Similarity

        self.index.addDataPointBatch(data)
        self.index.createIndex({'post': 2}, print_progress=True)

        self.save_index(self.index_path)
        print("\nSaving index...")
        print("Done.")

    # def serialize(self):
    #     """Serialize all fast text model, weighted corpus vector and index."""
    #
    #     print("\nSaving fast text model...")
    #     self.save_model(self.fasttext_model_path)
    #     print("Saving weighted corpus vector...")
    #     self.save_corpus_vector(self.corpus_vector_path)
    #     print("Saving index...")
    #     self.save_index(self.index_path)
    #     print("Done.")


class Serving(BuildSearchEngine):

    def __init__(self, configPath):
        super().__init__(configPath)
        self.sp = SearchPSQL(configPath)
        self.reload()
        self.all_website_options = ",".join(["segments." + col for col in self.sp.tables["segments"]] +
                                            ["website." + col for col in self.sp.tables["website"][1:-1]] +
                                            ["ycc_domains." + col for col in self.sp.tables["ycc_domains"][1:-1]])
        self.all_file_options = ",".join(["segments." + col for col in self.sp.tables["segments"]] +
                                         ["file." + col for col in self.sp.tables["file"][1:-1]] +
                                         ["ycc_domains." + col for col in self.sp.tables["ycc_domains"]][1:-1])
        self.all_website_keys = self.sp.tables["segments"] + self.sp.tables["website"][1:] + self.sp.tables["ycc_domains"][1:-1]
        self.all_file_keys = self.sp.tables["segments"] + self.sp.tables["file"][1:] + self.sp.tables["ycc_domains"][1:-1]

    def reload(self):
        """Reload fast text model and index."""
        print("Reloading fast text model and index...")
        self.reload_model(self.fasttext_model_path)
        self.reload_index(self.index_path)
        print("Reloading complete.")

    def vectorize_input(self, text):
        """Convert user input into average fast text vector"""
        text = text.lower().split()  # lower and tokenize query
        vector = [self.ft_model[vec] for vec in text]  # get word embedding
        vector = np.mean(vector, axis=0)  # get document vector

        return vector

    def search(self, text, n_best=5, domain="Sedar"):
        """search n_best matches for the given query"""
        vector = self.vectorize_input(text)
        ids, distances = self.index.knnQuery(vector, k=n_best)

        results = []
        for id in ids:
            # if advanced:
            #     try:
            #         # query = "SELECT {} FROM segment WHERE query_id = {}".format(self.all_website_options, id+1)
            #         query = """select {} from ((segments inner join website on segments.website_id = website.website_id)
            #                     inner join ycc_domains on website.ycc_id = ycc_domains.ycc_id )
            #                     where segments.query_id = {}""".format(self.all_website_options, id+1)
            #         res = self.sp.fetch_records(query)
            #         res = {key: value for key, value in zip(self.all_website_keys, res)}
            #     except:
            #         query = "SELECT {} FROM segment WHERE query_id = {}".format(self.all_file_options, id + 1)
            #         res = self.sp.fetch_records(query)
            #         res = {key: value for key, value in zip(self.all_file_keys, res)}
            # else:
            #     query = "SELECT * FROM segments WHERE query_id = {}".format(id + 1)
            #     res = self.sp.fetch_records(query)
            #     res = {key: value for key, value in zip(self.sp.tables['segments'], res)}
            if domain == "Sedar":
                fields = ["src_lang", "src_text", "tgt_lang", "tgt_text", "quality", "type", "uri", "last_update"]
                # "src_lang, src_text, tgt_lang, tgt_text, quality, type, uri, lasr_update"
                query = """select {}
                           from ((segments inner join website on segments.website_id = website.website_id)
                                inner join ycc_domains on website.ycc_id = ycc_domains.ycc_id )
                           where segments.query_id = {}""".format(",".join(fields), id + 1)
                res = self.sp.fetch_records(query)
                res = dict(zip(fields, res))
                # res = {key: value for key, value in zip(fields, res)}
            else:
                raise ValueError("Currently only supprt Sedar domain.")

            results.append(res)

        return results


def test_build():
    # corpus_dir = "/linguistics/ethan/training_data/Sedar_Jobs/Sedar_cleaned_202101.merge_dedup.eng"
    # lang = 'eng'
    # model_dir = "/linguistics/ethan/Alexa_text_mining_repos/Models/SedarSearchEngine/ENG/sedar.eng.model"
    # vector_dir = "/linguistics/ethan/Alexa_text_mining_repos/Models/SedarSearchEngine/ENG/doc_vector.eng.pkl"
    # index_dir = "/linguistics/ethan/Alexa_text_mining_repos/Models/SedarSearchEngine/ENG/seadar.eng.index"

    configPath = "./config/search.conf"

    start = time.time()
    se = BuildSearchEngine(configPath)

    # se.fit()
    se.create_index()

    print("Total time consumed: {} min".format((time.time()-start) // 60))


def test_serve():

    configPath = "./config/search.conf"
    serving = Serving(configPath)


if __name__ == "__main__":

    test_build()
