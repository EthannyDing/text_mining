# -*- coding: utf-8 -*-

# rbmt: rules
#
# Author: Jason Cox, Renxian Zhang
# --------------------------------------------------
# This module implements rules for Rule-Based Machine Translation

from decimal import Decimal

import regex as re
import dateparser
from babel.dates import format_date, format_time, format_datetime
from babel import numbers
from babel.numbers import format_currency, format_decimal, parse_decimal, format_percent
from price_parser import parse_price

from .language_resources import Codes, CommonRegex

NAME_YAPPN_MAPPINGS = Codes.mappings('name', 'yappn')
CULTURE_CODES = Codes.CULTURE_CODES


class DatetimeTranslator:
    """Rule-based date/time translation using dateparser and Babel
    """

    def __init__(self, dtFormat, sourceLang, targetLang, targetLocale, scope, fullmatch=False):
        """Initialize a DatetimeTranslator instance

           Args:
              dtFormat (str): date/time format
                              'full', 'long', 'medium', 'short', or a custom date/time pattern
                              Refer to the Babel doc
              sourceLang (str): source language in full spelling, e.g., 'English'
              targetLang (str): target language in full spelling, e.g., 'French'
                                ignored if targetLocale is provided
              targetLocale (str): target locale identifier
              scope (str): the scope of translation
                           'date', 'time', or 'datetime'
              fullmatch (bool): whether to full-match a text or not
                                if True, DatetimeTranslator can act as an independent translator
                                if False, DatetimeTranslator must work with other translators
        """

        assert scope in ('date', 'time', 'datetime')

        self._dtFormat = dtFormat
        self.srcLang = NAME_YAPPN_MAPPINGS[sourceLang]
        self.tgtLocale = targetLocale if targetLocale else re.sub('-', '_', CULTURE_CODES[targetLang][0])
        self._scope = scope
        self._fullmatch = fullmatch

    def convert(self, text):
        """Convert date/time according to the target locale

           Args:
              text (str): date/time text
           Returns:
              (str): converted date/time
        """

        dt = dateparser.parse(text)

        if dt:
            if self._scope == 'date':
                res = format_date(dt, self._dtFormat, self.tgtLocale)
            elif self._scope == 'time':
                res = format_time(dt, self._dtFormat, self.tgtLocale)
            else:
                res = format_datetime(dt, self._dtFormat, self.tgtLocale)
        else:
            res = None

        return res

    def translate(self, text):
        """Translate text with date/time expression

           Args:
              text (str): text including date/time expression
           Returns:
              (str): text with translated date/time
                     if None, no datetime translation rule is matched
        """

        pattern = CommonRegex.DATE_PATTERN_ymd[self.srcLang]
        if self._fullmatch:
            pattern = r'(?i)(?P<date>' + r'^' + pattern[len(r'(?i)(?P<date>'):len(pattern) - 1] + r'$)'
        pr = re.compile(pattern)

        res = None

        try:
            if pr.search(text):
                res = pr.sub(lambda m: self.convert(m.group('date')), text)
        except:
            pass

        return res


