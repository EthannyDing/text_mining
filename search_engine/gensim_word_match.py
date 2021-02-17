from gensim import corpora, models, similarities
from gensim.matutils import cossim
from gensim.utils import simple_preprocess, SaveLoad
import numpy as np, pandas as pd, os, time, codecs, json, pickle
import itertools
from pathlib import Path

class GensimWordMatch(object):
    """Build the class to match most similar TM from Sedar corpus.
        Steps to build:
            1. Set up a dictionary or load pre-constructed dictionary.
            2. Set up vector value of each sentence in corpus or load pre-constructed vector.
            3. Split each input sentence into tokens and calculate its vector value
            4. Get cossim value of input vector with each vector of corpus TM.
            5. Select the highest cossim value and its corresponding corpus TM."""

    def __init__(self, bitext_corpus,
                       serialize_dict=None,
                       serialize_tfidf=None,
                       serialize_similarities=None,
                       preload=False):

        # self.bitext_corpus = bitext_corpus
        self.serialize_dict = serialize_dict
        self.serialize_tfidf = serialize_tfidf
        self.serialize_similarities = serialize_similarities

        self.dictionary = None
        self.tfidf = None
        self.similarities = None

        # if (serialize_dict is not None) and (serialize_vector is not None):
        print("Reading Corpus Data...")
        with codecs.open(bitext_corpus[0], 'r', encoding='utf8') as f:
            self.eng_corpus = f.readlines()  # Not applicable to numpy array for Sedar 37M data.
        with codecs.open(bitext_corpus[1], 'r', encoding='utf8') as f:
            self.fra_corpus = f.readlines()  # , dtype='<U5'
        self.corpus_len = len(self.eng_corpus)

        if preload:
            self.preload_models()
        else:
            self.setup_models()

    def preload_models(self):

        start = time.time()
        print("Preloading models...\n")

        # self.dictionary = corpora.Dictionary.load(self.serialize_dict)
        self.dictionary = SaveLoad.load(str(self.serialize_dict))
        print("\tDictionary loaded.")

        self.tfidf = SaveLoad.load(str(self.serialize_tfidf))
        print("\tTFIDF loaded.")

        self.similarities = SaveLoad.load(str(self.serialize_similarities))
        print("\tSimilarities loaded.")

        # self.corpus_vector = corpora.MmCorpus(serialize_vector)
        print("\tPreloading Completed. time cost: {}".format(round(time.time() - start, 2)))

    def setup_models(self):

        start = time.time()
        print("Preparing corpus dictionary and vector...")

        #corpus_documents = [str(src).split() for src in self.eng_corpus]
        corpus_documents = [simple_preprocess(str(src)) for src in self.eng_corpus]
        self.dictionary = corpora.Dictionary(corpus_documents)
        corpus_vector = [self.dictionary.doc2bow(tokens) for tokens in corpus_documents]
        print("\tCorpus dictionary and vector completed, time cost: {}".format(round(time.time() - start, 2)))

        start = time.time()
        feature_cnt = len(self.dictionary.token2id)
        self.tfidf = models.TfidfModel(corpus_vector, smartirs='nnc')
        self.similarities = similarities.SparseMatrixSimilarity(self.tfidf[corpus_vector],
                                                                num_features=feature_cnt)
        print("\tTFIDF and similarity matrix completed, time cost: {}".format(round(time.time() - start, 2)))

        print("\nSerializing corpus dictionary, tfidf and similarities... ")
        self.dictionary.save(str(self.serialize_dict))
        self.tfidf.save(str(self.serialize_tfidf))
        self.similarities.save(str(self.serialize_similarities))
        # corpora.MmCorpus.serialize(self.serialize_vector, self.corpus_vector)
        print("Serialization done.")

    def transform(self, input_texts):
        """Transform input text strings into vectors"""
        input_documents = [simple_preprocess(str(src)) for src in input_texts]
        input_vectors = [self.dictionary.doc2bow(tokens) for tokens in input_documents]

        return input_vectors

    def match(self, input_vectors):
        """Get the index of best candidate TM for each input source text."""

        start = time.time()
        total_number_vectors = len(input_vectors)
        best_indexes = np.zeros(total_number_vectors, dtype='int')
        best_scores = np.zeros(total_number_vectors)
        # for i, input_vector in enumerate(input_vectors):
        #     if (i+1) % 50 == 0:
        #         print("\tProgress: {} / {}".format(i + 1, total_number_vectors))
        #     sims = self.similarities[self.tfidf[input_vector]]
        #     best_indexes[i] = np.argmax(sims)
        #     best_scores[i] = np.max(sims)
        similarities = self.similarities[self.tfidf[input_vectors]]
        for i, sim in enumerate(similarities):
            best_indexes[i] = np.argmax(sim)
            best_scores[i] = np.max(sim)

        print("\tTime cost for finding best match and score:{} sec".format(time.time() - start))
        return best_indexes, best_scores

    def match_input_tm(self, inputFile, outputFile):

        print("Searching fuzzy match of input segments...")
        start = time.time()

        df_source = pd.read_excel(inputFile, converters={'source': str})
        df_source = df_source['source'].to_numpy(dtype=str)

        input_vectors = self.transform(df_source)
        best_indexes, best_scores = self.match(input_vectors)

        # best_corpus_src = self.eng_corpus[best_indexes]
        # best_corpus_tgt = self.fra_corpus[best_indexes]
        best_corpus_src = [self.eng_corpus[i] for i in best_indexes]
        best_corpus_tgt = [self.fra_corpus[i] for i in best_indexes]
        print("Searching done: time cost {} sec".format(time.time() - start))

        output_df = pd.DataFrame({"source": df_source,
                                  "Best_candidate_src": best_corpus_src,
                                  "Best_candidate_tgt": best_corpus_tgt,
                                  "Best_score": best_scores})
        output_df.to_excel(outputFile, header=True, index=None)


