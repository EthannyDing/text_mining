import pandas as pd, os, codecs, sys, regex as re
from pathlib import Path
from collections import defaultdict
from itertools import chain
import subprocess
import spacy
import concurrent.futures
from pyate import combo_basic

from pyate.term_extraction_pipeline import TermExtractionPipeline

base_dir = Path(os.path.abspath(__file__)).parent.parent.__str__()
sys.path.insert(0, base_dir)
from ..tb_utils.nlp import WordTokenizer, TextHumanizer, WordDetokenizer
from ..tb_utils.tm_fileparser import TmFileParser

SPACY_MAX_LEN = 10000000
EN_SPACY_MODEL = 'en_core_web_lg'
FR_SPACY_MODEL = 'fr_core_news_lg'


def find_word_index_of_term(source_text, term):
    """ Find word indices of source text that matches the given term.
    :param source_text: text from which match index are extracted
    :param term: match term
    :return: list.
        if no match, empty list.
        if matches, a list of all lists that match term
    """
    term_tokens = term.split()
    first_term_token = term_tokens[0]
    text_tokens = source_text.split()
    # assume only one occurance of term match.
    # searched = re.search(r'\b' + re.escape(term) + r'\b', source_text)
    # if searched:
    #
    #     start = 0
    #     first_term_range = [searched.span()[0], searched.span()[0] + len(first_term_token)]
    #     for i, word in enumerate(text_tokens):
    #         char_range = [start, start + len(word)]
    #         start = start + len(word) + 1
    #         if word == first_term_token and first_term_range == char_range:
    #             return list(range(i, i + len(term_tokens)))
    matched_word_index = []
    for searched in re.finditer(r'\b' + re.escape(term) + r'\b', source_text):

        start = 0
        first_term_range = [searched.span()[0], searched.span()[0] + len(first_term_token)]
        for i, word in enumerate(text_tokens):
            char_range = [start, start + len(word)]
            start = start + len(word) + 1

            if word == first_term_token and first_term_range == char_range:
                word_index = list(range(i, i + len(term_tokens)))
                matched_word_index.append(word_index)

    return matched_word_index


def find_terminology_pairs(src_tgt_forward_alignment, src_tgt_reverse_alignment, source_terms):
    """ Given source term, find its target term using fast alignment and matched word indices.
    :param src_tgt_forward_alignment: {source-target: forward-alignment} dict.
    :param src_tgt_reverse_alignment: {source-target: reverse-alignment} dict.
    :param source_terms (dataframe): terms of source langauge and pyate score.
    :return: terminology pairs.
    """
    print("\n\tSreaching for Terminologies.")
    final_terminologies = []
    for i, (src_term, score) in enumerate(zip(source_terms["source_term"], source_terms['score'])):  # find target term for each src term

        for (src, tgt), forward_align in src_tgt_forward_alignment.items():  # for each term, loop through all src text.

            src_word_indices = find_word_index_of_term(src, src_term)  # get src word indices of term
            if len(src_word_indices) == 1:  # check if multiple matches of term in the source text.
                src_indices = src_word_indices[0]
            # for src_indices in src_word_indices:

                tgt_indices = [forward_align.get(ind) for ind in src_indices]  # find tgt word indices.
                if None not in tgt_indices:  # check if one or more tgt indices mapping do not exist

                    tgt_indices = sorted(list(set(chain(*tgt_indices))))  # flat tgt indices (list of list) and remove duplicates and sort.
                    if tgt_indices == list(range(min(tgt_indices), max(tgt_indices) + 1)):  # check if tgt indices are consecutive.

                        reverse_align = src_tgt_reverse_alignment[(src, tgt)]
                        reverse_src_indices = set(chain(*[reverse_align.get(ind) for ind in tgt_indices]))
                        if set(src_indices) == reverse_src_indices:  # Finally reverse-check src word indices. if equal, consider

                            tgt_tokens = tgt.split()
                            tgt_term = " ".join([tgt_tokens[ti] for ti in tgt_indices])
                            term_pair = (src_term, tgt_term, score)
                            if term_pair not in final_terminologies:
                                final_terminologies.append(term_pair)
                                print("\tFind Terminology pair {}/{}:  {} -- {}".format(i+1, len(source_terms),
                                                                                        src_term, tgt_term))

    final_terminologies = sorted(final_terminologies, key=lambda x: x[2], reverse=True)

    return final_terminologies


