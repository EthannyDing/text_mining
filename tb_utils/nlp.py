# -*- coding: utf-8 -*-

# utils: nlp
#
# Author: Renxian Zhang
# --------------------------------------------------
# This modules provides basic NLP tools for convenient calling.

import html
import os
import string
import sys
import unicodedata
from pathlib import Path

base_dir = os.path.dirname(Path(__file__).parent.parent)
sys.path.append(base_dir)
sys.path.append(base_dir)

import textdistance
from bs4 import BeautifulSoup
import nltk, jieba, pangu
from janome.tokenizer import Tokenizer as jpn_tokenizer
from konlpy.tag import Kkma
from pyarabic import araby
import regex as re
import ftfy
import langid
from hanziconv import HanziConv
from sacremoses import MosesTokenizer, MosesDetokenizer
import spacy

from .rules import NumberTranslator
from .language_resources import Codes, Writing, CommonRegex

YAPPN_NAME_MAPPINGS = Codes.mappings('yappn', 'name')
YAPPN_ISO6391_MAPPINGS = Codes.mappings('yappn', 'iso-639-1')


class SentenceTokenizer_nltk:
    """Sentence tokenzier wrapper for various languages
    """

    def __init__(self, lang):
        """Intialize a SentenceTokenizer instance.

           Args:
               lang (str): the 3-letter Yappn language code
        """

        self.lang = lang
        if lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                    'pol', 'por', 'spa', 'swe', 'tur'):
            self.sentenceTokenizer = nltk.data.load('tokenizers/punkt/%s.pickle' % YAPPN_NAME_MAPPINGS[lang].lower())
        elif lang in ['jpn', 'ypt', 'zhh', 'zhs', 'zht']:
            self.sentenceTokenizer = nltk.tokenize.RegexpTokenizer(r'[^。？！]+?[。？！]')
        elif lang == 'ara':
            self.sentenceTokenizer = nltk.tokenize.RegexpTokenizer(
                r'[^' + r''.join(['\.', '!', u'؟']) + r']+?[' + r''.join(['\.', '!', u'؟']) + r']')
        else:
            raise NotImplementedError('language %s is not implemented' % lang)

    def tokenize(self, text):
        """Tokenize a text into sentences.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized sentences
        """

        assert isinstance(text, str)

        if self.lang in ('ara', 'ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                         'pol', 'por', 'spa', 'swe', 'tur', 'jpn', 'ypt', 'zhh', 'zhs', 'zht'):
            res = self.sentenceTokenizer.tokenize(text)
        else:
            raise NotImplementedError('language %s is not implemented' % self.lang)

        return res

    def tokenize_with_new_line(self, text):
        """Tokenize a text into sentences by always splitting at line breaks.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized sentences
        """

        assert isinstance(text, str)

        paras = (p for p in text.split('\n') if p)

        res = [sent for para in paras for sent in self.tokenize(para)]

        return res

    def get_gaps(self, text, sentences):
        """Get the gaps (e.g., ' ', '\n\n', '\t') in the text from
           the tokenized sentences

           Args:
              text (str): the untokenized text
              sentences (list): a list of tokenized sentences

           Returns:
              (list/None): a list of strings as gaps that can "join" the sentences into the original text
                           if None, cannot get a list of gaps because the sentences are not based on the text
        """

        gapPatternTemplate = r'(?P<gap_before>\s*)(?P<text>%s)(?P<gap_after>\s*)'
        textIdx = 0

        res = []

        try:
            for (sent_id, sentence) in enumerate(sentences):
                gapPattern = gapPatternTemplate % (re.escape(sentence),)
                gap = re.search(gapPattern, text[textIdx:]).group('gap_before')
                res.append(gap)
                textIdx += len(gap) + len(sentence)
            res.append(text[textIdx:])
        except:
            res = None

        return res

    def tokenize_with_gaps(self, text):
        """Tokenize a text into sentences and output all the gaps between them.

           Args:
               text (str): the input text

           Returns:
              (tuple): (a list of ordered strings as tokenized sentences,
                        a list of ordered strings as gaps in between)
        """

        # sents = self.tokenize(text)
        sents = self.tokenize_with_new_line(text)

        try:
            gaps = self.get_gaps(text, sents)
        except:
            print('get_gaps error ... using all spaces as default')
            gaps = [''] + [' '] * (len(sents) - 1) + ['']

        return (sents, gaps)


class SentenceTokenizer:
    """Sentence tokenzier wrapper for various languages
    """

    def __init__(self, lang):
        """Intialize a SentenceTokenizer instance.

           Args:
               lang (str): the 3-letter Yappn language code
        """

        self.lang = lang
        if lang in ('eng', 'fra', 'spa', 'zhs'):
            self.sentenceTokenizer = spacy.load(YAPPN_ISO6391_MAPPINGS[lang], disable=['parser'])
            self.sentenceTokenizer.add_pipe(self.sentenceTokenizer.create_pipe('sentencizer'))
        else:
            self.sentenceTokenizer = SentenceTokenizer_nltk(lang)

    def tokenize(self, text):
        """Tokenize a text into sentences.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized sentences
        """

        assert isinstance(text, str)

        if self.lang in ('eng', 'fra', 'spa', 'zhs'):
            doc = self.sentenceTokenizer(text)
            res = [s.text.strip() for s in doc.sents if s.text.strip()]
        else:
            res = self.sentenceTokenizer.tokenize(text)

        return res

    def tokenize_with_new_line(self, text):
        """Tokenize a text into sentences by always splitting at line breaks.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized sentences
        """

        assert isinstance(text, str)

        paras = (p for p in text.split('\n') if p)

        res = [sent for para in paras for sent in self.tokenize(para)]

        return res

    def get_gaps(self, text, sentences):
        """Get the gaps (e.g., ' ', '\n\n', '\t') in the text from
           the tokenized sentences

           Args:
              text (str): the untokenized text
              sentences (list): a list of tokenized sentences

           Returns:
              (list/None): a list of strings as gaps that can "join" the sentences into the original text
                           if None, cannot get a list of gaps because the sentences are not based on the text
        """

        gapPatternTemplate = r'(?P<gap_before>\s*)(?P<text>%s)(?P<gap_after>\s*)'
        textIdx = 0

        res = []

        try:
            for (sent_id, sentence) in enumerate(sentences):
                gapPattern = gapPatternTemplate % (re.escape(sentence),)
                gap = re.search(gapPattern, text[textIdx:]).group('gap_before')
                res.append(gap)
                textIdx += len(gap) + len(sentence)
            res.append(text[textIdx:])
        except:
            res = None

        return res

    def tokenize_with_gaps(self, text):
        """Tokenize a text into sentences and output all the gaps between them.

           Args:
               text (str): the input text

           Returns:
              (tuple): (a list of ordered strings as tokenized sentences,
                        a list of ordered strings as gaps in between)
        """

        sents = self.tokenize_with_new_line(text)

        try:
            gaps = self.get_gaps(text, sents)
        except:
            print('get_gaps error ... using all spaces as default')
            gaps = [''] + [' '] * (len(sents) - 1) + ['']

        return (sents, gaps)


class SubsentenceTokenizer:
    """Subsentence tokenzier for various languages
       Subsentences are fragments below the sentence level, typically ending with ;
    """

    def __init__(self, lang):
        """Intialize a SubsentenceTokenizer instance.

           Args:
               lang (str): the 3-letter Yappn language code
        """

        self.lang = lang

        continuousSymbolPattern = r'[' + re.escape(string.punctuation) + r']{4,}'

        self.symbolTokenizer = nltk.tokenize.RegexpTokenizer(continuousSymbolPattern)

        if lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                    'pol', 'por', 'spa', 'swe', 'tur'):
            self.sentenceTokenizer = nltk.tokenize.RegexpTokenizer(';', gaps=True)
        elif lang in ['jpn', 'ypt', 'zhh', 'zhs', 'zht']:
            self.sentenceTokenizer = nltk.tokenize.RegexpTokenizer('；', gaps=True)
        elif lang == 'ara':
            self.sentenceTokenizer = nltk.tokenize.RegexpTokenizer(u'؛', gaps=True)
        else:
            raise NotImplementedError('language %s is not implemented' % lang)

    def tokenize_symbol(self, text):
        """Tokenize a text by separating continuous symbol strings from the surrounding texts

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized subsentences
        """

        splitIdxs = list(self.symbolTokenizer.span_tokenize(text))

        res = []
        start = 0

        for (i1, i2) in splitIdxs:
            res.append(text[start:i1].strip())
            res.append(text[i1:i2].strip())
            start = i2

        res.append(text[start:].strip())

        res = [seg for seg in res if seg]

        return res

    def tokenize_semicolon(self, text):
        """Tokenize a text into subsentences using semicolon

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized subsentences
        """

        assert isinstance(text, str)

        if self.lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                         'pol', 'por', 'spa', 'swe', 'tur'):
            text = re.sub(r';{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
            if text[0] == ';':
                text = ' ' + text
            if text[-1] == ';':
                text += ' '
            split = self.sentenceTokenizer.tokenize(text)
            res = [t.strip() + ';' for t in split[:-1]] + [split[-1].strip()]
        elif self.lang in ['jpn', 'ypt', 'zhh', 'zhs', 'zht']:
            text = re.sub(r'；{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
            if text[0] == '；':
                text = ' ' + text
            if text[-1] == '；':
                text += ' '
            split = self.sentenceTokenizer.tokenize(text)
            res = [t.strip() + '；' for t in split[:-1]] + [split[-1].strip()]
        elif self.lang == 'ara':
            text = re.sub(u'؛' + r'{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
            if text[0] == u'؛':
                text = ' ' + text
            if text[-1] == u'؛':
                text += ' '
            split = self.sentenceTokenizer.tokenize(text)
            res = [t.strip() + u'؛' for t in split[:-1]] + [split[-1].strip()]
        else:
            raise NotImplementedError('language %s is not implemented' % self.lang)

        res = [t for t in res if t]

        return res

    def tokenize(self, text):
        """Tokenize a text into subsentences.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized subsentences
        """

        assert isinstance(text, str)

        res = self.tokenize_symbol(text)
        res = [seg_ for seg in res for seg_ in self.tokenize_semicolon(seg)]

        return res

    # def tokenize(self, text):
    # """Tokenize a text into subsentences.

    # Args:
    # text (str): the input text

    # Returns:
    # (list): a list of strings as tokenized subsentences
    # """

    # assert isinstance(text, str)

    # if self.lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
    # 'pol', 'por', 'spa', 'swe', 'tur'):
    # text = re.sub(r';{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
    # if text[0] == ';':
    # text = ' ' + text
    # if text[-1] == ';':
    # text += ' '
    # split = self.sentenceTokenizer.tokenize(text)
    # res = [t.strip() + ';' for t in split[:-1]] + [split[-1].strip()]
    # elif self.lang in ['jpn', 'ypt', 'zhh', 'zhs', 'zht']:
    # text = re.sub(r'；{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
    # if text[0] == '；':
    # text = ' ' + text
    # if text[-1] == '；':
    # text += ' '
    # split = self.sentenceTokenizer.tokenize(text)
    # res = [t.strip() + '；' for t in split[:-1]] + [split[-1].strip()]
    # elif self.lang == 'ara':
    # text = re.sub(u'؛' + r'{2,}', lambda m: ' '.join([c for c in m.group(0)]), text)
    # if text[0] == u'؛':
    # text = ' ' + text
    # if text[-1] == u'؛':
    # text += ' '
    # split = self.sentenceTokenizer.tokenize(text)
    # res = [t.strip() + u'؛' for t in split[:-1]] + [split[-1].strip()]
    # else:
    # raise NotImplementedError('language %s is not implemented' % self.lang)

    # res = [t for t in res if t]

    # return res


class WordTokenizer:
    """Word tokenzier wrapper for various languages
    """

    def __init__(self, lang, defaultTokenizer='moses'):
        """Intialize a WordTokenizer instance.

           Args:
               lang (str): the 3-letter Yappn language code
               defaultTokenizer (str): the name of the default tokenizer
                                       e.g., 'moses', 'nltk', 'whitespace'
        """

        self.lang = lang
        self._default = defaultTokenizer

        if lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                    'pol', 'por', 'spa', 'swe', 'tur'):
            if defaultTokenizer == 'moses':
                self.wordTokenizer = MosesTokenizer(lang=YAPPN_ISO6391_MAPPINGS[lang])
            elif defaultTokenizer == 'nltk':
                self.wordTokenizer = nltk.word_tokenize
            else:
                self.wordTokenizer = None
        elif lang == 'jpn':
            self.wordTokenizer = jpn_tokenizer()
        elif lang in ('ypt', 'zhh', 'zhs', 'zht'):
            self.wordTokenizer = jieba
        elif lang == 'kor':
            self.wordTokenizer = Kkma()
        elif lang == 'ara':
            self.wordTokenizer = araby
        else:
            raise NotImplementedError('language %s is not implemented' % lang)

    def tokenize(self, text, escape=False):
        """Tokenize a text into words.

           Args:
               text (str): the input text

           Returns:
              (list): a list of strings as tokenized words
        """

        assert isinstance(text, str)

        if self.lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                         'pol', 'por', 'spa', 'swe', 'tur'):
            if self._default == 'moses':
                res = self.wordTokenizer.tokenize(text, escape=escape)
            elif self._default == 'nltk':
                res = self.wordTokenizer(text, language=YAPPN_NAME_MAPPINGS[self.lang].lower())
            else:
                res = text.split()
        elif self.lang == 'ara':
            res = self.wordTokenizer.tokenize(text)
            res = [t for t in res if t.strip()]
        elif self.lang == 'jpn':
            res = self.wordTokenizer.tokenize(text, wakati=True)
            res = [t for t in res if t.strip()]
        elif self.lang in ('ypt', 'zhh', 'zhs', 'zht'):
            res = self.wordTokenizer.lcut(text)
            res = [t for t in res if t.strip()]
        elif self.lang == 'kor':
            res = self.wordTokenizer.morphs(text)
            res = [t for t in res if t.strip()]
        else:
            raise NotImplementedError('language %s is not implemented' % self.lang)

        return res


class WordDetokenizer:
    """Word detokenzier wrapper for various languages
    """

    def __init__(self, lang, defaultDetokenizer='moses'):
        """Intialize a WordDetokenizer instance.

           Args:
               lang (str): the 3-letter Yappn language code
               defaultDetokenizer (str): the name of the default detokenizer
        """

        self.lang = lang
        self._default = defaultDetokenizer

        if self.lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                         'pol', 'por', 'spa', 'swe', 'tur'):
            if defaultDetokenizer == 'moses':
                self.wordDetokenizer = MosesDetokenizer(lang=YAPPN_ISO6391_MAPPINGS[lang])
            else:
                raise NotImplementedError('Detokenizer %s is not implemented' % defaultDetokenizer)
        elif self.lang in ('ara', 'jpn', 'ypt', 'zhh', 'zhs', 'zht'):
            self.wordDetokenizer = TextHumanizer(self.lang)
        else:
            raise NotImplementedError('Language %s is not implemented' % self.lang)

    def detokenize(self, tokens):
        """Detokenize a list of tokens back to text.

           Args:
               tokens (list): a list of tokens

           Returns:
              (str): output text
        """

        assert isinstance(tokens, list)

        if self.lang in ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                         'pol', 'por', 'spa', 'swe', 'tur'):
            if self._default == 'moses':
                res = self.wordDetokenizer.detokenize(tokens)
            else:
                raise NotImplementedError('Detokenizer %s is not implemented' % self._default)
        elif self.lang in ('ypt', 'zhh', 'zhs', 'zht'):
            res = self.wordDetokenizer.humanizeText(''.join(tokens))
        elif self.lang in ('ara', 'jpn'):
            res = self.wordDetokenizer.humanizeText(' '.join(tokens))
        else:
            raise NotImplementedError('language %s is not implemented' % self.lang)

        return res


