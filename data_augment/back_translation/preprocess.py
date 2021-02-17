from ..tb_utils.nlp import WordTokenizer
from ..data_process.html_text_process import txt_io
import os, codecs
import subprocess, concurrent.futures

LANG = "fra"
tokenizer = WordTokenizer(LANG)

def _tokenize_text(text):
    return " ".join(tokenizer.tokenize(text))

def tokenize_texts(texts):
    """ Tokenize texts using multiprocessing to speed up.
    :param texts: humanized texts.
    :param lang: text language
    :return: tokenized texts
    """
    print("\n\tTokenizing Texts...")

    max_threads = int(0.8 * os.cpu_count())
    size = max(int(len(texts) / max_threads), 1)
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_threads) as executor:
        tok_texts = list(executor.map(_tokenize_text, texts, chunksize=size))

    # tok_texts = [" ".join(self.tokenizer.tokenize(text)) for text in texts]
    return tok_texts


if __name__ == '__main__':

    file = "/linguistics/ethan/Canlii_data/historic_html/canlii_monolingual_final.fra"
    output_file = '/linguistics/ethan/Canlii_data/historic_html/canlii_monolingual_final.tok.fra'
    # with codecs.open(file, 'r') as f:
    #     lines = f.readlines()

    lines = txt_io(file, action='r')
    res = tokenize_texts(lines)
    txt_io(output_file, action='w', write_lines=res)
