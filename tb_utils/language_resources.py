# -*- coding: utf-8 -*-

# utils: language resources
#
# Author: Renxian Zhang 
# --------------------------------------------------
# This modules provides language constants as resources for convenient calling.

import regex as re
from expynent import patterns as expy_patterns
from common_regex import CommonRegex as cr_patterns
# pip install iso-3166-1
from iso3166 import Country
import ftfy

class Codes:
    """Language and culture codes
    """
    
    LANGUAGE_CODES = {'Afrikaans': {'yappn': 'afr', 'google': 'af', 'microsoft': 'af', 'iso-639-1': 'af'}, 
                      'Albanian': {'yappn': 'sqi', 'google': 'sq', 'microsoft': None, 'iso-639-1': 'sq'}, 
                      'Amharic': {'yappn': 'amh', 'google': 'am', 'microsoft': None, 'iso-639-1': 'am'}, 
                      'Arabic': {'yappn': 'ara', 'google': 'ar', 'microsoft': 'ar', 'iso-639-1': 'ar'},    
                      'Armenian': {'yappn': 'arm', 'google': 'hy', 'microsoft': None, 'iso-639-1': 'hy'}, 
                      'Azeerbaijani': {'yappn': 'aze', 'google': 'az', 'microsoft': None, 'iso-639-1': 'az'}, 
                      'Basque': {'yappn': 'bas', 'google': 'eu', 'microsoft': None, 'iso-639-1': 'eu'}, 
                      'Belarusian': {'yappn': 'bel', 'google': 'be', 'microsoft': None, 'iso-639-1': 'be'}, 
                      'Bengali': {'yappn': 'ben', 'google': 'bn', 'microsoft': None, 'iso-639-1': 'bn'}, 
                      'Bosnian': {'yappn': 'bos', 'google': 'bs', 'microsoft': 'bs', 'iso-639-1': 'bs'}, 
                      'Bulgarian': {'yappn': 'bul', 'google': 'bg', 'microsoft': 'bg', 'iso-639-1': 'bg'}, 
                      'Cantonese': {'yappn': 'yue', 'google': None, 'microsoft': 'yue', 'iso-639-1': None}, 
                      'Catalan': {'yappn': 'cat', 'google': 'ca', 'microsoft': 'ca', 'iso-639-1': 'ca'}, 
                      'Cebuano': {'yappn': 'ceb', 'google': 'ceb', 'microsoft': None, 'iso-639-1': None}, 
                      'Chichewa': {'yappn': 'nya', 'google': 'ny', 'microsoft': None, 'iso-639-1': 'ny'}, 
                      'Chinese': {'yappn': 'zhh', 'google': 'zh-CN', 'microsoft': 'zh-Hans', 'iso-639-1': 'zh'}, 
                      'Chinese Simplified': {'yappn': 'zhs', 'google': 'zh-CN', 'microsoft': 'zh-Hans', 'iso-639-1': 'zh'}, 
                      'Chinese Traditional': {'yappn': 'zht', 'google': 'zh-TW', 'microsoft': 'zh-Hant', 'iso-639-1': 'zh'},
                      'Chinese Taiwanese': {'yappn': 'ypt', 'google': None, 'microsoft': None, 'iso-639-1': None},
                      'Corsican': {'yappn': 'cos', 'google': 'co', 'microsoft': None, 'iso-639-1': 'co'},
                      'Croatian': {'yappn': 'hrv', 'google': 'hr', 'microsoft': 'hr', 'iso-639-1': 'hr'},
                      'Czech': {'yappn': 'ces', 'google': 'cs', 'microsoft': 'cs', 'iso-639-1': 'cs'},
                      'Danish': {'yappn': 'dan', 'google': 'da', 'microsoft': 'da', 'iso-639-1': 'da'},
                      'Dutch': {'yappn': 'nld', 'google': 'nl', 'microsoft': 'nl', 'iso-639-1': 'nl'}, 
                      'English': {'yappn': 'eng', 'google': 'en', 'microsoft': 'en', 'iso-639-1': 'en'},
                      'Esperanto': {'yappn': 'epo', 'google': 'eo', 'microsoft': None, 'iso-639-1': 'eo'},
                      'Estonian': {'yappn': 'est', 'google': 'et', 'microsoft': 'et', 'iso-639-1': 'et'},
                      'Fijian': {'yappn': 'fij', 'google': None, 'microsoft': 'fj', 'iso-639-1': 'fj'},
                      'Filipino': {'yappn': 'fil', 'google': None, 'microsoft': 'fil', 'iso-639-1': 'fl'},
                      'Finnish': {'yappn': 'fin', 'google': 'fi', 'microsoft': 'fi', 'iso-639-1': 'fi'},                      
                      'French': {'yappn': 'fra', 'google': 'fr', 'microsoft': 'fr', 'iso-639-1': 'fr'}, 
                      'Frisian': {'yappn': 'fry', 'google': 'fy', 'microsoft': None, 'iso-639-1': 'fy'}, 
                      'Galician': {'yappn': 'glg', 'google': 'gl', 'microsoft': None, 'iso-639-1': 'gl'}, 
                      'Georgian': {'yappn': 'geo', 'google': 'ka', 'microsoft': None, 'iso-639-1': 'ka'}, 
                      'German': {'yappn': 'deu', 'google': 'de', 'microsoft': 'de', 'iso-639-1': 'de'}, 
                      'Greek': {'yappn': 'ell', 'google': 'el', 'microsoft': 'el', 'iso-639-1': 'el'},
                      'Gujarati': {'yappn': 'guj', 'google': 'gu', 'microsoft': None, 'iso-639-1': 'gu'},
                      'Haitian Creole': {'yappn': 'htc', 'google': 'ht', 'microsoft': 'ht', 'iso-639-1': 'ht'},
                      'Hausa': {'yappn': 'hau', 'google': 'ha', 'microsoft': None, 'iso-639-1': 'ha'},
                      'Hawaiian': {'yappn': 'haw', 'google': 'haw', 'microsoft': None, 'iso-639-1': None},
                      'Hebrew': {'yappn': 'heb', 'google': 'iw', 'microsoft': 'he', 'iso-639-1': 'he'},
                      'Hindi': {'yappn': 'hin', 'google': 'hi', 'microsoft': 'hi', 'iso-639-1': 'hi'},
                      'Hmong': {'yappn': 'hmn', 'google': 'hmn', 'microsoft': None, 'iso-639-1': None},
                      'Hmong Daw': {'yappn': 'mww', 'google': None, 'microsoft': 'mww', 'iso-639-1': None},
                      'Hungarian': {'yappn': 'hun', 'google': 'hu', 'microsoft': 'hu', 'iso-639-1': 'hu'},
                      'Icelandic': {'yappn': 'isl', 'google': 'is', 'microsoft': None, 'iso-639-1': 'is'},
                      'Igbo': {'yappn': 'ibo', 'google': 'ig', 'microsoft': None, 'iso-639-1': 'ig'},
                      'Indonesian': {'yappn': 'ind', 'google': 'id', 'microsoft': 'id', 'iso-639-1': 'id'}, 
                      'Irish': {'yappn': 'gle', 'google': 'ga', 'microsoft': None, 'iso-639-1': 'ga'},                       
                      'Italian': {'yappn': 'ita', 'google': 'it', 'microsoft': 'it', 'iso-639-1': 'it'}, 
                      'Japanese': {'yappn': 'jpn', 'google': 'ja', 'microsoft': 'ja', 'iso-639-1': 'ja'},
                      'Javanese': {'yappn': 'jav', 'google': 'jw', 'microsoft': None, 'iso-639-1': 'jv'},
                      'Kannada': {'yappn': 'kan', 'google': 'kn', 'microsoft': None, 'iso-639-1': 'kn'},
                      'Kazakh': {'yappn': 'kaz', 'google': 'kk', 'microsoft': None, 'iso-639-1': 'kk'},
                      'Khmer': {'yappn': 'khm', 'google': 'km', 'microsoft': None, 'iso-639-1': 'km'},                                            
                      'Korean': {'yappn': 'kor', 'google': 'ko', 'microsoft': 'ko', 'iso-639-1': 'ko'},
                      'Kurdish': {'yappn': 'kur', 'google': 'ku', 'microsoft': None, 'iso-639-1': 'ku'},
                      'Kyrgyz': {'yappn': 'kir', 'google': 'ky', 'microsoft': None, 'iso-639-1': 'ky'},
                      'Lao': {'yappn': 'lao', 'google': 'lo', 'microsoft': None, 'iso-639-1': 'lo'},
                      'Latin': {'yappn': 'lat', 'google': 'la', 'microsoft': None, 'iso-639-1': 'la'},
                      'Latvian': {'yappn': 'lav', 'google': 'lv', 'microsoft': 'lv', 'iso-639-1': 'lv'},
                      'Lithuanian': {'yappn': 'lit', 'google': 'lt', 'microsoft': 'lt', 'iso-639-1': 'lt'},
                      'Luxembourgish': {'yappn': 'ltz', 'google': 'lb', 'microsoft': None, 'iso-639-1': 'lb'},
                      'Macedonian': {'yappn': 'mkd', 'google': 'mk', 'microsoft': None, 'iso-639-1': 'mk'},
                      'Malagasy': {'yappn': 'mlg', 'google': 'mg', 'microsoft': 'mg', 'iso-639-1': 'mg'},
                      'Malay': {'yappn': 'msa', 'google': 'ms', 'microsoft': 'ms', 'iso-639-1': 'ms'}, 
                      'Malayalam': {'yappn': 'mal', 'google': 'ml', 'microsoft': None, 'iso-639-1': 'ml'}, 
                      'Maltese': {'yappn': 'mlt', 'google': 'mt', 'microsoft': 'mt', 'iso-639-1': 'mt'}, 
                      'Maori': {'yappn': 'mri', 'google': 'mi', 'microsoft': None, 'iso-639-1': 'mi'}, 
                      'Marathi': {'yappn': 'mar', 'google': 'mr', 'microsoft': None, 'iso-639-1': 'mr'}, 
                      'Mongolian': {'yappn': 'mon', 'google': 'mn', 'microsoft': None, 'iso-639-1': 'mn'}, 
                      'Myanmar': {'yappn': 'mya', 'google': 'my', 'microsoft': None, 'iso-639-1': 'my'}, 
                      'Nepali': {'yappn': 'nep', 'google': 'ne', 'microsoft': None, 'iso-639-1': 'ne'}, 
                      'Norwegian': {'yappn': 'nor', 'google': 'no', 'microsoft': 'no', 'iso-639-1': 'no'}, 
                      'Pashto': {'yappn': 'pus', 'google': 'ps', 'microsoft': None, 'iso-639-1': 'ps'}, 
                      'Persian': {'yappn': 'fas', 'google': 'fa', 'microsoft': 'fa', 'iso-639-1': 'fa'}, 
                      'Polish': {'yappn': 'pol', 'google': 'pl', 'microsoft': 'pl', 'iso-639-1': 'pl'}, 
                      'Portuguese': {'yappn': 'por', 'google': 'pt', 'microsoft': 'pt', 'iso-639-1': 'pt'}, 
                      'Punjabi': {'yappn': 'pan', 'google': 'pa', 'microsoft': None, 'iso-639-1': 'pa'}, 
                      'Romanian': {'yappn': 'ron', 'google': 'ro', 'microsoft': 'ro', 'iso-639-1': 'ro'},    
                      'Russian': {'yappn': 'rus', 'google': 'ru', 'microsoft': 'ru', 'iso-639-1': 'ru'},    
                      'Samoan': {'yappn': 'smo', 'google': 'sm', 'microsoft': 'sm', 'iso-639-1': 'sm'},
                      'Scots Gaelic': {'yappn': 'gla', 'google': 'gd', 'microsoft': None, 'iso-639-1': 'gd'},
                      'Serbian': {'yappn': 'srp', 'google': 'sr', 'microsoft': 'sr-Cyrl', 'iso-639-1': 'sr'}, 
                      'Sesotho': {'yappn': 'sot', 'google': 'st', 'microsoft': None, 'iso-639-1': 'st'},
                      'Shona': {'yappn': 'sna', 'google': 'sn', 'microsoft': None, 'iso-639-1': 'sn'},
                      'Sindhi': {'yappn': 'snd', 'google': 'sd', 'microsoft': None, 'iso-639-1': 'sd'},
                      'Sinhala': {'yappn': 'sin', 'google': 'si', 'microsoft': None, 'iso-639-1': 'si'},
                      'Slovak': {'yappn': 'slk', 'google': 'sk', 'microsoft': 'sk', 'iso-639-1': 'sk'},
                      'Slovenian': {'yappn': 'slv', 'google': 'sl', 'microsoft': 'sl', 'iso-639-1': 'sl'},
                      'Somali': {'yappn': 'som', 'google': 'so', 'microsoft': None, 'iso-639-1': 'so'},
                      'Spanish': {'yappn': 'spa', 'google': 'es', 'microsoft': 'es', 'iso-639-1': 'es'}, 
                      'Sundanese': {'yappn': 'sun', 'google': 'su', 'microsoft': None, 'iso-639-1': 'su'}, 
                      'Swahili': {'yappn': 'swa', 'google': 'sw', 'microsoft': None, 'iso-639-1': 'sw'}, 
                      'Swedish': {'yappn': 'swe', 'google': 'sv', 'microsoft': 'sv', 'iso-639-1': 'sv'}, 
                      'Tahitian': {'yappn': 'tah', 'google': None, 'microsoft': 'ty', 'iso-639-1': 'ty'}, 
                      'Tajik': {'yappn': 'tgk', 'google': 'tg', 'microsoft': None, 'iso-639-1': 'tg'},
                      'Tamil': {'yappn': 'tam', 'google': 'ta', 'microsoft': 'ta', 'iso-639-1': 'ta'},
                      'Telugu': {'yappn': 'tel', 'google': 'te', 'microsoft': None, 'iso-639-1': 'te'},                      
                      'Thai': {'yappn': 'tha', 'google': 'th', 'microsoft': 'th', 'iso-639-1': 'th'},    
                      'Tongan': {'yappn': 'ton', 'google': None, 'microsoft': 'to', 'iso-639-1': 'to'}, 
                      'Turkish': {'yappn': 'tur', 'google': 'tr', 'microsoft': 'tr', 'iso-639-1': 'tr'},  
                      'Ukrainian': {'yappn': 'ukr', 'google': 'uk', 'microsoft': 'uk', 'iso-639-1': 'uk'}, 
                      'Urdu': {'yappn': 'urd', 'google': 'ur', 'microsoft': 'ur', 'iso-639-1': 'ur'}, 
                      'Uzbek': {'yappn': 'uzb', 'google': 'uz', 'microsoft': None, 'iso-639-1': 'uz'}, 
                      'Vietnamese': {'yappn': 'vie', 'google': 'vi', 'microsoft': 'vi', 'iso-639-1': 'vi'}, 
                      'Welsh': {'yappn': 'cym', 'google': 'cy', 'microsoft': 'cy', 'iso-639-1': 'cy'}, 
                      'Xhosa': {'yappn': 'xho', 'google': 'xh', 'microsoft': None, 'iso-639-1': 'xh'}, 
                      'Yiddish': {'yappn': 'yid', 'google': 'yi', 'microsoft': None, 'iso-639-1': 'yi'}, 
                      'Yoruba': {'yappn': 'yor', 'google': 'yo', 'microsoft': None, 'iso-639-1': 'yo'}, 
                      'Zulu': {'yappn': 'zul', 'google': 'zu', 'microsoft': None, 'iso-639-1': 'zu'} 
                      }
            
    CULTURE_CODES = {'Afrikaans': ('af', 'af-ZA'), 
                     'Albanian': ('sq', 'sq-AL'), 
                     'Arabic': ('ar', 'ar-DZ', 'ar-BH', 'ar-EG', 'ar-IQ', 'ar-JO', 'ar-KW', 'ar-LB', 'ar-LY', 'ar-MA', 'ar-OM', 'ar-QA', 'ar-SA', 'ar-SY', 'ar-TN', 'ar-AE', 'ar-YE'), 
                     'Armenian': ('hy', 'hy-AM'), 
                     'Azerbaijani': ('az', 'az-AZ-Cyrl', 'az-AZ-Latn'), 
                     'Basque': ('eu', 'eu-ES'), 
                     'Belarusian': ('be', 'be-BY'), 
                     'Bulgarian': ('bg', 'bg-BG'), 
                     'Catalan': ('ca', 'ca-ES'), 
                     'Chinese Simplified':('zh-CN', 'zh-CHS'), 
                     'Chinese Traditional': ('zh-HK', 'zh-MO', 'zh-SG', 'zh-TW', 'zh-CHT'), 
                     'Chinese Taiwanese': ('zh-TW', 'zh-CHT'), 
                     'Croatian': ('hr', 'hr-HR'), 
                     'Czech': ('cs', 'cs-CZ'), 
                     'Danish': ('da', 'da-DK'), 
                     'Dutch': ('nl', 'nl-BE', 'nl-NL'),
                     'English': ('en-US', 'en', 'en-AU', 'en-BZ', 'en-CA', 'en-CB', 'en-IE', 'en-JM', 'en-NZ', 'en-PH', 'en-ZA', 'en-TT', 'en-GB', 'en-ZW'),
                     'Estonian': ('et', 'et-EE'), 
                     'Finnish': ('fi', 'fi-FI'), 
                     'French': ('fr-CA', 'fr', 'fr-FR', 'fr-BE', 'fr-LU', 'fr-MC', 'fr-CH'), 
                     'Galician': ('gl', 'gl-ES'), 
                     'Georgian': ('ka', 'ka-GE'), 
                     'German': ('de', 'de-AT', 'de-DE', 'de-LI', 'de-LU', 'de-CH'), 
                     'Greek': ('el', 'el-GR'), 
                     'Gujarati': ('gu', 'gu-IN'), 
                     'Hebrew': ('he', 'he-IL'), 
                     'Hindi': ('hi', 'hi-IN'), 
                     'Hungarian': ('hu', 'hu-HU'), 
                     'Icelandic': ('is', 'is-IS'), 
                     'Indonesian': ('id', 'id-ID'), 
                     'Italian': ('it', 'it-IT', 'it-CH'), 
                     'Japanese': ('ja', 'ja-JP'), 
                     'Kannada': ('kn', 'kn-IN'), 
                     'Kazakh':('kk', 'kk-KZ'), 
                     'Korean': ('ko', 'ko-KR'), 
                     'Kyrgyz': ('ky', 'ky-KG'), 
                     'Latvian': ('lv', 'lv-LV'), 
                     'Lithuanian': ('lt', 'lt-LT'), 
                     'Macedonian': ('mk', 'mk-MK'), 
                     'Malay': ('ms', 'ms-BN', 'ms-MY'), 
                     'Marathi': ('mr', 'mr-IN'), 
                     'Mongolian': ('mn', 'mn-MN'), 
                     'Norwegian': ('no', 'nb-NO', 'nn-NO'),                      
                     'Persian': ('fa', 'fa-IR'), 
                     'Polish': ('pl', 'pl-PL'), 
                     'Portuguese': ('pt', 'pt-BR', 'pt-PT'), 
                     'Punjabi': ('pa', 'pa-IN'), 
                     'Romanian': ('ro', 'ro-RO'), 
                     'Russian': ('ru', 'ru-RU'), 
                     'Serbian': ('sr-SP-Cyrl', 'sr-SP-Latn'), 
                     'Slovak': ('sk', 'sk-SK'), 
                     'Slovenian': ('sl', 'sl-SI'), 
                     'Spanish': ('es', 'es-AR', 'es-BO', 'es-CL', 'es-CO', 'es-CR', 'es-DO', 'es-EC', 'es-SV', 'es-GT', 'es-HN', 'es-MX', 'es-NI', 'es-PA', 'es-PY', 'es-PE', 'es-PR', 'es-ES', 'es-UY', 'es-VE'), 
                     'Swahili': ('sw', 'sw-KE'), 
                     'Swedish': ('sv', 'sv-FI', 'sv-SE'), 
                     'Tamil': ('ta', 'ta-IN'), 
                     'Telugu': ('te', 'te-IN'), 
                     'Thai': ('th', 'th-TH'), 
                     'Turkish': ('tr', 'tr-TR'), 
                     'Ukrainian': ('uk', 'uk-UA'), 
                     'Urdu': ('ur', 'ur-PK'), 
                     'Uzbek': ('uz', 'uz-UZ-Cyrl', 'uz-UZ-Latn'), 
                     'Vietnamese': ('vi',)
                     }   
    
    COUNTRY_CODES = {ftfy.fix_text(Country._member_map_[country].english_short_name): {'alpha2': Country[country].alpha2, 
                                                                                       'alpha3': Country[country].alpha3, 
                                                                                       'numeric': Country[country].numeric}                    
                     for country in Country._member_map_}
    
    @classmethod   
    def mappings(self, mappingFrom, mappingTo):
        """For covenient conversions between language codes
    
           Args:        
               mappingFrom (str): 'name', 'yappn', 'google', 'microsoft', or 'iso-639-1'
               mappingTo (str): 'name', 'yappn', 'google', 'microsoft', or 'iso-639-1'
    
           Returns:
               (dict): Mappings from one code system to the other   
        """        
    
        lc = {language: {'name': language, 
                         'yappn': self.LANGUAGE_CODES[language]['yappn'], 
                         'google': self.LANGUAGE_CODES[language]['google'], 
                         'microsoft': self.LANGUAGE_CODES[language]['microsoft'], 
                         'iso-639-1': self.LANGUAGE_CODES[language]['iso-639-1']} 
              for language in self.LANGUAGE_CODES}
        
        res = {lc[lang][mappingFrom]: lc[lang][mappingTo] for lang in lc if lc[lang][mappingFrom]}
    
        return res   
    
       