class LanguageDetector:
    """It detects the language of an input string
       and legitimacy of the text
    """

    def __init__(self, langCodeFormat='iso-639-1', languages=None):
        """Initialize a LanguageDetector instance

           Args:
              langCodeFormat (str): the format of the language code
                                    'name', 'yappn', 'google', 'microsoft', or 'iso-639-1' (default)
              languages (list or None): a list of possible languages (3-letter Yappn language codes) to detect
                                        if not None, the detector will return a result in the given list only
        """

        assert langCodeFormat in ['name', 'yappn', 'google', 'microsoft', 'iso-639-1']

        try:
            self._langs = [YAPPN_ISO6391_MAPPINGS[lang] for lang in languages]
        except:
            self._langs = None
        langid.set_languages(self._langs)

        self._langCode = langCodeFormat
        self._cp = ChineseProcessor('zhs')

    def getUnicodeScriptName(self, char):
        """Get the unicode script name of the input character

           Args:
              char (str): input character

           Returns:
              (str): the unicode script name
        """

        assert isinstance(char, str) and len(char) == 1

        try:
            res = unicodedata.name(char).split()[0]
        except:
            res = ''

        return res

    def hasTextChars(self, text, lang, minLenContinuousChars=2):
        """Decide if there are text characters in the text of a language
           with a given minimum number threshold of continuous text characters

           Args:
              text (str): input text
              lang (str): 3-letter Yappn language code
              minLenContinuousChars (int): the minimum number of continuous characters used for the decision

           Returns:
              (bool): whether there are text characters in the text
        """

        if minLenContinuousChars <= 0:
            res = True
        else:
            res = False

            for langScript in Writing.CHARACTERS_UNICODE_NAME[lang]:
                try:
                    found = re.findall(r'(?u)\p{' + langScript + r'}+', text)
                    if found:
                        if max(map(lambda x: len(x), found)) >= minLenContinuousChars:
                            res = True
                            break
                except:
                    continue

        return res

    def isCanonicalText(self, text):
        """Decide if the input text is canonical text (e.g. not filename, url, etc.)

           Args:
              text (str): input text

           Returns:
              (bool): whether the input text is canonical text
        """

        res = True

        for pattern in (CommonRegex.FILENAME_PATTERN, CommonRegex.URL_PATTERN,
                        CommonRegex.SOCIAL_PATTERN, CommonRegex.SCRIPT_PATTERN):
            if re.search(pattern, text):
                res = False
                break

        return res

    def detect(self, text):
        """Detect the language of the input text

           Args:
              text (str): input

           Returns:
              (str): the language (code) according to the code format
        """

        assert isinstance(text, str)

        res = langid.classify(text)[0]

        if res == 'zh':
            if self._cp.isSimplified(text):
                res = 'zhs'
            else:
                res = 'zht'
            res = Codes.mappings('yappn', self._langCode)[res] if self._langCode != 'yappn' else res

        else:
            res = Codes.mappings('iso-639-1', self._langCode)[res] if self._langCode != 'iso-639-1' else res

        return res

    def getTopN(self, text, n):
        """Get the top N detected languages of the input text

           Args:
              text (str): input
              n (int): number of top detected languages

           Returns:
              (list): a list of ranked languages (codes) according to the code format
        """

        assert isinstance(text, str) and isinstance(n, int)

        ranked = [lang for (lang, _) in langid.rank(text)]

        num = min(n, len(ranked))

        if self._langCode == 'iso-639-1':
            res = ranked[:num]
        else:
            res = [Codes.mappings('iso-639-1', self._langCode)[lc] for lc in ranked[:num]
                   if lc in Codes.mappings('iso-639-1', self._langCode)]

        return res


