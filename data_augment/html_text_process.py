import os, pandas as pd, numpy as np, regex, codecs
import functools, time
from itertools import chain
from ..tb_utils.nlp import SentenceTokenizer, TextHumanizer
from ..tb_utils.language_resources import Codes
from ..tb_utils.mxliff_manager import detect_language
YAPPN_ISO_MAPPING = Codes.mappings("yappn", "iso-639-1")


def timer(func):
    @functools.wraps(func)
    def time_function_runtime(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        end = time.time()
        print("\nTime elapse for function: {} is {} seconds".format(func.__name__, round(end - start, 2)))
        return res

    return time_function_runtime


class HtmlTextProcess(object):

    CHARACTERS_UNICODE_NAME = {'ar': ['ARABIC', 'LATIN'],
                               'bg': ['LATIN', 'CYRILLIC'],
                               'bn': ['DEVANAGARI'],
                               'ca': ['LATIN'],
                               'cs': ['LATIN'],
                               'da': ['LATIN'],
                               'de': ['LATIN'],
                               'el': ['GREEK'],
                               'en': ['LATIN'],
                               'es': ['LATIN'],
                               'fa': ['ARABIC', 'LATIN'],
                               'fi': ['LATIN'],
                               'fr': ['LATIN'],
                               'gu': ['DEVANAGARI'],
                               'he': ['HEBREW'],
                               'hi': ['DEVANAGARI'],
                               'hr': ['LATIN'],
                               'hu': ['LATIN'],
                               'id': ['LATIN'],
                               'it': ['LATIN'],
                               'ja': ['CJK', 'HIRAGANA', 'KATAKANA', 'KATAKANA-HIRAGANA', 'LATIN'],
                               'kn': ['KANNADA'],
                               'ko': ['CJK', 'HANGUL'],
                               'lv': ['LATIN'],
                               'ml': ['ARABIC', 'MALAYALAM'],
                               'mr': ['DEVANAGARI'],
                               'ms': ['LATIN'],
                               'nb': ['LATIN'],
                               'nl': ['LATIN'],
                               'pa': ['ARABIC', 'GURMUKHI'],
                               'pl': ['LATIN'],
                               'pt': ['LATIN'],
                               'ro': ['LATIN'],
                               'ru': ['CYRILLIC'],
                               'sk': ['LATIN'],
                               'sl': ['LATIN'],
                               'sv': ['LATIN'],
                               'ta': ['TAMIL'],
                               'te': ['BRAHMI', 'TELUGU'],
                               'th': ['THAI'],
                               'tr': ['LATIN'],
                               'uk': ['CYRILLIC'],
                               'vi': ['LATIN'],
                               'zh': ['CJK']}

    SENTENTENCE_FINAL_PUNCTUATIONS = {'ar': ('\u061b', '\u06d4', '!', '061f', ')', ']', '}', '"', '”', '»'),
                                      'bg': (';', '.', '!', '?', ')', ']', '}', '"', '“', '»'),
                                      'bn': (';', '|', '!', '?', ')', ']', '}', '"', '”'),
                                      'ca': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'cs': (';', '.', '!', '?', ')', ']', '}', '"', '“'),
                                      'da': (';', '.', '!', '?', ')', ']', '}', '"', '«', '“'),
                                      'de': (';', '.', '!', '?', ')', ']', '}', '"', '“'),
                                      'el': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'en': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'es': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'fa': ('\u061b', '\u06d4', '!', '061f', ')', ']', '}', '"', '”', '»'),
                                      'fi': (';', '|', '!', '?', ')', ']', '}', '"', '”'),
                                      'fr': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'gu': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'he': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'hi': (';', '|', '!', '?', ')', ']', '}', '"', '”'),
                                      'hr': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'hu': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'id': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'it': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'ja': ('；', '。', '！', '？', ')', ']', '}', '"', '」', '﹂'),
                                      'kn': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'ko': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'lv': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'ml': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'mr': (';', '|', '!', '?', ')', ']', '}', '"', '”'),
                                      'ms': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'nb': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'nl': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'pa': (';', '|', '!', '?', ')', ']', '}', '"', '”'),
                                      'pl': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'pt': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'ro': (';', '.', '!', '?', ')', ']', '}', '"', '»'),
                                      'ru': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'sk': (';', '.', '!', '?', ')', ']', '}', '"', '“'),
                                      'sl': (';', '.', '!', '?', ')', ']', '}', '"', '“'),
                                      'sv': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'ta': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'te': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'th': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'tr': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'uk': (';', '.', '!', '?', ')', ']', '}', '"', '»', '”'),
                                      'vi': (';', '.', '!', '?', ')', ']', '}', '"', '”'),
                                      'zh': ('；', '。', '！', '？', '）', ']', '}', '"', '”', '」', '﹂')}

    def __init__(self, lang):

        self.lang = lang
        self.st = SentenceTokenizer(self.lang)
        self.th = TextHumanizer(self.lang)

    def is_sentence_segment(self, texts):
        """Decide if the input text is a sentence segment
           Works only for Latin script

           Args:
              text (str): input text
              language_iso_6391 (str): the ISO6391 code of the language

           Returns:
              (bool): whether the text is a sentence segment or not
        """

        print("Selecting sentences...")
        language_iso_6391 = YAPPN_ISO_MAPPING[self.lang]
        texts = [text for text in texts
                 if any([text[-1] in self.SENTENTENCE_FINAL_PUNCTUATIONS[language_iso_6391],
                                          regex.search(r'(?V1).+[[\w]--[_]]$', text)])]

        return texts

    def humanize(self, texts):

        print("Humanizing sentences...")
        texts = [self.th.humanizeText(text) for text in texts]
        return texts

    def sentence_segmentation(self, texts):

        print("Segmenting sentences...")
        texts = [self.st.tokenize(text) for text in texts]
        texts = list(chain(*texts))
        return texts

    def word_len_check(self, texts, min_len=8, max_len=100):

        print("Select sentences based on word length...")
        texts = [text for text in texts if min_len <= len(text.split()) <= max_len]
        return texts

    def start_text_process(self, file_dir):

        with codecs.open(file_dir, "r") as f:
            texts = f.readlines()
        print("\nBefore postprocessing, number of segments: {}".format(len(texts)))

        texts = self.humanize(texts)
        texts = self.sentence_segmentation(texts)
        texts = self.word_len_check(texts)
        texts = self.is_sentence_segment(texts)

        print("After postprocessing, number of segments: {}".format(len(texts)))
        return texts


def merge_and_deduplicate(input_files, output_file):

    total_lines = []
    for file in input_files:
        with codecs.open(file, 'r') as f:
            lines = f.readlines()
        total_lines += lines

    print("After merging all files, number of lines: {}".format(len(total_lines)))
    total_lines = list(dict.fromkeys(total_lines))
    print("After de-duplicating, number of lines: {}".format(len(total_lines)))

    print("Saving final lines.")
    with codecs.open(output_file, 'w') as f:
        f.writelines(total_lines)


def txt_io(file, action='r', write_lines=None):

    if action == 'r':
        with codecs.open(file, action) as f:
            lines = f.readlines()
        return lines

    elif action == 'w':
        with open(file, action) as f:
            for line in write_lines:
                f.write(line.strip() + '\n')
    else:
        print(f"Action {action} not supported")

@timer
def remove_wrong_lang_text(input_files, output_files, removed_noise_files, noise_lang='en'):

    srcTexts = np.array(txt_io(input_files[0], action='r', write_lines=None))
    tgtTexts = np.array(txt_io(input_files[1], action='r', write_lines=None))

    print("Detecting languages from target texts...")
    tgtText_langs = np.array(detect_language(tgtTexts))

    print("Moving noisy texts of wrong language out of target texts...")
    tgtText_noise_index = np.where(tgtText_langs == noise_lang)
    tgtText_clean_index = np.where(tgtText_langs != noise_lang)

    cleanSrcTexts, cleanTgtTexts = srcTexts[tgtText_clean_index], tgtTexts[tgtText_clean_index]
    noiseSrcTexts, noiseTgtTexts = srcTexts[tgtText_noise_index], tgtTexts[tgtText_noise_index]

    print("Saving results...")
    txt_io(output_files[0], action='w', write_lines=cleanSrcTexts)
    txt_io(output_files[1], action='w', write_lines=cleanTgtTexts)

    txt_io(removed_noise_files[0], action='w', write_lines=noiseSrcTexts)
    txt_io(removed_noise_files[1], action='w', write_lines=noiseTgtTexts)


def test():

    text = "les deux personnes reposaient"
    tp = HtmlTextProcess("fra")
    print(tp.is_sentence_segment(text))

def test2():

    file_dir = '/linguistics/ethan/Canlii_data/historic_html/Tribunal/merge_dedup/tribunal_alltime.merge_dedup.fra'
    output_dir = "/linguistics/ethan/Canlii_data/historic_html/Tribunal/postprocess/tribunal_alltime.merge_dedup.postprocess.fra"
    tp = HtmlTextProcess("fra")
    res = tp.start_text_process(file_dir)

    with open(output_dir, 'w') as f:
        for l in res:
            f.write(l.strip() + "\n")

def test3():
    input_files = ["/linguistics/ethan/Canlii_data/historic_monolingual/Courts/first_batch/courts_alltime_0-620506.eng",
                   "/linguistics/ethan/Canlii_data/historic_monolingual/Courts/second_batch/courts_alltime_620506-end.eng"]
    output_file = "/linguistics/ethan/Canlii_data/historic_monolingual/Courts/courts_alltime.merge_dedup.eng"
    merge_and_deduplicate(input_files, output_file)

def test4():
    input_files = ["/linguistics/ethan/training_data/CPA/test/sample1000.eng",
                   "/linguistics/ethan/training_data/CPA/test/sample1000.fra"]
    output_files = ["/linguistics/ethan/training_data/CPA/test/sample1000.cleaned.eng",
                    "/linguistics/ethan/training_data/CPA/test/sample1000.cleaned.fra"]
    removed_noise_files = ["/linguistics/ethan/training_data/CPA/test/sample1000.removed.eng",
                           "/linguistics/ethan/training_data/CPA/test/sample1000.removed.fra"]

    remove_wrong_lang_text(input_files, output_files, removed_noise_files, noise_lang='en')


if __name__ == "__main__":

    # test()
    # test2()
    # test3()
    test4()