class NumberTranslator:
    """Rule-based number translation
    """

    def __init__(self, sourceLang, targetLang, sourceLocale, targetLocale, fullmatch=False):
        """Initialize a NumberTranslator instance

           Args:
              sourceLang (str): source language in full spelling, e.g., 'English'
                                ignored if sourceLocale is provided
              sourceLocale (str): source locale identifier
              targetLang (str): target language in full spelling, e.g., 'French'
                                ignored if targetLocale is provided
              targetLocale (str): target locale identifier
              fullmatch (bool): whether to full-match a text or not
                                if True, NumberTranslator can act as an independent translator
                                if False, NumberTranslator must work with other translators
        """

        self.srcLang = NAME_YAPPN_MAPPINGS[sourceLang]
        self.srcLocale = sourceLocale if sourceLocale else re.sub('-', '_', CULTURE_CODES[sourceLang][0])
        self.tgtLocale = targetLocale if targetLocale else re.sub('-', '_', CULTURE_CODES[targetLang][0])
        self._fullmatch = fullmatch

        self.srcDecimalSymbol = numbers.get_decimal_symbol(self.srcLocale)
        self.tgtDecimalSymbol = numbers.get_decimal_symbol(self.tgtLocale)
        self.srcGroupSymbol = numbers.get_group_symbol(self.srcLocale)
        self.tgtGroupSymbol = numbers.get_group_symbol(self.tgtLocale)

    def convert(self, text, check_group_symbol=False):
        """Convert number according to the target locale

           Args:
              text (str): number text
           Returns:
              (str): converted number
        """

        try:
            numberText = str(parse_decimal(text, locale=self.srcLocale))

            if numberText:
                res = format_decimal(numberText, locale=self.tgtLocale, decimal_quantization=False)

                # if (self.srcGroupSymbol in text) and (self.tgtGroupSymbol in res):
                # if (self.srcDecimalSymbol in text) and (self.tgtDecimalSymbol not in res):
                # res += self.tgtDecimalSymbol + text[text.index(self.srcDecimalSymbol) + 1:]

                if check_group_symbol:
                    if all([self.srcGroupSymbol in text, self.tgtGroupSymbol in res,
                            self.srcDecimalSymbol in text, self.tgtDecimalSymbol not in res]):
                        res += self.tgtDecimalSymbol + text[text.index(self.srcDecimalSymbol) + 1:]
                    else:
                        res = text
                else:
                    if all([self.srcDecimalSymbol in text, self.tgtDecimalSymbol not in res]):
                        res += self.tgtDecimalSymbol + text[text.index(self.srcDecimalSymbol) + 1:]

                        # else:
                    # res = text
            else:
                res = None
        except:
            res = None

        return res

    def translate(self, text):
        """Translate text with number expression

           Args:
              text (str): text including number expression
           Returns:
              (str): text with translated number
                     if None, no number translation rule is matched
        """

        number_only_pattern = r'^\s*(\d+)\s*$'
        num_pr = re.compile(number_only_pattern)

        if self.srcLang == 'eng':
            pattern = r'(?P<number>[\d]+(?:[,]\d\d\d)*[\.]?\d*)'
        elif self.srcLang == 'fra':
            pattern = r'(?P<number>[\d]+(?:[\s]\d\d\d)*[,]?\d*)'
        else:
            raise NotImplementedError('Language %s is not supported' % self.srcLang)

        if self._fullmatch:
            pattern = r'(?P<number>' + r'^' + pattern[len(r'(?P<number>'):len(pattern) - 1] + r'$)'
        pr = re.compile(pattern)

        res = None

        try:
            if num_pr.search(text):
                res = pr.sub(lambda m: self.convert(m.group('number'), True), text)
            elif pr.search(text):
                res = pr.sub(lambda m: self.convert(m.group('number')), text)
        except:
            pass

        return res


class PercentTranslator:
    """Rule-based percent translation
    """

    def __init__(self, sourceLang, targetLang, sourceLocale, targetLocale, fullmatch=False):
        """Initialize a PercentTranslator instance

           Args:
              sourceLang (str): source language in full spelling, e.g., 'English'
                                ignored if sourceLocale is provided
              sourceLocale (str): source locale identifier
              targetLang (str): target language in full spelling, e.g., 'French'
                                ignored if targetLocale is provided
              targetLocale (str): target locale identifier
              fullmatch (bool): whether to full-match a text or not
                                if True, PercentTranslator can act as an independent translator
                                if False, PercentTranslator must work with other translators
        """

        self.srcLang = NAME_YAPPN_MAPPINGS[sourceLang]
        self.srcLocale = sourceLocale if sourceLocale else re.sub('-', '_', CULTURE_CODES[sourceLang][0])
        self.tgtLocale = targetLocale if targetLocale else re.sub('-', '_', CULTURE_CODES[targetLang][0])
        self._fullmatch = fullmatch

        self.srcDecimalSymbol = numbers.get_decimal_symbol(self.srcLocale)
        self.tgtDecimalSymbol = numbers.get_decimal_symbol(self.tgtLocale)

    def _floatPrecision(self, percentText, decimalSymbol):
        """Return the float precision of the percent text
           E.g. 15% -> 2; 13.0% -> 3

           Args:
              percentText (str): the percent text
              decimalSymbol (str): the decimal symbol ('.' or ',', etc.)

           Returns:
              (int): the number of float precision
        """

        assert '%' in percentText

        numberText = percentText.strip('%')

        if decimalSymbol in numberText:
            res = len(numberText[numberText.index(decimalSymbol) + 1:]) + 2
        else:
            res = 2

        return res

    def convert(self, text):
        """Convert percent according to the target locale

           Args:
              text (str): percent text
           Returns:
              (str): converted percent
        """

        percentPattern = r'^(?P<number>[,\.\xa0\d]*\d)(?P<symbol>\s*%)$'
        numberText = str(parse_decimal(text.strip('%'), locale=self.srcLocale))
        srcFloatPrecision = self._floatPrecision(text, self.srcDecimalSymbol)

        try:
            assert '%' in text

            percentText = str(
                parse_decimal(str((Decimal(numberText) / 100).quantize(Decimal(10) ** -srcFloatPrecision)),
                              locale=self.srcLocale))

            if percentText:
                res = format_percent(percentText, locale=self.tgtLocale, decimal_quantization=False)

                if self.srcDecimalSymbol in text:
                    match = re.search(percentPattern, res)
                    if self.tgtDecimalSymbol not in res:
                        res = match.group('number') + self.tgtDecimalSymbol + numberText[
                                                                              numberText.index('.') + 1:] + match.group(
                            'symbol')
                    elif len(match.group('number')[
                             match.group('number').index(self.tgtDecimalSymbol) + 1:]) != srcFloatPrecision - 2:
                        res = match.group('number')[
                              :match.group('number').index(self.tgtDecimalSymbol)] + self.tgtDecimalSymbol + numberText[
                                                                                                             numberText.index(
                                                                                                                 '.') + 1:] + match.group(
                            'symbol')
            else:
                res = None
        except:
            res = None

        return res

    def translate(self, text):
        """Translate text with percent expression

           Args:
              text (str): text including percent expression
           Returns:
              (str): text with translated percent
                     if None, no percent translation rule is matched
        """

        if self.srcLang == 'eng':
            pattern = r'(?P<percent>(?P<number>[,\.\d]*\d)(?P<symbol>\s*%))'
        elif self.srcLang == 'fra':
            pattern = r'(?P<percent>(?P<number>[,\xa0\d]*\d)(?P<symbol>\s*%))'
        else:
            raise NotImplementedError('Language %s is not supported' % self.srcLang)

        if self._fullmatch:
            pattern = r'(?P<percent>' + r'^' + pattern[len(r'(?P<percent>'):len(pattern) - 1] + r'$)'

        pr = re.compile(pattern)

        res = None

        try:
            if pr.search(text):
                res = pr.sub(lambda m: self.convert(m.group('percent')), text)
        except:
            pass

        return res