class TextHumanizer:
    """It cleans/standardizes/rectifies text for human reading
    """

    def __init__(self, lang):
        """Initialize a TextHumanizer instance

           Args:
              lang (str): the 3-letter Yappn language code
        """

        self.lang = lang
        self._number_converter = {'eng_fra': NumberTranslator('English', 'French',
                                                              None, None),
                                  'fra_eng': NumberTranslator('French', 'English',
                                                              None, None)
                                  }

    def cleanHtml(self, text):
        """Clean HTML characters in the input text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text without html characters
        """

        assert isinstance(text, str)

        res = html.unescape(BeautifulSoup(text, 'lxml').text)

        # Delete illegitimate &...; characters

        p = r'(?<=\s|^)(&\w+;)(?=\s|$)'
        try:
            res = re.sub(p, lambda m: '', res)
        except:
            pass

        return res

    def standardizePercentages(self, text):
        """Standardize the format of percentages by removing unnecessary spaces.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized percentages
        """

        p = r'(?<=\s|^)(?P<number>\d+(\.\d+)?)\s+(?P<percent>[%٪％])(?=\W|$)'
        try:
            res = re.sub(p, lambda m: m.group('number') + m.group('percent'), text)
        except:
            res = text

        return res

    def standardizePercentages_English(self, text):
        """Standardize the format of percentages in English by removing unnecessary spaces.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized percentages
        """

        p = r'(?<=\s|^)(?P<number>\d+(\.\d+)?)\s*(?P<percent>[%٪％])(?=\W|$)'
        try:
            res = re.sub(p, lambda m: m.group('number') + '%', text)
        except:
            res = text

        return res

    def standardizePercentages_French(self, text):
        """Standardize the format of percentages in French by removing unnecessary spaces.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized percentages
        """

        p = r'(?<=\s|^)(?P<number>\d+(,\d+)?)\s*(?P<percent>[%٪％])(?=\W|$)'
        try:
            res = re.sub(p, lambda m: m.group('number') + '\xa0%', text)
        except:
            res = text

        return res

    def standardizeNumbers_French_old(self, text):
        """Standardize the format of number in French

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized number
        """

        p = r'(?:^|\s)(?P<number>\d{3,})(?:$|\s)'
        for item in re.findall(p, text):
            text = text.replace(item, self._number_converter['eng_fra'].convert(item), 1)

        return text

    def standardizeNumbers_French(self, fra_text, eng_text):
        """Standardize the format of number in French

           Args:
              fra_text (str): the text to be processed
              eng_text (str): the English text as reference
           Returns:
              (str): text with standardized number
        """

        p_fra = r'(?:^|\s)(?P<number>\d{3,})(?:$|\s)'
        p_eng = r'(?:^|\D)(?P<number>[\d]+(?:[,\s]\d{3})*)(?:$|\D)'

        if eng_text:
            numbers_eng = re.findall(p_eng, eng_text, overlapped=True)
            for item in re.findall(p_fra, fra_text):
                if self._number_converter['fra_eng'].convert(item) in numbers_eng:
                    fra_text = fra_text.replace(item, self._number_converter['eng_fra'].convert(item), 1)
        else:
            for item in re.findall(p_fra, fra_text):
                fra_text = fra_text.replace(item, self._number_converter['eng_fra'].convert(item), 1)

        return fra_text

    def standardizeDollarsignSpaces(self, text):
        """Standardize the spaces around dollar sign.

           Args:
              text (str): the text to be processed
           Returns:
              (str): standardized text
        """

        p = r'(?<=[^\W_]|^)(?P<dollarsign>\s*\$(\d+)?\s*)(?=\S|$)'
        try:
            res = re.sub(p, lambda m: ' ' + m.group('dollarsign').strip() + ' ', text)
        except:
            res = text

        return res

    def standardizeWordSpaces_Latin(self, text):
        """Standardize the spaces between words for texts of the Latin script.
           This is a general-purpose method for Latin texts including English, French, etc.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words
        """

        assert isinstance(text, str)

        # res = ' '.join(text.split()).strip()
        res = ' '.join(re.split(r'(?V1)[\s--[\xa0]]+', text)).strip()

        return res

    def standardizeCapitalization_English(self, text):
        """Standardize the capitalization of common English proper nouns.
           This is only a temporary solution, which should be deprecated by better AI

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized word capitalizations
        """

        assert isinstance(text, str)

        CAPITALIZATION_MAPPINGS = {'january': 'January',
                                   'february': 'February',
                                   'april': 'April',
                                   'june': 'June',
                                   'july': 'July',
                                   'august': 'August',
                                   'september': 'September',
                                   'october': 'October',
                                   'november': 'November',
                                   'december': 'December',
                                   'monday': 'Monday',
                                   'tuesday': 'Tuesday',
                                   'wednesday': 'Wednesday',
                                   'thursday': 'Thursday',
                                   'friday': 'Friday',
                                   'saturday': 'Saturday',
                                   'sunday': 'Sunday'}

        res = text

        for term in CAPITALIZATION_MAPPINGS:
            res = re.sub(r'\b' + term + r'\b', CAPITALIZATION_MAPPINGS[term], res)

        return res

    def standardizeWordSpaces_Chinese(self, text, addSpaceBetweenChineseAndHalfwidth=True):
        """Standardize the spaces between words for Chinese

           Args:
              text (str): the text to be processed
              addSpaceBetweenChineseAndHalfwidth (bool): whether to add space between a Chinese character and a half-width character
           Returns:
              (str): text with standardized spaces between words
        """

        assert isinstance(text, str)

        cp = ChineseProcessor(self.lang)

        segs = text.split()

        if segs:
            res = segs[0]
            for seg in segs[1:]:
                if cp.isChineseCharacter(res[-1], punctuation=False) and cp.isChineseCharacter(seg[0],
                                                                                               punctuation=False):
                    res += seg
                else:
                    res += ' ' + seg
        else:
            res = ''

        if addSpaceBetweenChineseAndHalfwidth:
            res = pangu.spacing_text(res).strip()
        else:
            res = res.strip()

        return res

    def standardizeWordPunctuationSpaces_Latin(self, text):
        """Standardize the word-punctuation spaces for texts of the Latin script.
           This is a general-purpose method for Latin texts including English, etc.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and punctuations
        """

        assert isinstance(text, str)

        res = text

        # Text-beginning: ,xxx ...

        # p = r'^(\s*[,;:…!\?\.]\s*)(?!\d)(?=\w)'
        p = r'(?V1)^(\s*[,;:…!\?\.]\s*)(?=[\w--\d])'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + ' ', res)
        except:
            pass

        # Mid-text: ... xxx, yyy ...

        # p = r'(?<=\w)(\s*[,;:…!\?\.]\s*)(?!\d)(?=\w)'
        p = r'(?V1)(?<=\S)(\s*[,;:…!\?\.]\s*)(?=[\w--\d])'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + ' ', res)
        except:
            pass

        # Text-ending: ... xxx.

        # p = r'(?<=\w)(\s*[,;:…!\?\.]\s*)(?=\Z)'
        p = r'(?<=\S)(\s*[,;:…!\?\.]\s*)(?=\Z)'

        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass

        return res

    def standardizeWordPunctuationSpaces_French(self, text):
        """Standardize the word-punctuation spaces for French.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and punctuations
        """

        assert isinstance(text, str)

        res = text

        # Text-beginning: ,xxx ...

        p = r'(?V1)^(\s*[,;:…!\?\.]\s*)(?=[\w--\d])'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + ' ', res)
        except:
            pass

        # Mid-text: ... xxx, yyy ...

        p = r'(?V1)(?<=\S)(\s*[,;…!\?\.]\s*)(?=[\w--\d])'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + ' ', res)
        except:
            pass
        p = r'(?V1)(?<=\S)(\s*[:]\s*)(?=[\w--\d])'
        try:
            res = re.sub(p, lambda m: '\xa0' + m.group(1).strip() + ' ', res)
        except:
            pass

        # Text-ending: ... xxx.

        p = r'(?<=\S)(\s*[,;…!\?\.]\s*)(?=\Z)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass
        p = r'(?<=\S)(\s*[:]\s*)(?=\Z)'
        try:
            res = re.sub(p, lambda m: '\xa0' + m.group(1).strip(), res)
        except:
            pass

        return res

    def standardizeWordPunctuationSpaces_Arabic(self, text):
        """Standardize the word-punctuation spaces for texts of the Arabic script.
           This is a general-purpose method for Arabic text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and punctuations
        """

        assert isinstance(text, str)

        res = text

        # Mid-text: ... xxx, yyy ...

        p = r'(?<=\w)(\s*[\.،؟؛:!…]\s*)(?!\d)(?=\w)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + ' ', res)
        except:
            pass

        # Text-ending: ... xxx.

        p = r'(?<=\w)(\s*[\.،؟؛:!…]\s*)(?=\Z)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass

        return res

    def standardizeWordPunctuationSpaces_Chinese(self, text):
        """Standardize the word-punctuation spaces for Chinese

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and punctuations
        """

        assert isinstance(text, str)

        cp = ChineseProcessor(self.lang)

        segs = text.split()

        if segs:
            res = segs[0]
            for seg in segs[1:]:
                if (cp.isChinesePunctuation(res[-1]) and cp.isChineseCharacter(seg[0])) or (
                        cp.isChineseCharacter(res[-1]) and cp.isChinesePunctuation(seg[0])):
                    res += seg
                else:
                    res += ' ' + seg
        else:
            res = ''

        res = res.strip()

        return res

    def standardizeWordPunctuationSpaces_Japanese(self, text):
        """Standardize the word-punctuation spaces for Japanese

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and punctuations
        """

        assert isinstance(text, str)

        jp = JapaneseProcessor(self.lang)

        segs = text.split()

        if segs:
            res = segs[0]
            for seg in segs[1:]:
                if (jp.isJapanesePunctuation(res[-1]) and jp.isJapaneseCharacter(seg[0])) or (
                        jp.isJapaneseCharacter(res[-1]) and jp.isJapanesePunctuation(seg[0])):
                    res += seg
                else:
                    res += ' ' + seg
        else:
            res = ''

        res = res.strip()

        return res

    def standardizeWordQuoteSpaces_Latin(self, text):
        """Standardize the word-quote spaces for texts of the Latin script.
           This is a general-purpose method for Latin texts including English, French, etc.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and quotes
        """

        assert isinstance(text, str)

        res = text

        # Symmetrical quotes: " ... "

        p = r'"(\s*[^"]+\s*)"'
        try:
            res = re.sub(p, lambda m: '"' + m.group(1).strip() + '"', res)
        except:
            pass

        # Non-symmetrical quoations: “ ... ”

        p = r'“(\s*[^“”]+\s*)”'
        try:
            res = re.sub(p, lambda m: '“' + m.group(1).strip() + '”', res)
        except:
            pass

        return res

    def standardizeWordQuoteSpaces_French(self, text):
        """Standardize the word-quote spaces for French

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and quotes
        """

        assert isinstance(text, str)

        res = text

        p = r'«(\s*[^«»]+\s*)»'
        try:
            res = re.sub(p, lambda m: '«\xa0' + m.group(1).strip() + '\xa0»', res)
        except:
            pass

        return res

    def standardizeWordQuoteSpaces_Chinese(self, text):
        """Standardize the word-quote spaces for Chinese text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and quotes
        """

        assert isinstance(text, str)

        res = text

        p = r'“(\s*[^“”]+\s*)”'
        try:
            res = re.sub(p, lambda m: '“' + m.group(1).strip() + '”', res)
        except:
            pass

        return res

    def standardizeWordQuoteSpaces_Japanese(self, text):
        """Standardize the word-quote spaces for Japanese text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and quotes
        """

        assert isinstance(text, str)

        res = text

        p = r'「(\s*[^「」]+\s*)」'
        try:
            res = re.sub(p, lambda m: '「' + m.group(1).strip() + '」', res)
        except:
            pass

        p = r'『(\s*[^『』]+\s*)』'
        try:
            res = re.sub(p, lambda m: '『' + m.group(1).strip() + '』', res)
        except:
            pass

        return res

    def standardizeWordBracketSpaces_Latin(self, text):
        """Standardize the word-bracket spaces for texts of the Latin script.
           This is a general-purpose method for Latin texts including English, French, etc.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and brackets
        """

        assert isinstance(text, str)

        res = text

        p = r'\((\s*[^\(\)]+\s*)\)'
        try:
            res = re.sub(p, lambda m: '(' + m.group(1).strip() + ')', res)
        except:
            pass

        return res

    def standardizeWordBracketSpaces_Chinese(self, text):
        """Standardize the word-bracket spaces for Chinese text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and brackets
        """

        assert isinstance(text, str)

        res = text

        for leftBracket, rightBracket in (('（', '）'), ('〈', '〉'), ('《', '》'), ('【', '】')):
            p = leftBracket + r'(\s*[^' + leftBracket + rightBracket + r']+\s*)' + rightBracket
            try:
                res = re.sub(p, lambda m: leftBracket + m.group(1).strip() + rightBracket, res)
            except:
                pass

        return res

    def standardizeWordBracketSpaces_Japanese(self, text):
        """Standardize the word-bracket spaces for Japanese text

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized spaces between words and brackets
        """

        assert isinstance(text, str)

        res = text

        for leftBracket, rightBracket in (('（', '）'), ('<', '>'), ('\[', '\]'), ('【', '】')):
            p = leftBracket + r'(\s*[^' + leftBracket + rightBracket + r']+\s*)' + rightBracket
            try:
                res = re.sub(p, lambda m: leftBracket + m.group(1).strip() + rightBracket, res)
            except:
                pass

        return res

    def standardizeContractionSpaces_English(self, text):
        """Standardize the contraction spaces for texts of English.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized contraction spaces
        """

        assert isinstance(text, str)

        res = text

        # Two parts: I've, he'd, ...

        p = r'(?<=[a-zA-Z]+)(\s*[’\']\s*)(t|m|ll|ve|s|re|d)(?=\W)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip() + m.group(2), res)
        except:
            pass

        # One part: students' room

        p = r'(?<=[a-zA-Z]+s)(\s*[’\'])(?=\W)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass

        return res

    def standardizeContractionSpaces_French(self, text):
        """Standardize the contraction spaces for texts of French.

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized contraction spaces
        """

        assert isinstance(text, str)

        res = text

        p = r'(?<=\w)(\s*[\'’]\s*)(?=\w)'
        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass

        return res

    def convertQuotes_English(self, text, convertSingleQuote=True):
        """Convert quotes from « or » to ".

           Args:
              text (str): the text to be processed
              convertSingleQuote (bool): whether to convert in a single mode
                                         i.e., a single « or » to "
           Returns:
              (str): text with converted quotes
        """

        assert isinstance(text, str)

        res = text

        # Convert « or »

        if convertSingleQuote:
            res = re.sub('«', '"', res)
            res = re.sub('»', '"', res)
        else:
            p = r'«([^«»]+)»'
            try:
                res = re.sub(p, lambda m: '"' + m.group(1) + '"', res)
            except:
                pass

        return res

    def convertQuotes_French(self, text, convertSingleQuote=True):
        """Convert quotes from " " or “ ” to « ».

           Args:
              text (str): the text to be processed
              convertSingleQuote (bool): whether to convert in a single mode
                                         i.e., “ to «,  ” to »
           Returns:
              (str): text with converted quotes
        """

        assert isinstance(text, str)

        res = text

        # Symmetrical quotes: " ... "

        # p = r'"([^"]+)"'
        # try:
        # res = re.sub(p, lambda m: '«' + m.group(1) + '»', res)
        # except:
        # pass
        p = r'[“"]([^“”"]+)["”]'
        try:
            res = re.sub(p, lambda m: '«' + m.group(1) + '»', res)
        except:
            pass

        if convertSingleQuote:
            res = re.sub('“', '«', res)
            res = re.sub('”', '»', res)
            # The following handling of " is ugly; to be improved
            if res.count('"') == 1:
                if re.search(r'(^|\s)"(\S)', res):
                    res = re.sub('"', '«\xa0', res)
                elif re.search(r'(\S)"($|\s)', res):
                    res = re.sub('"', '\xa0»', res)
        # else:
        # Non-symmetrical quoations: “ ... ”

        # p = r'“([^“”]+)”'
        # p = r'[“"]([^“”"]+)["”]'
        # try:
        # res = re.sub(p, lambda m: '«' + m.group(1) + '»', res)
        # except:
        # pass

        res = self.standardizeWordQuoteSpaces_French(res)

        return res

    def convertApostrophe_French(self, text):
        """Convert apostrophe from ' to ’ ('\u2019').

           Args:
              text (str): the text to be processed

           Returns:
              (str): text with converted apostrophe
        """

        p = r"(?i)\b(c|j|n|m|t|s|l|d|qu|jusqu|lorsqu|puisqu|quoiqu)(')(\p{L})"

        res = re.sub(p, lambda m: m.group(1) + "’" + m.group(3), text)

        return res

    def standardizeAlphabet_French(self, text):
        """Standardize the French alphabet, e.g., changing ´e to é

           Args:
              text (str): the text to be processed
           Returns:
              (str): text with standardized French alphabet
        """

        assert isinstance(text, str)

        res = text

        accent_mappings = {'\u0301': '\u00b4',
                           '\u0300': '\u0060',
                           '\u0302': '\u02c6',
                           '\u0308': '\u00a8',
                           '\u0327': '\u00b8'
                           }

        for key in accent_mappings:
            res = re.sub(key, accent_mappings[key], res)

        p = r"(?i)(?<=\w)(?<!des)(?<!n\'a)(\s+[´]\s+)(?=[eE])"
        try:
            res = re.sub(p, lambda m: m.group(1).strip(), res)
        except:
            pass

        p = r'(?i)(?<![^\W_]des)(\s+[´]\s+)(?=[eE])'
        try:
            res = re.sub(p, lambda m: m.group(1).rstrip(), res)
        except:
            pass

        p = r'([eE])(\s+[´]\s+)(?![eE])'
        try:
            res = re.sub(p, lambda m: m.group(2).strip() + m.group(1), res)
        except:
            pass

        p = r'([eE])(\s*[`]\s*)(?![eE])'
        try:
            res = re.sub(p, lambda m: m.group(2).strip() + m.group(1), res)
        except:
            pass

        acute_mappings = (('´E', 'É'), ('´e', 'é'))
        grave_mappings = (('`A', 'À'), ('`a', 'à'), ('`E', 'È'), ('`e', 'è'), ('`U', 'Ù'), ('`u', 'ù'))
        circumflex_mappings = (('ˆA', 'Â'), ('ˆa', 'â'), ('ˆE', 'Ê'), ('ˆe', 'ê'),
                               ('ˆI', 'Î'), ('ˆi', 'î'), ('ˆO', 'Ô'), ('ˆo', 'ô'), ('ˆU', 'Û'), ('ˆu', 'û'))
        diaeresis_mappings = (('¨E', 'Ë'), ('¨e', 'ë'), ('¨I', 'Ï'), ('¨i', 'ï'),
                              ('¨U', 'Ü'), ('¨u', 'ü'), ('¨Y', 'Ÿ'), ('¨y', 'ÿ'))
        cedilla_mappings = (('¸C', 'Ç'), ('¸c', 'ç'))

        alphabet_mappings = dict(acute_mappings + grave_mappings + circumflex_mappings +
                                 diaeresis_mappings + cedilla_mappings)

        for key in alphabet_mappings:
            res = re.sub(key, alphabet_mappings[key], res)

        return res

    def humanizeText(self, text,
                     source_text=None,
                     cleanHtml=True,
                     standardizePercentages=True,
                     standardizeNumbers=True,
                     standardizeDollarsignSpaces=True,
                     standardizeAlphabet=True,
                     standardizeCapitalization=True,
                     standardizeWordSpaces=True,
                     standardizeWordPunctuationSpaces=True,
                     uncurlQuotes=False,
                     addSpaceBetweenFullwidthAndHalfwidth=True,
                     standardizeWordQuoteSpaces=True,
                     standardizeWordBracketSpaces=True,
                     standardizeContractionSpaces=True,
                     standardizeApostrophe=True
                     ):
        """Humanize text for the specified language

           Args:
              text (str): the text to be processed
              source_text (str): the source text for reference
              cleanHtml (bool): whether to clean HTML content
              standardizeNumbers (bool): whether to standardize numbers
              standardizePercentages (bool): whether to standardize the percentages
              standardizeDollarsignSpaces (bool): whether to standardize the dollar sign spaces
              standardizeAlphabet (bool): whether to standardize the alphabet
              standardizeCapitalization (bool): whether to standardize the capitalization
              standardizeWordSpaces (bool): whether to standardize spaces between words
              standardizeWordPunctuationSpaces (bool): whether to standardize spaces between words and punctuations
              uncurlQuotes (bool): whether to convert “ ”, « », etc. to " "
              addSpaceBetweenChineseAndHalfwidth (bool): whether to add space between a full-width character and a half-width character
              standardizeWordQuoteSpaces (bool): whether to standardize spaces between words and quotes
              standardizeWordBracketSpaces (bool): whether to standardize spaces between words and brackets
              standardizeContractionSpaces (bool): whether to standardize spaces around contractions
              standardizeApostrophe (bool): whether to standardize apostrophe
           Returns:
              (str): humanized text
        """

        assert isinstance(text, str)
        try:
            if cleanHtml:
                text = self.cleanHtml(text)

            # if standardizePercentages:
            # text = self.standardizePercentages(text)

            if standardizeDollarsignSpaces:
                text = self.standardizeDollarsignSpaces(text)

            # Per-language humanization

            if self.lang == 'ara':
                res = ftfy.fix_text(text, uncurl_quotes=uncurlQuotes)

                if standardizePercentages:
                    res = self.standardizePercentages(res)
                if standardizeWordBracketSpaces:
                    res = self.standardizeWordBracketSpaces_Latin(res)
                if standardizeWordQuoteSpaces:
                    res = self.standardizeWordQuoteSpaces_Latin(res)
                if standardizeWordPunctuationSpaces:
                    res = self.standardizeWordPunctuationSpaces_Arabic(res)
                if standardizeWordSpaces:
                    res = self.standardizeWordSpaces_Latin(res)

            elif self.lang == 'eng':
                res = ftfy.fix_text(text, uncurl_quotes=uncurlQuotes)

                if standardizeCapitalization:
                    res = self.standardizeCapitalization_English(res)
                if standardizeContractionSpaces:
                    res = self.standardizeContractionSpaces_English(res)
                if standardizeWordBracketSpaces:
                    res = self.standardizeWordBracketSpaces_Latin(res)
                if standardizeWordPunctuationSpaces:
                    res = self.standardizeWordPunctuationSpaces_Latin(res)
                if standardizeWordSpaces:
                    res = self.standardizeWordSpaces_Latin(res)
                if standardizeWordQuoteSpaces:
                    if not uncurlQuotes:
                        res = self.convertQuotes_English(res)
                    res = self.standardizeWordQuoteSpaces_Latin(res)
                if standardizePercentages:
                    res = self.standardizePercentages_English(res)

            elif self.lang == 'fra':
                res = ftfy.fix_text(text, uncurl_quotes=uncurlQuotes)

                if standardizeAlphabet:
                    res = self.standardizeAlphabet_French(res)
                if standardizeContractionSpaces:
                    res = self.standardizeContractionSpaces_French(res)
                if standardizeWordBracketSpaces:
                    res = self.standardizeWordBracketSpaces_Latin(res)
                if standardizeWordPunctuationSpaces:
                    res = self.standardizeWordPunctuationSpaces_French(res)
                if standardizeWordSpaces:
                    res = self.standardizeWordSpaces_Latin(res)
                if standardizeWordQuoteSpaces:
                    res = self.standardizeWordQuoteSpaces_Latin(res)
                    if not uncurlQuotes:
                        res = self.convertQuotes_French(res)
                    else:
                        res = self.standardizeWordQuoteSpaces_French(res)
                if standardizeApostrophe:
                    res = self.convertApostrophe_French(res)
                if standardizePercentages:
                    res = self.standardizePercentages_French(res)
                if standardizeNumbers:
                    res = self.standardizeNumbers_French(res, source_text)

            elif self.lang == 'jpn':
                res = ftfy.fix_text(text, fix_character_width=False, uncurl_quotes=uncurlQuotes)

                if standardizePercentages:
                    res = self.standardizePercentages(res)
                if standardizeWordBracketSpaces:
                    res = self.standardizeWordBracketSpaces_Japanese(res)
                if standardizeWordQuoteSpaces:
                    res = self.standardizeWordQuoteSpaces_Japanese(res)
                if standardizeWordPunctuationSpaces:
                    res = self.standardizeWordPunctuationSpaces_Japanese(res)
                if standardizeWordSpaces:
                    res = self.standardizeWordSpaces_Latin(res)

            elif self.lang in ('ypt', 'zhh', 'zhs', 'zht'):
                res = ftfy.fix_text(text, fix_character_width=False, uncurl_quotes=uncurlQuotes)

                if standardizePercentages:
                    res = self.standardizePercentages(res)
                if standardizeWordBracketSpaces:
                    res = self.standardizeWordBracketSpaces_Chinese(res)
                if standardizeWordQuoteSpaces:
                    res = self.standardizeWordQuoteSpaces_Chinese(res)
                if standardizeWordPunctuationSpaces:
                    res = self.standardizeWordPunctuationSpaces_Chinese(res)
                if standardizeWordSpaces:
                    res = self.standardizeWordSpaces_Chinese(res,
                                                             addSpaceBetweenChineseAndHalfwidth=addSpaceBetweenFullwidthAndHalfwidth)
            else:
                raise NotImplementedError('Language %s is not supported' % self.lang)

        except:
            return text

        return res