class CommonRegex:
    """Common regular expressions
    """    
    
    # Language-insensitive
    
    # Markups    
    INLINE_MARKUP_PATTERNs = [r'^(?P<pre_text>.*?)[<\{\[\(](?P<mark>\w+)[>\}\]\)](?P<text>.*)[<\{\[\(](?P=mark)[>\}\]\)](?P<post_text>.*)$', 
                              r'^(?P<pre_text>.*?)(?P<mark>\w+)[>\}\]\)](?P<text>.*)[<\{\[\(].*(?P=mark)(?P<post_text>.*)$']
            
    # For Windows
    FILENAME_PATTERN = (r'''(?P<file_path>^(?:[\w]\:\\|\\)([a-zA-Z_\-\s0-9\.()~!@#$%^&=+\';,{}\[\]]+)(\\[a-zA-Z_\-\s0-9\.()~!@#$%^&=+\';,{}\[\]]+)*\.'''
                        r'''(?i)(xhtml|html|docx|pptx|tiff|xlsx|indd|aspx|htm|pdf|doc|log|msg|odt|rtf|tex|txt|wpd|wps|csv|dat|pps|ppt|tar|vcf|xml|aif|m3u|m4a|mid|mp3|mpa|wav|wma|'''
                        r'''3gp|asf|avi|flv|m4v|mov|mp4|mpg|rm|srt|swf|vob|wmv|bmp|gif|jpg|png|psd|tif|eps|svg|xlr|xls|mdb|sql|apk|app|bat|cgi|com|'''
                        r'''exe|jar|wsf|asp|css|dcr|jsp|php|rss|dll|ico|lnk|sys|cfg|ini|pkg|rar|zip|bin|bak|tmp|ps|db|js|7g|gz))$'''
                        )
           
    URL_PATTERN = (r'''(?i)(?P<url>^(?:(http|https|ftp|mailto|about|data|file|irc|dns|geo|gopher|imap|pop|rtsp|sms|telnet|tv|mms):(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)'''  
                   r'''(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])$)'''
                   ) 
        
    DIGIT_PATTERN = r'(?P<digit>[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?)([^\d\.]|$)'
    
    PERCENTAGE_PATTERN = r'(?P<percentage>((?:\d+(?:\.\d+)?\-)?(?:\d+(?:\.\d+)?))[%٪％])'

    TP_timeExp = r'(?:((1[0-2]|0?[1-9])(:([0-5]?[0-9])){1,2}(\s?[AP]M))|((2[0-3]|[01]?[0-9])(:([0-5]?[0-9])){1,2}))'
    TP_timeRange = r'(?:' + TP_timeExp + r'(?:(?:\s*-\s*' + TP_timeExp + r')*))'          
    TP_timeRangeSelection = r'(?:' + TP_timeRange + r'(?:(?:\s*/\s*' + TP_timeRange + r')*))'
    TIME_PATTERN = r'(?i)(?P<time>' + TP_timeRangeSelection + ')'   
       
    PHONENUMBER_PATTERN = r'(?P<phonenumber>(?<![^\W_])(?:(?:\(?(?:00|\+)(?:[1-4]\d\d|[1-9]\d?)\)?)?[\-\.\\\/]?)?((?:\(?\d{3,}\)?[\-\.\ \\\/]?){2,})(?:[\-\.\ \\\/]?(?:#|ext\.?|extension|x)[\-\.\ \\\/]?(?:\d+))?(?![^\W_]))'       
    
    CODE_PATTERN = r'(?P<code>^[0-9A-Za-z]+(?:(?:[_\\\/-][0-9A-Za-z]+)+)$)'
    
    SCRIPT_PATTERN = r'(?ms)(?P<script>^(<!--.+-->)$)'
    
    #SOCIAL_PATTERN = r'(?i)(?P<social>([^@\s]+(@| +at +)[^@\s]+((\.| +dot +)[^@\s]+)?)|((?<![^\s])#[^#\s]+))'
    SOCIAL_PATTERN = r'(?i)(?P<social>([^@\s]+(@)[^@\s]+((\.)[^@\s]+)?)|((?<![^\s])#[^#\s]+))'

    SIZE_PATTERN = r'((?<![^\W_])(?P<size>(?:\dX|X*)[SL]|M))(?![^\W_])'            
        
    # Locale-sensitive
    
    CP_number = r'(?:[-+±]?(?:[.]?\d+(?:,\d\d\d)*(?:[\.]\d*)?))'
    CP_numberRange = r'(?:' + CP_number + r'(?:(?:\s*-\s*' + CP_number + r')*))'
    CURRENCY_UNITS_Arabic = {'symbols': (u'دج', u'.د.ب', u'E£', u'د.ع', u'د.ك', u'ل.د', u'د.م.', u'ر.ع.', u'ر.ق', u'ر.س', u'د.ت', u'د.إ'), 
                             'codes': ('DA', 'BD', 'JD', 'K.D.', 'LL', 'LD', 'DH', 'Dhs', 'QR', 'SR', 'LS', 'DT')}
    CURRENCY_UNITS_Chinese_Simplified = {'symbols': ('¥',), 
                                         'codes': ('CNY',)}
    CURRENCY_UNITS_Chinese_Traditional = {'symbols': ('¥', '$', 'HK$', 'NT$', 'MOP$', 'S$'), 
                                          'codes': ('CNY', 'HKD', 'TWD', 'MOP', 'SGD')} 
    CURRENCY_UNITS_English = {'symbols': ('$', '£', '€'), 
                              'codes': ('AUD', 'CAD', 'EUR', 'HKD', 'SGD', 'USD', 'GBP')}
    CURRENCY_UNITS_French = {'symbols': ('$', '£', '€'), 
                             'codes': ('AUD', 'CAD', 'EUR', 'HKD', 'SGD', 'USD', 'GBP')}
    CURRENCY_UNITS_German = {'symbols': ('$', '£', '€'), 
                              'codes': ('AUD', 'CAD', 'EUR', 'HKD', 'SGD', 'USD', 'GBP')}
    CURRENCY_UNITS_Japanese = {'symbols': ('¥',), 
                               'codes': ('JPY',)}
    CURRENCY_UNITS_Spanish = {'symbols': ('$', '£', '€'), 
                              'codes': ('AUD', 'CAD', 'EUR', 'HKD', 'SGD', 'USD', 'GBP')}
    CURRENCY_UNITS = {'ara': CURRENCY_UNITS_Arabic,
                      'deu': CURRENCY_UNITS_German, 
                      'eng': CURRENCY_UNITS_English, 
                      'fra': CURRENCY_UNITS_French, 
                      'jpn': CURRENCY_UNITS_Japanese, 
                      'spa': CURRENCY_UNITS_Spanish, 
                      'zhs': CURRENCY_UNITS_Chinese_Simplified, 
                      'zht': CURRENCY_UNITS_Chinese_Traditional}
    CURRENCY_PATTERN = {}
    for lang in CURRENCY_UNITS:
        expanded_symbols = [re.escape(s) if s[0].isalpha() else r'(?:[A-Z]{2})?' + re.escape(s) for s in CURRENCY_UNITS[lang]['symbols']]
        CP_unit = r'(?:(?:(?<![^\W\d_])(' + r'|'.join(CURRENCY_UNITS[lang]['codes'] + tuple(expanded_symbols)) + r')(?![^\W\d_])))'
        CP_currencyExp = r'(?:(?:' + CP_numberRange + r'(?:\s*' + CP_unit + r'))|(?:' + CP_unit + r'(?:\s*' + CP_numberRange + ')))'
        CP_currencySelection = r'(?:' + CP_currencyExp + r'(?:(?:\s*/\s*' + CP_currencyExp + r')*))'
        CURRENCY_PATTERN[lang] = r'(?P<currency>' + CP_currencySelection + ')'
        
    # Language-sensitive

    QP_number = r'(?:[-+±]?(?:(?:(?:\s*\d+\s*/\s*\d+)|(?:\s*[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞↉]))|[.]?\d+(?:,\d\d\d)*(?:(?:[\.]\d*)|(?:\s+\d+\s*/\s*\d+)|(?:\s*[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞↉]))?))'
    QP_numberRange = r'(?:' + QP_number + r'(?:(?:\s*-\s*' + QP_number + r')*))'
    UNITS_Arabic = {'length': (u'اميال', u'ميل', u'بوصة', u'ياردة', u'أقدام', u'قدم', 'mi', 'kms', 'km', 'm', 'cm', 'mm', 'in', 'yd', 'ft', "'", '"', '’', '”'), 
                    'volume': (u'أكواب', u'كوب', 'c', u'باينت', 'pt', u'ربع جالون', u'ربع غالون', 'qt', u'غالون', 'gal', u'لتر', 'l'), 
                    'mass': (u'طن', u'كيلوغرام', 'kg', u'غرام', 'g', u'مليغرام', 'mg', u'جنيه', 'lb', u'أوقية', 'oz'), 
                    'temperature': ('°C', '°F', 'k'), 
                    'energy': (u'جول وحدة طاقة', 'j', u'كيلو جول', 'kj', 'kWh', u'سعرات حراريه', 'cal', u'السعرات الحرارية', 'kcal'), 
                    'area': (u'كيلومتر مربع', 'sq km', u'اميال مربعة', 'sq mi', u'متر مربع', 'sq m', u'سم مربع', 'sq cm', u'قدم مربع', 'sq, ft', 
                             u'ياردة مربعة', 'sq yd', u'بوصة مربعة', 'sq, in', u'هكتار', 'ha', u'هكتار', 'ac'), 
                    'speed': (u'سم / ث', u'متر / ث', u'كم / ساعة', u'ميل في الساعة', u'عقد', u'قدم / ث'), 
                    'time': (u'سنوات', u'عام', 'yr', u'أسابيع', u'أسبوع', 'w', u'أيام', u'يوم', 'd', u'ساعات', u'ساعة', 'h', u'دقائق', u'دقيقة', 'mins', 'min', u'ثواني', u'ثانية', 's', u'ميلي ثانية', u'ميلي ثانية واحدة', 'ms'), 
                    'power': (u'وات', 'w', u'كيلووات', 'kw', u'ميغاواط', 'mw'), 
                    'voltage': (u'كيلو فولت', 'kv', u'ميليفولت', 'mv', u'فولت', 'Vrms', 'Vpp', 'v'), 
                    'current': (u'أمبير', 'amp', 'A', 'mA', 'μA'),
                    'resistance': (u'كيلو اوم', 'kΩ', u'الاوم', u'أوم', 'Ω'), 
                    'capacitance': (u'الفارادات', u'فاراد', 'F', u'مكروفاراد', 'μF', u'بيكوفاراد', 'pF'), 
                    'data': (u'بت', 'b', u'بايت', 'B', u'كيلو بايت', 'KB', u'ميغابايت', 'MB', u'جيجابايت', 'GB', u'تيرابايت', 'TB'), 
                    'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                    'pressure': (u'كيلوباسكال', 'kpa', u'باسكال', 'pa'),
                    'frequency': (u'ميغاهيرتز', u'كيلوهرتز', u'هرتز', 'rpm'), 
                    'sound': (u'ديسيبل', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                    } 
    UNITS_Chinese_Simplified = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', '英里', '英寸', 'in', '码', 'yd', '英尺', 'ft', "'", '"', '’', '”'), 
                                'volume': ('杯', 'c', '品脱', 'pt', '夸脱', 'qt', '加仑', 'gal', '升', 'l'), 
                                'mass': ('吨', '公斤', '千克', 'kg', '克', 'g', '毫克', 'mg', '磅', 'lb', '盎司', 'oz'), 
                                'temperature': ('°C', '°F', 'k'), 
                                'energy': ('焦耳', 'j', '千焦', 'kj', '千瓦时', '卡路里', 'cal', '千卡', 'kcal'), 
                                'area': ('平方公里', '平方千米', 'sq km', '平方英里', 'sq mi', '平方米', 'sq m', '平方厘米', 'sq cm', '平方英尺', 'sq, ft', 
                                         '平方码', 'sq yd', '平方英寸', 'sq, in', '公顷', 'ha', '英亩', 'ac'), 
                                'speed': ('厘米/秒', '米/秒', '千米/小时', '英里每小时', '海里', '英尺/秒'), 
                                'time': ('年', 'yr', '周', '星期', 'w', '日', '天', 'd', '小时', 'h', '分', '分钟', 'mins', 'min', '秒', 's', '毫秒', 'ms'), 
                                'power': ('瓦', 'w', '千瓦', 'kw', '兆瓦', 'mw'), 
                                'voltage': ('千伏', 'kv', '毫伏', 'mv', '伏', '伏特', 'Vrms', 'Vpp', 'v'), 
                                'current': ('安培', 'amp', 'A', 'mA', 'μA'),
                                'resistance': ('千欧姆', 'kΩ', '欧姆', 'Ω'), 
                                'capacitance': ('法拉', 'F', '微法', 'μF', '皮法', 'pF'), 
                                'data': ('比特', 'b', '字节', 'B', '千字节', 'KB', '兆字节', 'MB', '千兆字节', 'GB', '万亿字节', 'TB'), 
                                'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                                'pressure': ('千帕', 'kpa', '帕', '帕斯卡', 'pa'),
                                'frequency': ('兆赫', '千赫', '赫兹', '赫', 'rpm'), 
                                'sound': ('分贝', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                         }
    UNITS_Chinese_Traditional = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', '英里', '吋', 'in', '碼', 'yd', '尺', 'ft', "'", '"', '’', '”'), 
                                 'volume': ('杯', 'c', '品脫', 'pt', '夸脫', 'qt', '加侖', 'gal', '升', 'l'), 
                                 'mass': ('噸', '公斤', 'kg', '克', 'g', '毫克', 'mg', '磅', 'lb', '安士', 'oz'), 
                                 'temperature': ('°C', '°F', 'k'), 
                                 'energy': ('焦耳', 'j', '熱量', 'kj', '千瓦時', '卡路里', 'cal', '千卡', 'kcal'), 
                                 'area': ('平方千米', 'sq km', '平方英里', 'sq mi', '平方米', 'sq m', '平方厘米', 'sq cm', '平方尺', 'sq, ft', 
                                          '平方碼', 'sq yd', '平方吋', 'sq, in', '公頃', 'ha', '英畝', 'ac'), 
                                 'speed': ('厘米/秒', '米/秒', '千米/小時', '英里每小時', '節', '尺/秒'), 
                                 'time': ('年', 'yr', '周', 'w', '天', 'd', '小時', 'h', '分鐘', 'mins', 'min', '秒', 's', '毫秒', 'ms'), 
                                 'power': ('瓦特', 'w', '千瓦', 'kw', '兆瓦', 'mw'), 
                                 'voltage': ('千伏特', 'kv', '毫伏', 'mv', '伏特', 'Vrms', 'Vpp', 'v'), 
                                 'current': ('安培', 'amp', 'A', 'mA', 'μA'),
                                 'resistance': ('千歐', 'kΩ', '歐姆', 'Ω'), 
                                 'capacitance': ('法拉', 'F', '微法', 'μF', '皮法', 'pF'), 
                                 'data': ('位', 'b', '位元組', 'B', '千位元組', 'KB', '百萬位元組', 'MB', '技嘉', 'GB', '兆兆位元組', 'TB'), 
                                 'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                                 'pressure': ('千帕', 'kpa', '帕斯卡', 'pa'),
                                 'frequency': ('兆赫', '千赫', '赫茲', 'rpm'), 
                                 'sound': ('分貝', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                                 }
    UNITS_English = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', 'miles', 'mile', 'inches', 'inch', 'in', 'yards', 'yard', 'yd', 'feet', 'foot', 'ft', "'", '"', '’', '”'), 
                     'volume': ('cups', 'cup', 'c', 'pints', 'pint', 'pt', 'quarts', 'quart', 'qt', 'gallons', 'gallon', 'gal', 'liter', 'l'), 
                     'mass': ('tons', 'ton', 'kilograms', 'kilogram', 'kg', 'grams', 'gram', 'g', 'milligrams', 'milligram', 'mg', 'pound', 'lb', 'ounce', 'oz'), 
                     'temperature': ('°C', '°F', 'k'), 
                     'energy': ('joule', 'j', 'kilojoule', 'kj', 'kWh', 'calories', 'cal', 'kilocalories', 'kcal'), 
                     'area': ('square kilometers', 'sq km', 'square miles', 'sq mi', 'square meters', 'sq m', 'square centimeters', 'sq cm', 'square feet', 'sq, ft', 
                              'square yards', 'sq yd', 'square inch', 'sq, in', 'hectare', 'ha', 'acre', 'ac'), 
                     'speed': ('cm/s', 'm/s', 'km/h', 'mph', 'knot', 'ft/s'), 
                     'time': ('years', 'year', 'yr', 'weeks', 'week', 'w', 'days', 'day', 'd', 'hours', 'hour', 'h', 'minutes', 'minute', 'mins', 'min', 'seconds', 'second', 's', 'milliseconds', 'millisecond', 'ms'), 
                     'power': ('watts', 'watt', 'w', 'kilowatts', 'kilowatt', 'kw', 'megawatts', 'megawatt', 'mw'), 
                     'voltage': ('kilovolts', 'kilovolt', 'kv', 'millivolts', 'millivolt', 'mv', 'volts', 'volt', 'Vrms', 'Vpp', 'v'), 
                     'current': ('ampere', 'amp', 'A', 'mA', 'μA'),
                     'resistance': ('kohms', 'kohm', 'kΩ', 'ohms', 'ohm', 'Ω'), 
                     'capacitance': ('farads', 'farad', 'F', 'microfarads', 'microfarad', 'μF', 'picofarads', 'picofarad', 'pF'), 
                     'data': ('bits', 'bit', 'b', 'bytes', 'byte', 'B', 'kilobytes', 'kilobyte', 'KB', 'megabytes', 'megabyte', 'MB', 'gigabytes', 'gigabyte', 'GB', 'terabytes', 'terabyte', 'TB'), 
                     'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                     'pressure': ('kilopascals', 'kilopascal', 'kpa', 'pascals', 'pascal', 'pa'),
                     'frequency': ('mHz', 'kHz', 'Hz', 'rpm'), 
                     'sound': ('decibel', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                     }
    UNITS_French = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', 'milles', 'pouces', 'pouce', 'in', 'mètre', 'yd', 'pieds', 'pied', 'ft', "'", '"', '’', '”'), 
                    'volume': ('tasses', 'tasse', 'c', 'pintes', 'pinte', 'pt', 'litres', 'litre', 'qt', 'gallons', 'gallon', 'gal', 'l'), 
                    'mass': ('tonnes', 'tonne', 'kilogrammes', 'kilogramme', 'kg', 'grammes', 'gramme', 'g', 'milligrammes', 'milligramme', 'mg', 'livre', 'lb', 'once', 'oz'), 
                    'temperature': ('°C', '°F', 'k'), 
                    'energy': ('joule', 'j', 'kilojoule', 'kj', 'kWh', 'calories', 'cal', 'kilocalories', 'kcal'), 
                    'area': ('kilomètres carrés', 'sq km', 'milles carrés', 'sq mi', 'mètres carrés', 'sq m', 'centimètres carrés', 'sq cm', 'pieds carrés', 'sq, ft', 
                             'mètre carrées', 'sq yd', 'pouce carré', 'sq, in', 'hectare', 'ha', 'acre', 'ac'), 
                    'speed': ('cm/s', 'm/s', 'km/h', 'mph', 'nœud marin', 'fps'), 
                    'time': ('ans', 'année', 'yr', 'semaines', 'semaine', 'w', 'jours', 'jour', 'd', 'heures', 'heure', 'h', 'minutes', 'mins', 'min', 'seconds', 'second', 's', 'millisecondes', 'milliseconde', 'ms'), 
                    'power': ('watts', 'watt', 'w', 'kilowatts', 'kilowatt', 'kw', 'mégawatts', 'mégawatt', 'mw'), 
                    'voltage': ('kilovolts', 'kilovolt', 'kv', 'millivolts', 'millivolt', 'mv', 'volts', 'volt', 'Vrms', 'Vpp', 'v'), 
                    'current': ('ampère', 'amp', 'A', 'mA', 'μA'),
                    'resistance': ('kilohms', 'kilohm', 'kΩ', 'ohms', 'ohm', 'Ω'), 
                    'capacitance': ('farads', 'farad', 'F', 'microfarads', 'microfarad', 'μF', 'picofarads', 'picofarad', 'pF'), 
                    'data': ('bits', 'bit', 'b', 'octets', 'octet', 'B', 'kilo-octets', 'kilo-octet', 'KB', 'mégaoctets', 'mégaoctet', 'MB', 'gigaoctets', 'gigaoctet', 'GB', 'téraoctets', 'téraoctet', 'TB'), 
                    'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                    'pressure': ('kilopascals', 'kilopascal', 'kpa', 'pascals', 'pascal', 'pa'),
                    'frequency': ('mHz', 'kHz', 'Hz', 'rpm'), 
                    'sound': ('décibel', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                    }
    UNITS_German = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', 'Meilen', 'Zoll', 'in', 'Meter', 'Yard', 'yd', 'Fuß', 'ft', "'", '"', '’', '”'), 
                    'volume': ('Tassen', 'Tasse', 'c', 'Pints', 'Pint', 'pt', 'Quarts', 'Quart', 'qt', 'Gallonen', 'gal', 'Liter', 'l'), 
                    'mass': ('Tonnen', 'Tonne', 'Kilogramm', 'kg', 'Gramm', 'g', 'Milligramm', 'mg', 'Pfund', 'lb', 'Unze', 'oz'), 
                    'temperature': ('°C', '°F', 'k'), 
                    'energy': ('Joule', 'j', 'Kilojoule', 'kj', 'kWh', 'Kalorien', 'cal', 'Kilokalorien', 'kcal'), 
                    'area': ('Quadratkilometer', 'sq km', 'Quadratmeilen', 'sq mi', 'Quadratmeter', 'sq m', 'Quadratzentimeter', 'sq cm', 'Quadratfuß', 'sq, ft', 
                             'Quadratmeter', 'sq yd', 'Quadratzoll', 'sq, in', 'Hektar', 'ha', 'Morgen', 'ac'), 
                    'speed': ('cm/s', 'm/s', 'km/h', 'mph', 'Knoten', 'Fuß/s'), 
                    'time': ('Jahre', 'yr', 'Wochen', 'Woche', 'w', 'Tage', 'd', 'Stunden', 'Stunde', 'h', 'Minuten', 'mins', 'min', 'Sekunden', 's', 'Millisekunden', 'ms'), 
                    'power': ('Watt', 'w', 'Kilowatt', 'kw', 'Megawatt', 'mw'), 
                    'voltage': ('Kilovolt', 'kv', 'Millivolt', 'mv', 'Volt', 'Vrms', 'Vpp', 'v'), 
                    'current': ('Ampere', 'amp', 'A', 'mA', 'μA'),
                    'resistance': ('kOhm', 'kΩ', 'Ohm', 'Ω'), 
                    'capacitance': ('Farad', 'F', 'Mikrofarads', 'Mikrofarad', 'μF', 'Picofarads', 'Picofarad', 'pF'), 
                    'data': ('Bits', 'Bit', 'b', 'Byte', 'B', 'Kilobyte', 'KB', 'Megabyte', 'MB', 'Gigabyte', 'GB', 'Terabyte', 'TB'), 
                    'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                    'pressure': ('Kilopascal', 'kpa', 'Pascal', 'pa'),
                    'frequency': ('mHz', 'kHz', 'Hz', 'rpm'), 
                    'sound': ('Dezibel', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                    }
    UNITS_Japanese = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', 'マイル', 'インチ', 'in', 'ヤード', 'yd', 'フィート', 'ft', "'", '"', '’', '”'), 
                      'volume': ('カップ', 'c', 'パイント', 'pt', 'クォート', 'qt', 'ガロン', 'gal', 'リットル', 'l'), 
                      'mass': ('トン', 'キログラム', 'kg', 'グラム', 'g', 'ミリグラム', 'mg', 'ポンド', 'lb', 'オンス', 'oz'), 
                      'temperature': ('°C', '°F', 'k'), 
                      'energy': ('ジュール', 'j', 'キロジュール', 'kj', 'kWh', 'カロリー', 'cal', 'キロカロリー', 'kcal'), 
                      'area': ('平方キロメートル', 'sq km', '平方マイル', 'sq mi', '平方メートル', 'sq m', '平方センチメートル', 'sq cm', '平方フィート', 'sq, ft', 
                               '平方ヤード', 'sq yd', '平方インチ', 'sq, in', 'ヘクタール', 'ha', 'エーカー', 'ac'), 
                      'speed': ('cm/s', 'm/s', 'km/h', 'mph', 'ノット', 'ft/s'), 
                      'time': ('年', 'yr', '週間', 'w', '日', 'd', '時間', 'h', '分', 'mins', 'min', '秒', 's', 'ミリ秒', 'ms'), 
                      'power': ('ワット', 'w', 'キロワット', 'kw', 'メガワット', 'mw'), 
                      'voltage': ('キロボルト', 'kv', 'ミリボルト', 'mv', 'ボルト', 'Vrms', 'Vpp', 'v'), 
                      'current': ('アンペア', 'amp', 'A', 'mA', 'μA'),
                      'resistance': ('キロオーム', 'kΩ', 'オーム', 'Ω'), 
                      'capacitance': ('ファラド', 'F', 'マイクロファラッド', 'μF', 'ピコファラッド', 'pF'), 
                      'data': ('ビット', 'b', 'バイト', 'B', 'キロバイト', 'KB', 'メガバイト', 'MB', 'ギガバイト', 'GB', 'テラバイト', 'TB'), 
                      'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                      'pressure': ('キロパスカル', 'kpa', 'パスカル', 'pa'),
                      'frequency': ('mHz', 'kHz', 'Hz', 'rpm'), 
                      'sound': ('デシベル', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
                      }
    UNITS_Spanish = {'length': ('mi', 'kms', 'km', 'm', 'cm', 'mm', 'millas', 'milla', 'pulgadas', 'pulgada', 'in', 'yardas', 'yarda', 'yd', 'pies', 'pie', 'ft', "'", '"', '’', '”'), 
                     'volume': ('tazas', 'taza', 'c', 'pintas', 'pinta', 'pt', 'cuartos', 'qt', 'galones', 'gal', 'litros', 'l'), 
                     'mass': ('toneladas', 'kilogramos', 'kg', 'gramos', 'gramo', 'g', 'miligramos', 'miligramo', 'mg', 'libras', 'lb', 'onzas', 'oz'), 
                     'temperature': ('°C', '°F', 'k'), 
                     'energy': ('julio', 'j', 'kilojulio', 'kj', 'kWh', 'calorías', 'cal', 'kilocalorías', 'kcal'), 
                     'area': ('kilómetros cuadrados', 'sq km', 'millas cuadradas', 'sq mi', 'metros cuadrados', 'sq m', 'centímetros cuadrados', 'sq cm', 'pies cuadrados', 'sq, ft', 
                              'yardas cuadradas', 'sq yd', 'pulgadas cuadradas', 'sq, in', 'hectáreas', 'ha', 'acres', 'ac'), 
                     'speed': ('cm/s', 'm/s', 'km/h', 'mph', 'nudo', 'pies/s'), 
                     'time': ('años', 'yr', 'semanas', 'w', 'días', 'd', 'horas', 'h', 'minutos', 'mins', 'min', 'segundos', 's', 'milisegundos', 'ms'), 
                     'power': ('vatios', 'w', 'kilovatios', 'kw', 'megavatios', 'mw'), 
                     'voltage': ('kilovoltios', 'kilovoltio', 'kv', 'milivoltios', 'mv', 'voltios', 'Vrms', 'Vpp', 'v'), 
                     'current': ('amperios', 'amp', 'A', 'mA', 'μA'),
                     'resistance': ('kohms', 'kohm', 'kΩ', 'ohmios', 'ohm', 'Ω'), 
                     'capacitance': ('faradios', 'faradio', 'F', 'microfaradios', 'microfaradio', 'μF', 'picofaradios', 'picofaradio', 'pF'), 
                     'data': ('bits', 'b', 'bytes', 'B', 'kilobytes', 'KB', 'megabytes', 'MB', 'gigabytes', 'GB', 'terabytes', 'TB'), 
                     'data rate': ('gbps', 'gbs', 'gb/s', 'mbps', 'mbs', 'mb/s', 'kbps', 'kbs', 'kb/s', 'bps', 'b/s'),
                     'pressure': ('kilopascales', 'kilopascal', 'kpa', 'pascales', 'pascal', 'pa'),
                     'frequency': ('mHz', 'kHz', 'Hz', 'rpm'), 
                     'sound': ('decibelios', 'dB', 'dBμV', 'dBV', 'dBmV', 'dBFS', 'dBm', 'dBW', 'dBA')
              }
    UNITS = {'ara': UNITS_Arabic, 
             'deu': UNITS_German, 
             'eng': UNITS_English, 
             'fra': UNITS_French, 
             'jpn': UNITS_Japanese, 
             'spa': UNITS_Spanish, 
             'zhs': UNITS_Chinese_Simplified,
             'zht': UNITS_Chinese_Traditional}
    QUANTITY_PATTERN = {}
    for lang in UNITS:
        QP_unit = r'(?:(?:' + r'|'.join(sum(set(list(UNITS[lang].values()) + list(UNITS['eng'].values())), ())) + r')(?![\w\'"’”/]))'
        QP_numberUnitExp = r'(?:' + QP_numberRange + r'(?:\s*' + QP_unit + r'))'
        QP_dimension = r'(?:' + QP_numberUnitExp + '(?:(?:\s*(?:x|by)\s*' + QP_numberUnitExp + r')*))'
        QP_dimensionRange = r'(?:' + QP_dimension + r'(?:(?:\s*-\s*' + QP_dimension + r')*))'
        QP_dimensionRangeSelection = r'(' + QP_dimensionRange + r'(?:(?:\s*/\s*' + QP_dimensionRange + r')*))'
        QUANTITY_PATTERN[lang] = r'(?i)(?P<quantity>' + QP_dimensionRangeSelection + ')' 
         
    DP_year_Arabic  = r'(?:\b(?:\d{4})\b)' 
    DP_year_Chinese_Simplified  = r'(?:\b(?:\d{4})年?)'
    DP_year_Chinese_Traditional  = r'(?:\b(?:\d{4})年?)'
    DP_year_English  = r'(?:\b(?:\d{4})\b)'
    DP_year_French  = r'(?:\b(?:\d{4})\b)'
    DP_year_German  = r'(?:\b(?:\d{4})\b)'
    DP_year_Japanese  = r'(?:\b(?:\d{4})年?)'
    DP_year_Spanish  = r'(?:\b(?:\d{4})\b)'
    DP_years = {'ara': DP_year_Arabic, 
                'deu': DP_year_German, 
                'eng': DP_year_English, 
                'fra': DP_year_French, 
                'jpn': DP_year_Japanese, 
                'spa': DP_year_Spanish, 
                'zhs': DP_year_Chinese_Simplified,
                'zht': DP_year_Chinese_Traditional}
    
    DP_month_Arabic = (r'''(?:(?:\d{1,2}|'''
                       r'''يناير|فبراير|مارس|أبريل|مايو|يونيو|'''
                       r'''يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)(?=(?:[\s/_,-]|$)))'''
                       )   
    DP_month_Chinese_Simplified = (r'''(?:\d{1,2}|'''
                                   r'''一月|1月|二月|2月|三月|3月|四月|4月|五月|5月|六月|6月|'''
                                   r'''七月|7月|八月|8月|九月|9月|十月|10月|十一月|11月|十二月|12月)'''
                                   )  
    DP_month_Chinese_Traditional = (r'''(?:\d{1,2}|'''
                                    r'''一月|1月|二月|2月|三月|3月|四月|4月|五月|5月|六月|6月|'''
                                    r'''七月|7月|八月|8月|九月|9月|十月|10月|十一月|11月|十二月|12月)'''
                                    )       
    DP_month_English = (r'''(?:\b(?:\d{1,2}|'''
                        r'''January|Jan(?:\.)?|February|Feb(?:\.)?|March|Mar(?:\.)?|April|Apr(?:\.)?|May|June|Jun(?:\.)?|'''
                        r'''July|Jul(?:\.)?|August|Aug(?:\.)?|September|Sep(?:\.)?|October|Oct(?:\.)?|November|Nov(?:\.)?|December|Dec(?:\.)?)(?=(?:[\s/_,-]|$)))'''
                        ) 
    DP_month_French = (r'''(?:\b(?:\d{1,2}|'''
                       r'''janvier|janv(?:\.)?|février|févr(?:\.)?|mars|avril|mai|juin|'''
                       r'''juillet|juil(?:\.)?|août|septembre|sept(?:\.)?|octobre|oct(?:\.)?|novembre|nov(?:\.)?|décembre|déc(?:\.)?)(?=(?:[\s/_,-]|$)))'''
                       )    
    DP_month_German = (r'''(?:\b(?:\d{1,2}|'''
                       r'''Januar|Jan(?:\.)?|Jän(?:\.)?|Februar|Feb(?:\.)?|März|April|Apr(?:\.)?|Mai|Juni|'''
                       r'''Juli|August|Aug(?:\.)?|September|Sept(?:\.)?|Oktober|Okt(?:\.)?|November|Nov(?:\.)?|Dezember|Dez(?:\.)?)(?=(?:[\s/_,-]|$)))'''
                       )  
    DP_month_Japanese = (r'''(?:\d{1,2}|'''
                         r'''1月|2月|3月|4月|5月|6月|'''
                         r'''7月|8月|9月|10月|11月|12月)'''
                         )
    DP_month_Spanish = (r'''(?:\b(?:\d{1,2}|'''
                        r'''de enero|de eno(?:\.)?|de febrero|de feb(?:\.)?|de fbro(?:\.)?|de marzo|de mzo(?:\.)?|de abril|de ab(?:\.)?|de abr(?:\.)?|de mayo|de junio|de jun(?:\.)?|'''
                        r'''de Julio|de jul(?:\.)?|de agosto|de agto(?:\.)?|de septiembre|de sept(?:\.)?|de sbre(?:\.)?|de set(?:\.)?|de octubre|de oct(?:\.)?|de obre(?:\.)?|de noviembre|de nov(?:\.)?|de nbre(?:\.)?|de diciembre|de dic(?:\.)?|de dbre(?:\.)?)(?=(?:[\s/_,-]|$)))'''
                        )      
    DP_months = {'ara': DP_month_Arabic, 
                 'deu': DP_month_German, 
                 'eng': DP_month_English, 
                 'fra': DP_month_French, 
                 'jpn': DP_month_Japanese, 
                 'spa': DP_month_Spanish, 
                 'zhs': DP_month_Chinese_Simplified,
                 'zht': DP_month_Chinese_Traditional}
    
    DP_day_Arabic = r'(?:\b(?:\d{1,2})\b)'
    DP_day_Chinese_Simplified = r'(?:\d{1,2}((?:日|号)|\b))'
    DP_day_Chinese_Traditional = r'(?:\d{1,2}((?:日|號)|\b))'
    DP_day_English = r'(?:\b(?:\d{1,2}(?:st|nd|rd|th)?)\b)'
    DP_day_French = r'(?:\b(?:\d{1,2}(?:er|re|e)?)\b)'
    DP_day_German = r'(?:\b(?:\d{1,2}(?:\.)?))'
    DP_day_Japanese = r'(?:\d{1,2}((?:日)|\b))'
    DP_day_Spanish = r'(?:\b(?:\d{1,2})\b)'
    DP_days = {'ara': DP_day_Arabic, 
               'deu': DP_day_German, 
               'eng': DP_day_English, 
               'fra': DP_day_French, 
               'jpn': DP_day_Japanese, 
               'spa': DP_day_Spanish, 
               'zhs': DP_day_Chinese_Simplified,
               'zht': DP_day_Chinese_Traditional}
    
    DP_separator_Arabic = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_Chinese_Simplified = r'\s*(?:|[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_Chinese_Traditional = r'\s*(?:|[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_English = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_French = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_German = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separator_Japanese = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)?\s*'
    DP_separator_Spanish = r'\s*(?:[\s]+|[-]+|[/]+|[_]+|[,]+)\s*'
    DP_separators = {'ara': DP_separator_Arabic, 
                     'deu': DP_separator_German, 
                     'eng': DP_separator_English, 
                     'fra': DP_separator_French, 
                     'jpn': DP_separator_Japanese, 
                     'spa': DP_separator_Spanish, 
                     'zhs': DP_separator_Chinese_Simplified,
                     'zht': DP_separator_Chinese_Traditional}
    
    DATE_PATTERN = {}
    DATE_PATTERN_ymd, DATE_PATTERN_ym, DATE_PATTERN_md = {}, {}, {}
    for lang in DP_months:
        DP_date_ymd = r'(?:(?:' + DP_years[lang] + DP_separators[lang] + DP_months[lang] + DP_separators[lang] + DP_days[lang] + r')|(?:' + DP_months[lang] + DP_separators[lang] + DP_days[lang] + DP_separators[lang] + DP_years[lang] + r')|(?:' +\
            DP_days[lang] + DP_separators[lang] + DP_months[lang] + DP_separators[lang] + DP_years[lang] + r'))'
        DP_date_ym = r'(?:(?:' + DP_years[lang] + DP_separators[lang] + DP_months[lang] + r')|(?:' + DP_months[lang] + DP_separators[lang] + DP_years[lang] + r'))'        
        DP_date_md = r'(?:(?:' + DP_days[lang] + DP_separators[lang] + DP_months[lang] + r')|(?:' + DP_months[lang] + DP_separators[lang] + DP_days[lang] + r'))' 
        DP_dateExp = r'(?:(?:' + DP_date_ymd + r')|(?:' + DP_date_ym + r')|(?:' + DP_date_md + r'))'  
        DP_dateRange = r'(?:' + DP_dateExp + r'(?:(?:\s*-\s*' + DP_dateExp + r')*))'          
        DP_dateRangeSelection = r'(' + DP_dateRange + r'(?:(?:\s*/\s*' + DP_dateRange + r')*))'       
        DATE_PATTERN[lang] = r'(?i)(?P<date>' + DP_dateRangeSelection + ')'   
        
        # Add sub date patterns
        DP_dateExp_ymd = r'(?:' + DP_date_ymd + r')'  
        DP_dateRange_ymd = r'(?:' + DP_dateExp_ymd + r'(?:(?:\s*-\s*' + DP_dateExp_ymd + r')*))'          
        DP_dateRangeSelection_ymd = r'(' + DP_dateRange_ymd + r'(?:(?:\s*/\s*' + DP_dateRange_ymd + r')*))'       
        DATE_PATTERN_ymd[lang] = r'(?i)(?P<date>' + DP_dateRangeSelection_ymd + ')'        
        
                  
class CommonRegexFrom3P:
    """Common regular expressions from 3rd-party libraries
       Including expynent and commonregex
       The searching behavior is less consistent than CommonRegex
       No named grouping is used, so use ...group(0) in mosts cases
       The patterns from cr_patterns are re.compiled, so use xxx.pattern and xxx.flags in re.search(...) 
    """
    
    # Language-insensitive
    
    URL_PATTERN = cr_patterns.link.pattern, cr_patterns.link.flags
    DIGIT_PATTERN = expy_patterns.FLOAT_NUMBER
    TIME_PATTERN = cr_patterns.time.pattern, cr_patterns.time.flags
    PHONENUMBER_NOEXT_PATTERN = cr_patterns.phone.pattern, cr_patterns.phone.flags
    PHONENUMBER_EXT_PATTERN = cr_patterns.phones_with_exts.pattern, cr_patterns.phones_with_exts.flags
    EMAIL_PATTERN = cr_patterns.email.pattern, cr_patterns.email.flags
    
    BITCOIN_ADDRESS_PATTERN = expy_patterns.BITCOIN_ADDRESS
    CREDIT_CARD_PATTERN = expy_patterns.CREDIT_CARD
    ETHEREUM_ADDRESS_PATTERN = expy_patterns.ETHEREUM_ADDRESS
    IP_V4_PATTERN = expy_patterns.IP_V4
    IP_V6_PATTERN = expy_patterns.IP_V6
    ISBN_PATTERN = expy_patterns.ISBN
    LATITUDE_PATTERN = expy_patterns.LATITUDE
    LONGITUDE_PATTERN = expy_patterns.LONGITUDE
    MAC_ADDRESS_PATTERN = expy_patterns.MAC_ADDRESS    
    ROMAN_NUMERAL_PATTERN = expy_patterns.ROMAN_NUMERALS
    UUID_PATTERN = expy_patterns.UUID
    HEX_COLOR_PATTERN = cr_patterns.hex_color.pattern, cr_patterns.hex_color.flags
        
    # Locale-sensitive
    
    LICENSE_PLATE_PATTERN = {'fra': expy_patterns.LICENSE_PLATE['FR']}
    ZIP_CODE_PATTERN = expy_patterns.ZIP_CODE   # keys are "alpha2" in COUNTRY_CODES
    STREET_ADDRESS_PATTERN = {'eng': (cr_patterns.street_address.pattern, cr_patterns.street_address.flags)}
    
    # Language-sensitive
    
    DATE_PATTERN = {'eng': (cr_patterns.date.pattern, cr_patterns.date.flags)}
    
    
class Writing:
    """Symbols, characters, punctuations, and other constants
    """
    
    COMMERCIAL_SYMBOLS = ('©', '™', '®')
    
    CURRENCY_SYMBOLS = ('$', '£', '€', '¥')
    
    NUMBER_SYMBOLS = ('¼', '½', '¾', '⅐', '⅑', '⅒', '⅓', '⅔', '⅕', '⅖', '⅗', '⅘', '⅙', '⅚', '⅛', '⅜', '⅝', '⅞', '↉')
    
    PERCENTAGE_SYMBOLS = ('%', '٪', '％')
    
    UNIT_SYMBOLS = ('°C', '°F', 'μ', 'Ω')
    
    BAD_CHARACTERS = ('\ufff9', '\ufffa', '\ufffb', '\ufffc', '\ufffd', '\ufffe', '\uffff')
    
    BRACKETS = (('(', ')'), ('[', ']'), ('{', '}'), ('⁅', '⁆'),  ('〈', '〉'), ('❨', '❩'), ('<', '>'), 
                ('❪', '❫'), ('❬', '❭'), ('❮', '❯'), ('❰', '❱'), ('❲', '❳'), ('❴', '❵'), 
                ('⟅', '⟆'), ('⟦', '⟧'), ('⟨', '⟩'), ('⟪', '⟫'), ('⟬', '⟭'), ('⟮', '⟯'), 
                ('⦃', '⦄'), ('⦅', '⦆'), ('⦇', '⦈'), ('⦉', '⦊'), ('⦋', '⦌'), ('⦍', '⦎'), 
                ('⦏', '⦐'), ('⦑', '⦒'), ('⦗', '⦘'), ('⧼', '⧽'), ('⸦', '⸧'), ('⸨', '⸩'), 
                ('〈', '〉'), ('《', '》'), ('「', '」'), ('『', '』'), ('【', '】'), ('〔', '〕'), 
                ('〖', '〗'), ('〘', '〙'), ('〚', '〛'), ('﴾', '﴿'), ('﹙', '﹚'), ('﹛', '﹜'), 
                ('﹝', '﹞'), ('（', '）'), ('［', '］'), ('｛', '｝'), ('｟', '｠'), ('｢', '｣')
                )
    
    QUOTATIONS = (('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’'),  ('«', '»'), ('〝', '〞'),
                  ('‚', '’'), ('„', '”'), ('„', '“'), ('‹', '›'), ('”', '”'), ('’', '’'), 
                  ('»', '«'), ('「', '」'), ('『', '』'), ('›', '‹'), ('»', '»'), ('‚', '‘'), 
                  ('《', '》'), ('〈', '〉'), ('’', '‘')
                 )
    
    PAIRED_PUNCTUATIONS = (('¿', '?'), ('¡', '!'))
          
    SUPERSCRIPTS = ('⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', 'ⁱ', '⁺', '⁻', '⁼', '⁽', '⁾', 'ⁿ')
    
    SUBSCRIPTS = ('₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉', '₊', '₋', '₌', '₍', '₎', 'ₐ', 'ₑ', 'ₒ', 'ₓ', 'ₔ', 'ₕ', 'ₖ', 'ₗ', 'ₘ', 'ₙ', 'ₚ', 'ₛ', 'ₜ')
    
    PUNCTUATIONS_SENTENCE_COMMON = {'ara': '.،؟؛:!', 
                                    'ces': '.?;,:!', 
                                    'dan': '.?;,:!', 
                                    'deu': '.?;,:!', 
                                    'ell': '.;,·:!', 
                                    'eng': '.?;,:!', 
                                    'fin': '.?;,:!', 
                                    'fra': '.?;,:!', 
                                    'heb': '.?;,:!', 
                                    'hin': '|॥.?;,:!', 
                                    'hun': '.?;,:!', 
                                    'ind': '.?;,:!', 
                                    'ita': '.?;,:!', 
                                    'jpn': '。？；、，：！',
                                    'kor': '.?;,:!',  
                                    'msa': '.?;,:!', 
                                    'nld': '.?;,:!', 
                                    'nor': '.?;,:!', 
                                    'pol': '.?;,:!', 
                                    'por': '.?;,:!', 
                                    'ron': '.?;,:!', 
                                    'rus': '.?;,:!', 
                                    'spa': '.?;,:!', 
                                    'srp': '.?;,:!',                                    
                                    'swe': '.?;,:!', 
                                    'tha': '.?;,:!', 
                                    'tur': '.?;,:!', 
                                    'vie': '.?;,:!', 
                                    'ypt': '。？；、，：！', 
                                    'zhh': '。？；、，：！',
                                    'zhs': '。？；、，：！',
                                    'zht': '。？；、，：！'
                                    }
    
    PUNCTUATIONS_SENTENCE_FINAL = {'ara': '.،؟؛:!', 
                                   'ces': '.?;,:!', 
                                   'dan': '.?;,:!', 
                                   'deu': '.?;,:!', 
                                   'ell': '.;,·:!', 
                                   'eng': '.?;,:!', 
                                   'fin': '.?;,:!', 
                                   'fra': '.?;,:!', 
                                   'heb': '.?;,:!', 
                                   'hin': '|.?;,:!', 
                                   'hun': '.?;,:!', 
                                   'ind': '.?;,:!', 
                                   'ita': '.?;,:!', 
                                   'jpn': '。？；、，：！',
                                   'kor': '.?;,:!',  
                                   'msa': '.?;,:!', 
                                   'nld': '.?;,:!', 
                                   'nor': '.?;,:!', 
                                   'pol': '.?;,:!', 
                                   'por': '.?;,:!', 
                                   'ron': '.?;,:!', 
                                   'rus': '.?;,:!', 
                                   'spa': '.?;,:!', 
                                   'srp': '.?;,:!',                                    
                                   'swe': '.?;,:!', 
                                   'tha': '.?;,:!', 
                                   'tur': '.?;,:!', 
                                   'vie': '.?;,:!', 
                                   'ypt': '。？；，：！', 
                                   'zhh': '。？；，：！',
                                   'zhs': '。？；，：！',
                                   'zht': '。？；，：！'
                                   } 

    PUNCTUATIONS_FOR_MAPPINGS = {'ara': '.؟؛،:!', 
                                 'ces': '.?;,:!', 
                                 'dan': '.?;,:!', 
                                 'deu': '.?;,:!', 
                                 'ell': '.;,·:!', 
                                 'eng': '.?;,:!', 
                                 'fin': '.?;,:!', 
                                 'fra': '.?;,:!', 
                                 'heb': '.?;,:!', 
                                 'hin': '.?;,:!', 
                                 'hun': '.?;,:!', 
                                 'ind': '.?;,:!', 
                                 'ita': '.?;,:!', 
                                 'jpn': '。？；，：！',
                                 'kor': '.?;,:!',  
                                 'msa': '.?;,:!', 
                                 'nld': '.?;,:!', 
                                 'nor': '.?;,:!', 
                                 'pol': '.?;,:!', 
                                 'por': '.?;,:!', 
                                 'ron': '.?;,:!', 
                                 'rus': '.?;,:!', 
                                 'spa': '.?;,:!', 
                                 'srp': '.?;,:!',                                    
                                 'swe': '.?;,:!', 
                                 'tha': '.?;,:!', 
                                 'tur': '.?;,:!', 
                                 'vie': '.?;,:!', 
                                 'ypt': '。？；，：！', 
                                 'zhh': '。？；，：！',
                                 'zhs': '。？；，：！',
                                 'zht': '。？；，：！'
                                 }
    
    PUNCTUATIONS_LEADING = ('-', '\\')
    PUNCTUATIONS_TRAILING = ('…', '-')
    
    CHARACTERS_UNICODE_NAME = {'ara': ['ARABIC'], 
                               'ces': ['LATIN'], 
                               'dan': ['LATIN'], 
                               'deu': ['LATIN'], 
                               'ell': ['GREEK'], 
                               'eng': ['LATIN'], 
                               'fin': ['LATIN'], 
                               'fra': ['LATIN'], 
                               'heb': ['HEBREW'], 
                               'hin': ['DEVANAGARI'], 
                               'hun': ['LATIN'], 
                               'ind': ['LATIN'], 
                               'ita': ['LATIN'], 
                               'jpn': ['CJK', 'HIRAGANA', 'KATAKANA', 'KATAKANA-HIRAGANA'],
                               'kor': ['CJK', 'HANGUL'],  
                               'msa': ['LATIN'], 
                               'nld': ['LATIN'], 
                               'nor': ['LATIN'], 
                               'pol': ['LATIN'], 
                               'por': ['LATIN'], 
                               'ron': ['LATIN'], 
                               'rus': ['CYRILLIC'], 
                               'spa': ['LATIN'], 
                               'srp': ['LATIN', 'CYRILLIC'],                                    
                               'swe': ['LATIN'], 
                               'tha': ['THAI'], 
                               'tur': ['LATIN'], 
                               'vie': ['LATIN'], 
                               'ypt': ['CJK'], 
                               'zhh': ['CJK'],
                               'zhs': ['CJK'],
                               'zht': ['CJK']
                               }
    
    