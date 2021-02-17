from gensim import corpora, models, similarities
import os


def save_tfidf_similarities(dict_dir, vector_dir, save_tfidf, save_similarities):

    dictionary = corpora.Dictionary.load(dict_dir)
    corpus_vector = corpora.MmCorpus(vector_dir)

    feature_cnt = len(dictionary.token2id)
    print("Generating TFIDF...")
    ex_tfidf = models.TfidfModel(corpus_vector, smartirs='nnc')

    print("Generating Similarities...")
    ex_similarities = similarities.SparseMatrixSimilarity(ex_tfidf[corpus_vector],
                                                          num_features=feature_cnt)

    ex_tfidf.save(save_tfidf)
    ex_similarities.save(save_similarities)


if __name__ == '__main__':

    rootpath = '/linguistics/ethan/Alexa_text_mining_repos/master/alexa_text_mining/model'
    dict_dir = os.path.join(rootpath, 'Sedar_ALL.dict')
    vector_dir = os.path.join(rootpath, 'Sedar_ALL.mm')

    save_tfidf = os.path.join(rootpath, 'similarities.tfidf ')
    save_similarities = os.path.join(rootpath, 'similarities.similarities')
    save_tfidf_similarities(dict_dir, vector_dir, save_tfidf, save_similarities)