class TbExtractor(object):

    def __init__(self, input_file, input_type, output_rootpath, output_prefix, srcLang='eng', tgtLang='fra'):

        self.input_file = input_file
        self.input_type = input_type

        self.output_rootpath = output_rootpath
        self.output_prefix = output_prefix
        self.srcLang = srcLang
        self.tgtLang = tgtLang

        self.max_threads = os.cpu_count()
        self.setup_path()
        self.setup_spacy()

    def setup_path(self):
        """Set up paths for temporary files used for fast align and paths of fast_align executables."""
        tb_base_dir = Path(os.path.abspath(__file__)).parent.__str__()
        tmp_folder = os.path.join(tb_base_dir, 'tmp', self.output_prefix)
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        self.af_input_path = os.path.join(tmp_folder, self.output_prefix + '.input')
        self.af_forward_path = os.path.join(tmp_folder, self.output_prefix + '.forward')
        self.af_reverse_path = os.path.join(tmp_folder, self.output_prefix + '.reverse')
        self.af_symmetrized_path = os.path.join(tmp_folder, self.output_prefix + '.symmetrized')

        self.af_executable_rootpath = os.path.join(tb_base_dir, "fast_align", "build")
        self.final_output_path = os.path.join(self.output_rootpath, self.output_prefix + '.xlsx')
        self.original_source_term_path = os.path.join(tmp_folder, self.output_prefix + 'src_terms.xlsx')

    def setup_spacy(self):
        """Set up Spacy model for later term extraction."""
        if self.srcLang == 'eng':
            nlp_model = EN_SPACY_MODEL
        elif self.srcLang == 'fra':
            nlp_model = FR_SPACY_MODEL
        else:
            raise Exception("No spacy model found for source language: {}".format(self.srcLang))

        self.nlp = spacy.load(nlp_model)
        self.nlp.max_length = SPACY_MAX_LEN
        self.nlp.add_pipe(TermExtractionPipeline())

    def output_result(self, terminologies):

        df = pd.DataFrame(terminologies, columns=['source', 'target', 'score'])
        df = df.drop_duplicates(subset=['source'])
        df.to_excel(self.final_output_path, header=True, index=None)

    def postprocess(self, terminologies):
        """Postprocess by detokenizing and disambiguating."""

        df = pd.DataFrame(terminologies, columns=['source', 'target', 'score'])

        print("\n\tDetokenizing...")
        df['source'] = self.humanize_texts(df['source'], self.srcLang)
        df['target'] = self.humanize_texts(df['target'], self.tgtLang)

        print("\n\tDisambiguating...")
        df = df.drop_duplicates(subset=['source'])

        return df

    def text_preprocess(self):
        """ Preprocess by Humanizing and tokenzing.
        :return: preprocessed source and target texts
        """
        tfp = TmFileParser(self.input_type)
        tfp.parse(self.input_file)

        srcTexts = self.humanize_texts(tfp.srcTexts, self.srcLang)
        tgtTexts = self.humanize_texts(tfp.tgtTexts, self.tgtLang)

        srcTexts = self.tokenize_texts(srcTexts, self.srcLang)
        tgtTexts = self.tokenize_texts(tgtTexts, self.tgtLang)

        return srcTexts, tgtTexts

    def _humanize_text(self, text):
        return self.humanizer.humanizeText(text)

    def _tokenize_text(self, text):
        return " ".join(self.tokenizer.tokenize(text))

    def humanize_texts(self, texts, lang='eng'):
        """ Humanize texts using multiprocessing to speed up.
        :param texts: raw texts
        :param lang: text language
        :return: humanized text
        """
        print("\n\tHumanizing {} Texts...".format(lang))
        self.humanizer = TextHumanizer(lang)

        # size = max(int(len(texts) / self.max_threads), 1)
        # with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_threads) as executor:
        #     clean_texts = list(executor.map(self._humanize_text, texts, chunksize=size))

        clean_texts = [self.humanizer.humanizeText(text) for text in texts]
        return clean_texts

    def tokenize_texts(self, texts, lang='eng'):
        """ Tokenize texts using multiprocessing to speed up.
        :param texts: humanized texts.
        :param lang: text language
        :return: tokenized texts
        """
        print("\n\tTokenizing {} Texts...".format(lang))
        self.tokenizer = WordTokenizer(lang)

        # size = max(int(len(texts) / self.max_threads), 1)
        # with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_threads) as executor:
        #     tok_texts = list(executor.map(self._tokenize_text, texts, chunksize=size))

        tok_texts = [" ".join(self.tokenizer.tokenize(text)) for text in texts]
        return tok_texts

    def _extract_terms(self, string):
        """Extract terms from string given using spacy_model and spacy pipeline.
        :param string: string from which terms are extracted.
        :return: extracted terms
        """
        doc = self.nlp(string)
        output = doc._.combo_basic.sort_values(ascending=False)
        # terms = set(output.index)

        return output

    def extract_source_terms(self, texts):
        """Extract terms from source texts using pyate library."""

        print("\n\tExtracting Source Terms...")
        joint_string = " ".join(texts)

        char_len = len(joint_string)
        truncated_parts = (char_len // SPACY_MAX_LEN) + 1

        df = pd.DataFrame({"source_term": [], "score": []})
        for i in range(truncated_parts):
            substring = joint_string[i*SPACY_MAX_LEN: min((i+1)*SPACY_MAX_LEN, char_len)]
            terms = self._extract_terms(substring)
            df = pd.concat([df, pd.DataFrame({"source_term": list(terms.index), "score": list(terms)})])
            # source_terms = source_terms.union(terms)

        print("\t\t{} source terms extracted.".format(len(df)))

        print("\n\t\tSaving extracted source terms.")
        # df = pd.DataFrame({'source_term': list(source_terms)})
        df.to_excel(self.original_source_term_path, header=True, index=None)
        # source_terms = set(df["source_term"])

        return df

    def prepare_input_file(self, srcTexts, tgtTexts):
        """ Align source and target into one sentence separated by ' ||| ' and save it in local,
            e.g. doch jetzt ist der Held gefallen . ||| but now the hero has fallen .
        :param srcTexts: source texts to be aligned.
        :param tgtTexts: target texts to be aligned.
        """
        parallel_texts = [src.strip() + ' ||| ' + tgt.strip() + '\n' for src, tgt in zip(srcTexts, tgtTexts)]
        with codecs.open(self.af_input_path, 'w') as f:
            f.writelines(parallel_texts)
        print("\tParallel input file saved.")

    def execute_command(self, cmd, type):
        """Execute in command line."""
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
        if p.returncode == 0:
            print("\t{} Alignment Done.".format(type))
        else:
            raise Exception("\t{} Alignment Failed.".format(type))

    def forward_align(self):
        """Get Forward alignment from input file."""
        cmd = self.af_executable_rootpath + "/fast_align -i " + self.af_input_path + " -d -o -v > " + self.af_forward_path
        self.execute_command(cmd, 'Forward')

    def reverse_align(self):
        """Get Reverse alignment from input file."""
        cmd = self.af_executable_rootpath + "/fast_align -i " + self.af_input_path + " -d -o -v -r > " + self.af_reverse_path
        self.execute_command(cmd, 'Reverse')

    def symmetrized_align(self):
        """Get Symmetrized alignment from input file."""
        cmd = self.af_executable_rootpath + "/atools -c grow-diag-final-and -i " + self.af_forward_path + " -j " + \
              self.af_reverse_path + ' > ' + self.af_symmetrized_path
        self.execute_command(cmd, 'Symmetrized')

    def obtain_fast_alignment(self, srcTexts, tgtTexts):
        """A pipeline to get fast alignment: prepare input file, forward alignment, reverse alignment,
           symmetrized alignment."""
        self.prepare_input_file(srcTexts, tgtTexts)
        self.forward_align()
        self.reverse_align()
        self.symmetrized_align()
        print("\n\t Fast Alignemnt Done.")

    def create_text_alignment_dict(self, srcTexts, tgtTexts):
        """Create a dictionary with tuple (source text, target text) as key and symmetrized alignment as values"""

        print("\n\tCreating Forward and Reverse Alignment Dictionaries.")
        with codecs.open(self.af_symmetrized_path, 'r') as f:
            index_alignment = f.readlines()

        src_tgt_forward_alignment = {}
        src_tgt_reverse_alignment = {}
        for src, tgt, alignment in zip(srcTexts, tgtTexts, index_alignment):
            forward_align = defaultdict(list)
            reverse_align = defaultdict(list)
            for pair in alignment.split():
                src_index, tgt_index = list(map(int, pair.split('-')))
                forward_align[src_index].append(tgt_index)
                reverse_align[tgt_index].append(src_index)

            src_tgt_forward_alignment[(src, tgt)] = forward_align
            src_tgt_reverse_alignment[(src, tgt)] = reverse_align

        return src_tgt_forward_alignment, src_tgt_reverse_alignment

    def pipeline(self, best_num=2000):
        """Whole pipeline to extract terminologies, only this function needs to be called after initialization.
           best_num (int): the number of best source terms based on score, from which their target terms will be searched.
                    if best_num==None, select all source terms.
        """
        srcTexts, tgtTexts = self.text_preprocess()
        srcTerms = self.extract_source_terms(srcTexts)
        self.obtain_fast_alignment(srcTexts, tgtTexts)
        src_tgt_forward_alignment, src_tgt_reverse_alignment = self.create_text_alignment_dict(srcTexts, tgtTexts)

        srcTerms = srcTerms.head(best_num)
        final_terminologies = find_terminology_pairs(src_tgt_forward_alignment,
                                                     src_tgt_reverse_alignment,
                                                     srcTerms)
        df = self.postprocess(final_terminologies)
        df.to_excel(self.final_output_path, header=True, index=None)
        print("\nDone.")


def test_speedup():
    file_dir = ['/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.eng',
                '/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.fra']
    with codecs.open(file_dir[0], 'r') as f:
        lines = f.readlines()
    tbe = TbExtractor(file_dir, file_type='2txt', srcLang='eng', tgtLang='fra')
    # tbe.humanize_texts(lines, 'eng')
    print(tbe.tokenize_texts(lines, 'eng')[-5:])

def test_term_extraction():

    file_dir = ['/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.eng',
                '/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.fra']

    with codecs.open(file_dir[0], 'r') as f:
        lines = f.readlines()
    tbe = TbExtractor(file_dir, file_type='2txt', srcLang='eng', tgtLang='fra')
    res = tbe.extract_source_terms(lines)
    print(len(res))

def test_fast_alignment():
    file_dir = ['/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.eng',
                '/linguistics/ethan/Alexa_text_mining_repos/dev_ethan/alexa_text_mining/tb_extractor/test/test.fra']
    tbe = TbExtractor(file_dir, '2txt', 'output_rootpath', 'test_alignment', srcLang='eng', tgtLang='fra')
    srcTexts, tgtTexts = tbe.text_preprocess()
    tbe.obtain_fast_alignment(srcTexts, tgtTexts)

def test_pipeline():
    input_file = ['/linguistics/ethan/Bicleaner/Client_TM/CPA_assurance/cpa_assurance.eng',
                  '/linguistics/ethan/Bicleaner/Client_TM/CPA_assurance/cpa_assurance.fra']
    input_file = '/linguistics/ethan/CLIENT_JOBS/Client_TM/PwC_202102/deep_clean/tm_pwc_internal.20210212_133534.xlsx'
    input_type = 'excel'
    output_rootpath = '/linguistics/ethan/CLIENT_JOBS/Client_TM/PwC_202102/tb_extracted'
    output_prefix = 'tm_pwc_internal.20210212_133453'

    tbe = TbExtractor(input_file, input_type, output_rootpath, output_prefix, srcLang='eng', tgtLang='fra')
    tbe.pipeline(best_num=None)


if __name__ == '__main__':

    # test_humanizer()
    # test_term_extraction()
    # test_fast_alignment()
    test_pipeline()