def test_small():

    bitext_corpus = [Path.joinpath(Path(__file__).parent, 'data', 'clean_10000.eng'),
                     Path.joinpath(Path(__file__).parent, 'data', 'clean_10000.fra')]

    serialize_dict = Path.joinpath(Path(__file__).parent, 'model', 'sample_10000/clean_10000.dict')
    serialize_tfidf = Path.joinpath(Path(__file__).parent, 'model', 'sample_10000/clean_10000.tfidf')
    serialize_similarities = Path.joinpath(Path(__file__).parent, 'model', 'sample_10000/clean_10000.sim')

    client_file = Path.joinpath(Path(__file__).parent, 'data', 'final_client_merge_dedup_cleaned.xlsx')
    client_output = Path.joinpath(Path(__file__).parent, 'data', 'final_client_merge_dedup_cleaned.res1.xlsx')

    start_gwm = time.time()

    gwm = GensimWordMatch(bitext_corpus,
                          serialize_dict=serialize_dict,
                          serialize_tfidf=serialize_tfidf,
                          serialize_similarities=serialize_similarities,
                          preload=True)
    gwm.match_input_tm(client_file, client_output)

    end_gwm = time.time()
    print("Total time cost: {}".format(round(end_gwm - start_gwm, 2)))

def test_sedar_match():

    # bitext_corpus = ['/linguistics/ethan/Bicleaner/Sedar_Jobs/Sedar_cleaned_P0_P1.merge_dedup.eng',
    #                  '/linguistics/ethan/Bicleaner/Sedar_Jobs/Sedar_cleaned_P0_P1.merge_dedup.fra']
    bitext_corpus = ['/linguistics/ethan/Bicleaner/Client_TM/CPA_accounting/deep_cleaned/cpa_accouting.eng',
                     '/linguistics/ethan/Bicleaner/Client_TM/CPA_accounting/deep_cleaned/cpa_accouting.fra']

    serialize_dict = '/linguistics/ethan/Alexa_text_mining_repos/Models/CpaAccounting/cpa_accounting.dict'
    serialize_tfidf = '/linguistics/ethan/Alexa_text_mining_repos/Models/CpaAccounting/cpa_accounting.tfidf '
    serialize_similarities = '/linguistics/ethan/Alexa_text_mining_repos/Models/CpaAccounting/cpa_accounting.sim'

    client_file = '/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/client/cpa_accounting/Client_converted/556-201029-036.xlsx'
    client_output = '/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/client/cpa_accounting/556-201029-036.matched.xlsx'

    start_gwm = time.time()

    gwm = GensimWordMatch(bitext_corpus,
                          serialize_dict=serialize_dict,
                          serialize_tfidf=serialize_tfidf,
                          serialize_similarities=serialize_similarities,
                          preload=True)
    gwm.match_input_tm(client_file, client_output)

    end_gwm = time.time()
    print("Total time cost: {}".format(round(end_gwm - start_gwm, 2)))


if __name__ == '__main__':
    # test_small()
    test_sedar_match()