class TextMatcher:
    """It matches a target text against a reference text for orthographical agreement
    """

    def __init__(self, refLang, targetLang):
        """Initialize a TextMatcher instance

           Args:
              refLang (str): the 3-letter Yappn language code for the reference text
              targetLang (str): the 3-letter Yappn language code for the target text
        """

        self.refLang = refLang
        self.tgtLang = targetLang
        self.latinLang = ('ces', 'dan', 'nld', 'eng', 'fin', 'fra', 'deu', 'ell', 'ita', 'nor',
                          'pol', 'por', 'spa', 'swe', 'tur')

        refPunctuations = Writing.PUNCTUATIONS_FOR_MAPPINGS[refLang]
        tgtPunctuations = Writing.PUNCTUATIONS_FOR_MAPPINGS[targetLang]

        if (refLang, targetLang) == ('eng', 'fra'):
            self.ref2tgtPuncMappings_first = dict(zip(refPunctuations + '"“”', tgtPunctuations + '««»'))
            self.ref2tgtPuncMappings_last = dict(zip(refPunctuations + '"“”', tgtPunctuations + '»«»'))
            self.tgt2refPuncMappings_first = dict(zip(tgtPunctuations + '«»', refPunctuations + '""'))
            self.tgt2refPuncMappings_last = dict(zip(tgtPunctuations + '«»', refPunctuations + '""'))

        elif (refLang, targetLang) == ('fra', 'eng'):
            self.ref2tgtPuncMappings_first = dict(zip(tgtPunctuations + '«»', refPunctuations + '""'))
            self.ref2tgtPuncMappings_last = dict(zip(tgtPunctuations + '«»', refPunctuations + '""'))
            self.tgt2refPuncMappings_first = dict(zip(refPunctuations + '"“”', tgtPunctuations + '««»'))
            self.tgt2refPuncMappings_last = dict(zip(refPunctuations + '"“”', tgtPunctuations + '»«»'))

        self.left2rightBracketMappings = {left: right for (left, right) in Writing.BRACKETS}
        self.right2leftBracketMappings = {right: left for (left, right) in Writing.BRACKETS}

        self._superscriptMappings = dict(zip('0123456789()', '⁰¹²³⁴⁵⁶⁷⁸⁹⁽⁾'))
        self._superscriptTranslationTable = str.maketrans(self._superscriptMappings)

        self._regex_patterns = {'first_fra_left_quotation': r'^(?P<left_quotation>«)(?P<post_text>[^\xa0].*)$',
                                'last_fra_right_quotation': r'^(?P<pre_text>.*[^\xa0])(?P<right_quotation>»)$'}

        self._textHumanier = TextHumanizer(targetLang)

    def matchFirstCase_Latin(self, refText, targetText):
        """Match the case of the first letter of two Latin texts

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        EXCEPTIONS = ('BMO', 'BNP', 'CIBC', 'HSBC', 'RBC', 'TD', 'TSX', 'UBS')

        # All-uppercase words are to be excepted

        if targetText.split()[0] in EXCEPTIONS:
            res = targetText
        else:
            letterPattern = r'(?V1)[\w--[0-9]]'

            firstLetterInRefText = re.match(letterPattern, refText)
            firstLetterInTgtText = re.match(letterPattern, targetText)

            # Has no letter
            if (not firstLetterInRefText) or (not firstLetterInTgtText):
                res = targetText
            else:
                if firstLetterInRefText.group().isupper():
                    res = re.sub(firstLetterInTgtText.group(), firstLetterInTgtText.group().upper(), targetText, 1)
                else:
                    res = re.sub(firstLetterInTgtText.group(), firstLetterInTgtText.group().lower(), targetText, 1)

        return res

    def matchFirstPunctuation(self, refText, targetText):
        """Match the "first" punctuation of two texts using heuristics

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        refPunctuations = self.ref2tgtPuncMappings_first.keys()
        tgtPunctuations = self.tgt2refPuncMappings_first.keys()

        # First characters are not punctuations: do nothing
        if (refText[0] not in refPunctuations) and (targetText[0] not in tgtPunctuations):
            res = targetText
        # First characters are mapping punctuations: do nothing
        elif ((refText[0] in refPunctuations) and (targetText[0] in tgtPunctuations) and
              targetText[0] == self.ref2tgtPuncMappings_first[refText[0]]):
            res = targetText
        # First character in target is punctuation
        # and first character in ref is not punctuation: delete the first character in target
        elif ((refText[0] not in refPunctuations) and (targetText[0] in tgtPunctuations)):
            p = r'^' + re.escape(targetText[0]) + r'+(?P<text>.+)$'
            try:
                res = re.sub(p, re.search(p, targetText).group('text'), targetText)
            except:
                res = targetText
        # First character in ref is punctuation but has no mapping in target
        # and first character in target is not punctuation: prepend a mapping punctuation to target
        elif ((refText[0] in refPunctuations) and (targetText[0] not in tgtPunctuations) and
              self.ref2tgtPuncMappings_first[refText[0]] not in targetText):
            res = self.ref2tgtPuncMappings_first[refText[0]] + targetText
            # First characters in ref and target are non-mapping punctuations
        # and first character in ref has no mapping in target: prepend a mapping punctuation to target
        elif ((refText[0] in refPunctuations) and (targetText[0] in tgtPunctuations) and
              targetText[0] != self.ref2tgtPuncMappings_first[refText[0]] and
              self.ref2tgtPuncMappings_first[refText[0]] not in targetText):
            res = self.ref2tgtPuncMappings_first[refText[0]] + targetText
        else:
            res = targetText

        res = re.sub(self._regex_patterns['first_fra_left_quotation'],
                     lambda m: m.group('left_quotation') + '\xa0' + m.group('post_text'), res)

        return res

    def matchLastPunctuation(self, refText, targetText):
        """Match the "last" punctuation of two texts using heuristics

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        refPunctuations = self.ref2tgtPuncMappings_last.keys()
        tgtPunctuations = self.tgt2refPuncMappings_last.keys()

        # Last characters are not punctuations: do nothing
        if (refText[-1] not in refPunctuations) and (targetText[-1] not in tgtPunctuations):
            res = targetText
        # Last characters are mapping punctuations: do nothing
        elif ((refText[-1] in refPunctuations) and (targetText[-1] in tgtPunctuations) and
              targetText[-1] == self.ref2tgtPuncMappings_last[refText[-1]]):
            res = targetText
        # Last character in target is punctuation
        # and last character in ref is not punctuation: delete the last character in target
        elif ((refText[-1] not in refPunctuations) and (targetText[-1] in tgtPunctuations)):
            p = r'^(?P<text>.+?)' + re.escape(targetText[-1]) + r'+$'
            try:
                res = re.sub(p, re.search(p, targetText).group('text'), targetText)
            except:
                res = targetText
        # Last character in ref is punctuation but has no mapping in target
        # and last character in target is not punctuation: append a mapping punctuation to target
        elif ((refText[-1] in refPunctuations) and (targetText[-1] not in tgtPunctuations) and
              self.ref2tgtPuncMappings_last[refText[-1]] not in targetText):
            res = targetText + self.ref2tgtPuncMappings_last[refText[-1]]
            # Last characters in ref and target are non-mapping punctuations
        # and last character in ref has no mapping in target: append a mapping punctuation to target
        elif ((refText[-1] in refPunctuations) and (targetText[-1] in tgtPunctuations) and
              targetText[-1] != self.ref2tgtPuncMappings_last[refText[-1]] and
              self.ref2tgtPuncMappings_last[refText[-1]] not in targetText):
            res = targetText + self.ref2tgtPuncMappings_last[refText[-1]]
        else:
            res = targetText

        res = re.sub(self._regex_patterns['last_fra_right_quotation'],
                     lambda m: m.group('pre_text') + '\xa0' + m.group('right_quotation'), res)

        return res

    def matchPairedBrackets(self, refText, targetText):
        """Match the paired brackets with the same bracketed content

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        patterns = (r'(?V1)(?P<bracketed>\([\w--[_]]+?\))',
                    r'(?V1)(?P<bracketed>\[[\w--[_]]+?\])',
                    r'(?V1)(?P<bracketed>\{[\w--[_]]+?\})')

        res = targetText

        for p in patterns:
            refBracketedItems = re.findall(p, refText)
            for refBracketedItem in refBracketedItems:
                if (re.search(re.escape(refBracketedItem[1:]), res) and (
                        not re.search(re.escape(refBracketedItem), res)) and
                        (not re.search(r'(?V1)[\w--[_]]' + re.escape(refBracketedItem[1:]), res))):
                    res = re.sub(re.escape(refBracketedItem[1:]),
                                 self.right2leftBracketMappings[refBracketedItem[1:][-1]] + refBracketedItem[1:],
                                 res, 1)
                elif (re.search(re.escape(refBracketedItem[:-1]), res) and (
                        not re.search(re.escape(refBracketedItem), res)) and
                      (not re.search(r'(?V1)' + re.escape(refBracketedItem[:-1]) + r'[\w--[_]]', res))):
                    res = re.sub(re.escape(refBracketedItem[:-1]),
                                 refBracketedItem[:-1] + self.left2rightBracketMappings[refBracketedItem[:-1][0]],
                                 res, 1)

        return res

    def matchReferenceNumberFormatting(self, refText, targetText):
        """Match the reference number formatting,
           E.g, # of stocks (eng), yyy (1) (fra) -> yyy ¹⁾ (fra)

           This is language-specific

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        res = targetText

        if self.refLang == 'eng' and self.tgtLang == 'fra':
            ref_pattern = r'.+(?P<referenced>⁽[⁰¹²³⁴⁵⁶⁷⁸⁹]+⁾$)'
            tgt_pattern = r'^(?P<text>.+)(?P<referenced>(\([0-9]+\))|(⁽[⁰¹²³⁴⁵⁶⁷⁸⁹]+⁾)$)'

            refMatch = re.search(ref_pattern, refText)
            tgtMatch = re.search(tgt_pattern, res)

            if refMatch and tgtMatch:
                if tgtMatch.group('referenced').translate(self._superscriptTranslationTable) == refMatch.group(
                        'referenced'):
                    res = tgtMatch.group('text') + refMatch.group('referenced')[1:]

        return res

    def matchNumberSymbol(self, refText, targetText):
        """Match the number symbol,
           E.g,  # of stocks (eng), # d’actions (fra) -> nᵇʳᵉ d’actions (fra)
                 nᵇʳᵉ de stocks (fra), nᵇʳᵉ of stocks (eng) -> number of stocks (eng)
                 please refer to scenario no. 1 (eng), veuillez vous reporter au scénario no. 1 (fra) ->
                                                       veuillez vous reporter au scénario n° 1 (fra)
                 se reporter au scénario no. 1 et n° 2. (fra), see scenario no. 1 and No. 2. (eng) ->
                                                               see scenario no. 1 and no. 2. (eng)
           This is language-specific

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed

           Returns:
              (str): the matched target text
        """

        res = targetText

        if self.refLang == 'eng' and self.tgtLang == 'fra':

            # '#' -> 'nᵇʳᵉ'
            ref_pattern = r'(?P<before>^|^[^#]*?\s)(?P<pound_sign>#)(?P<after>\s[^#]+)$'
            tgt_pattern = r'(?P<before>^|^[^#]*?\s)(?P<pound_sign>#)(?P<after>\s[^#]+)$'

            refMatch = re.search(ref_pattern, refText)
            tgtMatch = re.search(tgt_pattern, res)

            if refMatch and tgtMatch:
                res = tgtMatch.group('before') + 'nᵇʳᵉ' + tgtMatch.group('after')

            # 'no. 1' -> 'n° 1'

            ref_pattern = r'(?i)(?P<before>^|\s)(?P<number_word>no\.|n °|n°)\s*(?P<number>\d+)(?P<after>\W|$)'
            tgt_pattern = r'(?i)(?P<before>^|\s)(?P<number_word>no\.|n °|n°)\s*(?P<number>\d+)(?P<after>\W|$)'

            refFound = re.findall(ref_pattern, refText, overlapped=True)
            tgtFound = re.findall(tgt_pattern, res, overlapped=True)

            if refFound and tgtFound and len(refFound) == len(tgtFound):
                res = re.sub(tgt_pattern, lambda m: m.group('before') + 'n° ' + m.group('number') + m.group('after'),
                             res)

        elif self.refLang == 'fra' and self.tgtLang == 'eng':

            # 'nᵇʳᵉ' -> 'number'
            ref_pattern = r'(?i)(?P<before>^|^.*?\s)(?P<number_word>nᵇʳᵉ)(?P<after>\s.+)$'
            tgt_pattern = r'(?i)(?P<before>^|^.*?\s)(?P<number_word>nᵇʳᵉ)(?P<after>\s.+)$'

            refMatch = re.search(ref_pattern, refText)
            tgtMatch = re.search(tgt_pattern, res)

            if refMatch and tgtMatch:
                res = tgtMatch.group('before') + 'number' + tgtMatch.group('after')

            # 'n° 1' -> 'no. 1'

            ref_pattern = r'(?i)(?P<before>^|\s)(?P<number_word>no\.|n °|n°)\s*(?P<number>\d+)(?P<after>\W|$)'
            tgt_pattern = r'(?i)(?P<before>^|\s)(?P<number_word>no\.|n °|n°)\s*(?P<number>\d+)(?P<after>\W|$)'

            refFound = re.findall(ref_pattern, refText, overlapped=True)
            tgtFound = re.findall(tgt_pattern, res, overlapped=True)

            if refFound and tgtFound and len(refFound) == len(tgtFound):
                res = re.sub(tgt_pattern, lambda m: m.group('before') + 'no. ' + m.group('number') + m.group('after'),
                             res)

        return res

    def matchForm(self, refText, targetText,
                  matchFirstCase=True,
                  matchFirstPunctuation=True,
                  matchLastPunctuation=True,
                  matchPairedBrackets=True,
                  matchReferenceNumberFormatting=True,
                  matchNumberSymbol=True):
        """Match the orthographical form of two texts

           Args:
              refText (str): the reference text
              targetText (str): the target text to be matched and changed
              matchFirstCase (bool): whether to match the case of the first letter
              matchFirstPunctuation (bool): whether to match the punctuation at the first character
              matchLastPunctuation (bool): whether to match the punctuation at the last character
              matchPairedBrackets (bool): whether to match paired brackets
              matchReferenceNumberFormatting (bool): whether to match reference number formatting
              matchNumberSymbol (bool): whether to match number symbols

           Returns:
              (str): the matched target text
        """

        res = targetText
        refText = re.sub(r'<[^>]+>', '', refText)

        if not res:
            res = refText
        else:
            try:
                if matchFirstPunctuation:
                    res = self.matchFirstPunctuation(refText, res)

                if matchLastPunctuation:
                    res = self.matchLastPunctuation(refText, res)

                if matchPairedBrackets:
                    res = self.matchPairedBrackets(refText, res)

                if matchReferenceNumberFormatting:
                    res = self.matchReferenceNumberFormatting(refText, res)

                if matchNumberSymbol:
                    res = self.matchNumberSymbol(refText, res)

                if matchFirstCase:
                    if self.refLang in self.latinLang and self.tgtLang in self.latinLang:
                        res = self.matchFirstCase_Latin(refText, res)
                    else:
                        raise NotImplementedError(
                            '%s and %s are not both Latin languages and not supported' % (self.refLang, self.tgtLang))

                if self.tgtLang == 'fra':
                    res = self._textHumanier.standardizeWordQuoteSpaces_French(res)
            except:
                print('matchform error')

        return res


class TextComparator:
    """It compares texts according to certain criteria
    """

    def __init__(self, lang1=None, lang2=None):
        """Initialize a TextComparator instance

           Args:
              lang1 (str or None): the 3-letter Yappn language code of the first language
              lang2 (str or None): the 3-letter Yappn language code of the second language
        """

        self.lang1 = lang1
        self.lang2 = lang2

        try:
            if None in (self.lang1, self.lang2):
                self._ld = LanguageDetector(langCodeFormat='yappn')
            else:
                self._ld = LanguageDetector(langCodeFormat='yappn', languages=[self.lang1, self.lang2])
        except:
            self._ld = LanguageDetector(langCodeFormat='yappn')

    def calculateLengthSimilarity(self, text1, text2, method):
        """Calculate the length similarity according to a given method

           Args:
              text1 (str): the first text
              text2 (str): the second text
              method (str): word-based or character-based
                            "char": the length similarity in terms of characters
                            "word": the length similarity in terms of words

           Returns:
              (int or float): the similarity score (0 .. 1); larger means similar
        """

        assert isinstance(text1, str) and isinstance(text2, str)

        if text1 == '' and text2 == '':
            res = 1
        else:
            if not self.lang1:
                self.lang1 = self._ld.detect(text1)
            if not self.lang2:
                self.lang2 = self._ld.detect(text2)

            if method == 'word':
                words1 = WordTokenizer(self.lang1, 'nltk').tokenize(text1)
                words2 = WordTokenizer(self.lang2, 'nltk').tokenize(text2)
                lenWords1, lenWords2 = len(words1), len(words2)
                res = min(lenWords1, lenWords2) / max(lenWords1, lenWords2)
            elif method == 'char':
                lenChars1, lenChars2 = len(text1), len(text2)
                res = min(lenChars1, lenChars2) / max(lenChars1, lenChars2)
            else:
                raise NotImplementedError('Method %s is not implemented' % method)

        return res

    def calculateStringSimilarity(self, text1, text2, method):
        """Calculate the string similarity according to a given method

           Args:
              text1 (str): the first text
              text2 (str): the second text
              method (str): a string similarity comparison algorithm
                            In theory it should support all algorithms/functions available in 3rd party modules
                            In practice the current implementation supports the following:
                            "levenshtein": the Levenshtein algorithm
                            "damerau-levenshtein": the Damerau-Levenshtein algorithm
                            "jaro": The Jaro algorithm
                            "jaro-winkler": The Jaro-Winkler algorithm
                            "jaccard": The Jaccard index
                            "sorensen-dice": The Sørensen–Dice coefficient
                            "cosine": The Cosine similarity
                            "ratcliff-obershelp": The Ratcliff-Obershelp similarity

           Returns:
              (int or float): the similarity score (0 .. 1); larger means similar
        """

        assert isinstance(text1, str) and isinstance(text2, str)

        if text1 == '' and text2 == '':
            res = 1
        else:
            if method == 'levenshtein':
                res = textdistance.levenshtein.normalized_similarity(text1, text2)
            elif method == 'damerau-levenshtein':
                res = textdistance.damerau_levenshtein.normalized_similarity(text1, text2)
            elif method == 'jaro':
                res = textdistance.jaro.normalized_similarity(text1, text2)
            elif method == 'jaro-winkler':
                res = textdistance.jaro_winkler.normalized_similarity(text1, text2)
            elif method == 'jaccard':
                res = textdistance.jaccard.normalized_similarity(text1, text2)
            elif method == 'sorensen-dice':
                res = textdistance.sorensen_dice.normalized_similarity(text1, text2)
            elif method == 'cosine':
                res = textdistance.cosine.normalized_similarity(text1, text2)
            elif method == 'ratcliff-obershelp':
                res = textdistance.ratcliff_obershelp.normalized_similarity(text1, text2)
            else:
                raise NotImplementedError('Method %s is not implemented' % method)

        return res


class ChineseProcessor:
    """It deals with special aspects of the Chinese text
    """

    def __init__(self, lang):
        """Initialize a ChineseProcessor instance

           Args:
              lang (str): the 3-letter Yappn language code
        """

        assert lang in ('ypt', 'zhh', 'zhs', 'zht')

        self.lang = lang

    def isChineseCharacter(self, char, punctuation=True):
        """Decide if a character is a Chinese character

           Args:
              char (str): the input character (len = 1)
              punctuation (bool): whether to include Chinese punctuations

           Returns:
              (bool): whether the character is Chinese or not
        """

        assert isinstance(char, str) and len(char) == 1

        if unicodedata.name(char).split()[0] == 'CJK':
            res = True
        elif punctuation:
            res = char in Writing.PUNCTUATIONS_SENTENCE_COMMON[self.lang]
        else:
            res = False

        return res

    def isChinesePunctuation(self, char):
        """Decide if a character is a Chinese punctuation

           Args:
              char (str): the input character (len = 1)

           Returns:
              (bool): whether the character is a Chinese punctuation or not
        """

        assert isinstance(char, str) and len(char) == 1

        res = char in Writing.PUNCTUATIONS_SENTENCE_COMMON[self.lang]

        return res

    def isChineseText(self, text):
        """Decide if the input text is Chinese

           Args:
              text (str): the input text

           Returns:
              (bool): whether the text is Chinese or not
        """

        assert isinstance(text, str)

        # Normalize white spaces
        text = re.sub('\s', ' ', text)

        if langid.classify(text)[0] == 'zh':
            # Filter quasi-Chinese text
            res = True
            for char in text:
                try:
                    # Legitimate letter
                    if unicodedata.name(char).split()[0] in ('CJK', 'LATIN'):
                        continue
                    # Number
                    elif unicodedata.category(char).startswith('N'):
                        continue
                    # Punctuation
                    elif unicodedata.category(char).startswith('P'):
                        continue
                        # Symbol
                    elif unicodedata.category(char).startswith('S'):
                        continue
                        # Space
                    elif unicodedata.category(char) == 'Zs':
                        continue
                    else:
                        res = False
                        break
                except:
                    res = False
                    break
        else:
            res = False

        return res

    def isSimplified(self, text):
        """Decide if the input text is Simplified Chinese,
           i.e., all the Chinese characters are simplified

           Args:
              text (str): the input text

           Returns:
              (bool): whether the text is Simplified Chinese
        """

        assert isinstance(text, str)

        res = HanziConv.toSimplified(text) == text

        return res

    def isTraditional(self, text):
        """Decide if the input text is Traditional Chinese,
           i.e., all the Chinese characters are traditional

           Args:
              text (str): the input text

           Returns:
              (bool): whether the text is Traditional Chinese
        """

        assert isinstance(text, str)

        res = HanziConv.toTraditional(text) == text

        return res

    def isCorrectFormat(self, text):
        """Decide if the input text is in the correct format as specified by 'lang',
           i.e., 'zhh' and 'zhs' should be simplified; 'zht' and 'ypt' should be traditional

           Args:
              text (str): the input text

           Returns:
              (bool): whether the text is Traditional Chinese
        """

        assert isinstance(text, str)

        if self.lang in ('zhh', 'zhs'):
            res = self.isSimplified(text)
        elif self.lang in ('zht', 'ypt'):
            res = self.isTraditional(text)
        else:
            raise ValueError('%s is not Chinese' % self.lang)

        return res

    def convertFormat(self, text, toFormat):
        """Convert the text from one format to the another format

           Args:
              text (str): the input text
              toFormat (str): 'simplified' or 'traditional'
           Returns:
              (str): the converted text
        """

        assert toFormat in ('simplified', 'traditional')

        if toFormat == 'simplified':
            res = HanziConv.toSimplified(text)
        else:
            res = HanziConv.toTraditional(text)

        return res


class JapaneseProcessor:
    """It deals with special aspects of the Japanese text
    """

    def __init__(self, lang='jpn'):
        """Initialize a JapaneseProcessor instance

           Args:
              lang (str): the 3-letter Yappn language code
        """

        assert lang == 'jpn'

        self.lang = lang

    def isJapaneseCharacter(self, char, punctuation=True):
        """Decide if a character is a Japanese character

           Args:
              char (str): the input character (len = 1)
              punctuation (bool): whether to include Japanese punctuations

           Returns:
              (bool): whether the character is Japanese or not
        """

        assert isinstance(char, str) and len(char) == 1

        if unicodedata.name(char).split()[0] in ('CJK', 'HIRAGANA', 'KATAKANA', 'KATAKANA-HIRAGANA'):
            res = True
        elif punctuation:
            res = char in Writing.PUNCTUATIONS_SENTENCE_COMMON[self.lang]
        else:
            res = False

        return res

    def isJapanesePunctuation(self, char):
        """Decide if a character is a Japanese punctuation

           Args:
              char (str): the input character (len = 1)

           Returns:
              (bool): whether the character is a Japanese punctuation or not
        """

        assert isinstance(char, str) and len(char) == 1

        res = char in Writing.PUNCTUATIONS_SENTENCE_COMMON[self.lang]

        return res

    def isJapaneseText(self, text):
        """Decide if the input text is Japanese

           Args:
              text (str): the input text

           Returns:
              (bool): whether the text is Japanese or not
        """

        assert isinstance(text, str)

        # Normalize white spaces
        text = re.sub('\s', ' ', text)

        if langid.classify(text)[0] == 'ja':
            # Filter quasi-Japanese text
            res = True
            for char in text:
                try:
                    # Legitimate letter
                    if unicodedata.name(char).split()[0] in ('CJK', 'HIRAGANA', 'KATAKANA',
                                                             'KATAKANA-HIRAGANA', 'LATIN'):
                        continue
                    # Number
                    elif unicodedata.category(char).startswith('N'):
                        continue
                    # Punctuation
                    elif unicodedata.category(char).startswith('P'):
                        continue
                        # Symbol
                    elif unicodedata.category(char).startswith('S'):
                        continue
                        # Space
                    elif unicodedata.category(char) == 'Zs':
                        continue
                    else:
                        res = False
                        break
                except:
                    res = False
                    break
        else:
            res = False

        return res


def test1():
    wt1 = WordTokenizer('zhs')
    sent1 = '你好，这是一个中文句子。'

    wt2 = WordTokenizer('spa')
    sent2 = 'Está lloviendo mucho.'

    print(wt1.tokenize(sent1))
    print(wt2.tokenize(sent2))


def test2():
    """Clean a zhs text file
    """

    inputPath = r'L:\Training data\benchmark preprocessed datasets 2018_08\preprocessed_and_domaindata\eng_zhs\generic\yappn_generic_eng_zhs_20180913_test.zhs'
    outputPath = r'L:\Training data\benchmark preprocessed datasets 2018_08\preprocessed_and_domaindata\eng_zhs\generic\yappn_generic_eng_zhs_20181121_test.zhs'
    lang = 'zhs'
    toFormat = 'simplified'
    th = TextHumanizer(lang)
    cp = ChineseProcessor(lang)

    f = open(inputPath, 'rb')
    raw = [line.decode('utf8') for line in f]

    cleaned = [th.humanizeText(cp.convertFormat(line, toFormat))
               for line in raw if cp.isChineseText(line)]

    with open(outputPath, 'wb') as f:
        f.writelines([(line + '\n').encode('utf8') for line in cleaned])


def test3():
    """Clean a zht text file
    """

    inputPath = r'L:\Training data\benchmark preprocessed datasets 2018_08\preprocessed_and_domaindata\eng_zht\generic\yappn_generic_eng_zht_20180913_test.zht'
    outputPath = r'L:\Training data\benchmark preprocessed datasets 2018_08\preprocessed_and_domaindata\eng_zht\generic\yappn_generic_eng_zht_20181121_test.zht'
    lang = 'zht'
    toFormat = 'traditional'
    th = TextHumanizer(lang)
    cp = ChineseProcessor(lang)

    f = open(inputPath, 'rb')
    raw = [line.decode('utf8') for line in f]

    cleaned = [th.humanizeText(cp.convertFormat(line, toFormat), standardizeWordSpaces=False)
               for line in raw if cp.isChineseText(line)]

    with open(outputPath, 'wb') as f:
        f.writelines([(line + '\n').encode('utf8') for line in cleaned])


if __name__ == '__main__':
    # res = test1()
    # res = test2()
    res = test3()

    print('\nCompleted successfully')