class CurrencyTranslator:
    """Rule-based currency translation
    """

    def __init__(self, curFormat, curCode, sourceLang, targetLang, sourceLocale, targetLocale, fullmatch=False):
        """Initialize a CurrencyTranslator instance

           Args:
              curFormat (str): currency symbol format
                              'symbol' (symbol-only, e.g., '$') or 'standard' (the one used by babel, e.g., '$US')
              curCode (str): currency code, e.g., 'USD'
              sourceLang (str): source language in full spelling, e.g., 'English'
                                ignored if sourceLocale is provided
              sourceLocale (str): source locale identifier
              targetLang (str): target language in full spelling, e.g., 'French'
                                ignored if targetLocale is provided
              targetLocale (str): target locale identifier
              fullmatch (bool): whether to full-match a text or not
                                if True, CurrencyTranslator can act as an independent translator
                                if False, CurrencyTranslator must work with other translators
        """

        assert curFormat in ('symbol', 'standard')

        self._curFormat = curFormat
        self.curCode = curCode
        self.srcLang = NAME_YAPPN_MAPPINGS[sourceLang]
        self.tgtLang = NAME_YAPPN_MAPPINGS[targetLang]
        self.srcLocale = sourceLocale if sourceLocale else re.sub('-', '_', CULTURE_CODES[sourceLang][0])
        self.tgtLocale = targetLocale if targetLocale else re.sub('-', '_', CULTURE_CODES[targetLang][0])
        self._fullmatch = fullmatch

        self.srcDecimalSymbol = numbers.get_decimal_symbol(self.srcLocale)

    def convert(self, text):
        """Convert currency according to the target locale

           Args:
              text (str): currency text
           Returns:
              (str): converted currency
        """

        cur = parse_price(re.sub('\s', ' ', text))

        if cur.amount and cur.currency:
            amountText, currency = cur.amount_text, cur.currency
            if self.srcDecimalSymbol in amountText:
                amount = float(cur.amount)
                res = format_currency(amount, self.curCode, locale=self.tgtLocale)
            else:
                amount = int(cur.amount)
                if self.tgtLang == 'eng':
                    res = format_currency(amount, self.curCode, format=u'¤#,##0', locale=self.tgtLocale,
                                          currency_digits=False)
                elif self.tgtLang == 'fra':
                    res = format_currency(amount, self.curCode, format=u'#,##0\xa0¤', locale=self.tgtLocale,
                                          currency_digits=False)
                else:
                    raise NotImplementedError('Target language %s is not supported' % (self.tgtLang,))

            if self._curFormat == 'symbol':
                tgtCurrencySymbol = numbers.get_currency_symbol(self.curCode, self.srcLocale)
                res = re.sub(re.escape(tgtCurrencySymbol) + r'\S+', tgtCurrencySymbol, res)
        else:
            res = None

        return res

    def translate(self, text):
        """Translate text with currency expression

           Args:
              text (str): text including currency expression
           Returns:
              (str): text with translated currency
                     if None, no currency translation rule is matched
        """

        currency_code_pattern = '(' + self.curCode + '|' + self.curCode[:-1] + ')'

        if self.srcLang == 'eng':
            # pattern = r'(?P<currency>((?P<currency_code>[A-Z]*(\xa0)?)\$)(?P<blank>\s*)(?P<currency_integer>\d+(,\d{3})*)(?P<currency_decimal>\.\d+)?)'
            pattern = r'(?P<currency>((?P<currency_code>' + currency_code_pattern + r'*(\xa0)?)\$)(?P<blank>\s*)(?P<currency_integer>\d+(,\d{3})*)(?P<currency_decimal>\.\d+)?)'
        elif self.srcLang == 'fra':
            # pattern = r'(?P<currency>(?P<currency_integer>\d+(\xa0\d{3})*)(?P<currency_decimal>,\d+)?(?P<blank>\s*)(\$(?P<currency_code>(\xa0)?[A-Z]*)))'
            pattern = r'(?P<currency>(?P<currency_integer>\d+(\xa0\d{3})*)(?P<currency_decimal>,\d+)?(?P<blank>\s*)(\$(?P<currency_code>(\xa0)?' + currency_code_pattern + r'*)))'
        else:
            raise NotImplementedError('Language %s is not supported' % self.srcLang)

        if self._fullmatch:
            pattern = r'(?P<currency>' + r'^' + pattern[len(r'(?P<currency>'):len(pattern) - 1] + r'$)'

        pr = re.compile(pattern)

        res = None

        try:
            if pr.search(text):
                res = pr.sub(lambda m: self.convert(m.group('currency')), text)
        except:
            pass

        return res


class TemplateTranslator:
    """Template-based translation using regex
    """

    def __init__(self, templates, sourceLang, targetLang):
        """Initialize a TemplateTranslator instance

           Args:
              templates (list): a list of (source_lang, target_lang, source_regex, target_regex) tuples
              sourceLang (str): source language in full spelling, e.g., 'English'
              targetLang (str): target language in full spelling, e.g., 'French'
        """

        self.srcLang = NAME_YAPPN_MAPPINGS[sourceLang]
        self.tgtLang = NAME_YAPPN_MAPPINGS[targetLang]
        self._mappings = {srcRegex: tgtRegex for (srcLang, tgtLang, srcRegex, tgtRegex)
                          in templates if srcLang == self.srcLang and tgtLang == self.tgtLang}

    def translate(self, text):
        """Translate a text according to the rules

           Args:
              text (str): input text
           Returns:
              (str): the translated text
                     if None, no template translation rule is matched
        """

        res = None

        for srcRegex in self._mappings:
            sr = re.compile(srcRegex)
            if sr.search(text):
                res = sr.sub(self._mappings[srcRegex], text)
                break

        return res


class Assembler:
    """Assemble piece translations to produce the final result
    """

    def __init__(self, translators):
        """Initialize an Assembler instance

           Args:
              translators (list): a list of translators (dict) with configurations to be applied in sequence
                                  Available translators are 'datetime', 'template'
                                  E.g. {'name':'template', 'templates': ..., 'sourceLang': ..., 'targetLang': ...}
                                       {'name':'datetime', 'format': ..., 'sourceLang': ..., 'targetLocale': ..., 'scope': ...}
                                       {'name':'currency', 'format': ..., 'code': ..., 'sourceLang': ..., 'targetLocale': ...}
        """

        assert all([translator['name'] in ('datetime', 'currency', 'template', 'number', 'percent') for translator in
                    translators])

        self._translators = translators

    def assemble(self, text):
        """Assemble translations

           Args:
              text (str): input text
           Returns:
              (str): the translated and assembled text
                     if None, no rule-based translation is applied
        """

        srcText = text
        tgtText = None

        for translator in self._translators:
            if translator['name'] == 'template':
                trans = TemplateTranslator(translator['templates'], translator['sourceLang'], translator['targetLang'])
            elif translator['name'] == 'datetime':
                trans = DatetimeTranslator(translator['format'], translator['sourceLang'],
                                           translator['targetLang'], translator['targetLocale'],
                                           translator['scope'], translator['fullmatch'])
            elif translator['name'] == 'currency':
                trans = CurrencyTranslator(translator['format'], translator['scope'],
                                           translator['sourceLang'], translator['targetLang'],
                                           translator['sourceLocale'], translator['targetLocale'],
                                           translator['fullmatch'])
            elif translator['name'] == 'number':
                trans = NumberTranslator(translator['sourceLang'], translator['targetLang'],
                                         translator['sourceLocale'], translator['targetLocale'],
                                         translator['fullmatch'])
            elif translator['name'] == 'percent':
                trans = PercentTranslator(translator['sourceLang'], translator['targetLang'],
                                          translator['sourceLocale'], translator['targetLocale'],
                                          translator['fullmatch'])
            else:
                raise NotImplementedError('Translator %s is not implemented' % translator['name'])

            srcText = trans.translate(srcText)

            if srcText is not None:
                tgtText = srcText
            else:
                break

        return tgtText
