from .tm_fileparser import TmFileParser
import pandas as pd, os, re, codecs
from lxml import etree
import langid
import spacy
from spacy_langdetect import LanguageDetector
from bs4 import BeautifulSoup

def removeMemsourceTag(texts):

    texts = [re.sub(r'\s+', " ",
                    re.sub(r'(\{\w{1,2}\>)|(\<\w{1,2}\})', ' ', str(t))
                    ).strip() + '\n' for t in texts]
    texts = [re.sub(r"\{\d{1,2}\}", "", str(t)) for t in texts]

    return texts

def detect_language(texts, corpus_name="en_core_web_lg", langs=['en', 'fr']):
    """Detect the language of a list of texts.
        return detected languages"""

    # nlp = spacy.load(corpus_name)
    # nlp.add_pipe(LanguageDetector(), name="language_detector", last=True)
    # detected_langs = [nlp(str(text))._.language['language'] for text in texts] # convert text into lowercase.

    langid.set_languages(langs)
    detected_langs = [langid.classify(text.lower())[0] for text in texts]

    return detected_langs

def mxliff_to_excel(mxliff_file, output):

    tfp = TmFileParser('mxliff')
    tfp.parse(mxliff_file)

    df = pd.DataFrame({'source': tfp.srcTexts, 'target': tfp.tgtTexts})
    df.to_excel(output, header=True, index=None)

def compare_MT_TM(excel_MT, excel_TM, output):
    """Make sure source on MT and TM files are aligned and same."""

    df_mt = pd.read_excel(excel_MT)
    df_tm = pd.read_excel(excel_TM)

    same = []
    for tgt_mt, tgt_tm in zip(df_mt['target'], df_tm['target']):

        if tgt_mt.strip() != tgt_tm.strip():
            same.append('False')

        else:
            same.append('True')

    df_mt['target_withTM'] = df_tm['target']
    df_mt['same'] = same

    df_mt.rename(columns={'target': 'target_withoutTM'})
    df_mt.to_excel(output, header=True, index=None)

def extract_src_segment(file_dir, return_dataframe=True):

    srcTexts = []

    parser = etree.XMLParser(strip_cdata=False)
    doc = etree.parse(file_dir, parser)

    xmlNamespace = '{' + doc.getroot().nsmap[None] + '}'
    transNodes = doc.findall('.//' + xmlNamespace + "trans-unit")

    for i, trans_unit in enumerate(transNodes):

        if trans_unit is not None:
            try:
                src_node = trans_unit.find('.//' + xmlNamespace + "source")  # layer 3
            except:
                raise Exception("source tag containing source text not found.")

            if src_node is not None:
                srcTexts.append(src_node.text)

    if return_dataframe:
        df = pd.DataFrame({'source': srcTexts})
        return df

    return srcTexts

def extract_src_tgt_score(file_dir, excel_output, add_score=False, add_mt_origin='all'):

    srcTexts = []
    tgtTexts = []
    scores = []
    # mt_origin = []

    parser = etree.XMLParser(strip_cdata=False)
    doc = etree.parse(file_dir, parser)

    xmlNamespace = '{' + doc.getroot().nsmap[None] + '}'
    transNodes = doc.findall('.//' + xmlNamespace + "trans-unit")

    for i, trans_unit in enumerate(transNodes):

        if trans_unit is not None:
            try:
                src_node = trans_unit.find('.//' + xmlNamespace + "source")  # layer 3
            except:
                raise Exception("source tag containing source text not found.")
            try:
                tgt_node = trans_unit.find('.//' + xmlNamespace + "target")
            except:
                raise Exception("target tag containing target text not found.")

            if (src_node is not None) and (tgt_node is not None):
                # if (src_node.text is not None) and (tgt_node.text is not None):
                    mt_origin = trans_unit.values()[4]  # MT origin: mt, null, tm, etc.

                    if add_mt_origin == 'all':
                        srcTexts.append(src_node.text)
                        tgtTexts.append(tgt_node.text)
                        scores.append(trans_unit.values()[2])  # TM matching score
                    # elif add_mt_origin == mt_origin:
                    elif mt_origin in add_mt_origin:
                        srcTexts.append(src_node.text)
                        tgtTexts.append(tgt_node.text)
                        scores.append(trans_unit.values()[2])  # TM matching score
                    else:
                        pass

    if add_score:
        df = pd.DataFrame({'source': srcTexts, 'target': tgtTexts, 'score': scores})
    else:
        df = pd.DataFrame({'source': srcTexts, 'target': tgtTexts})

    # elif add_mt_origin == 'mt':
    #     if add_score:
    #         mt_segments = zip(srcTexts, tgtTexts, scores, mt_origin)
    #         df = pd.DataFrame({'source': srcTexts, 'target': tgtTexts, 'score': scores})
    df.to_excel(excel_output, header=True, index=None)

def pipelineDetectLangOfTranslatedSegments(file_dir, excel_output, lang='en'):

    df = extract_src_segment(file_dir)
    df['source'] = removeMemsourceTag(df['source'])
    df['lang'] = detect_language(df['source'], corpus_name="en_core_web_lg")
    df = df[df.apply(lambda x: x['lang'] == lang, axis=1)]

    df.to_excel(excel_output, header=True, index=None)


def test_0():
    # pipeline for single file.
    file_dir = "/linguistics/ethan/document_test/mxliff/JHN13365 Investor Brochure FR_en-en_ca-fr_ca-T.mxliff"
    excel_output = "/linguistics/ethan/document_test/source_segments/JHN13365 Investor Brochure FR_en-en_ca-fr_ca-T.untranslated.xlsx"
    pipelineDetectLangOfTranslatedSegments(file_dir, excel_output, lang='fr')

    # pipeline for a batch of files
    # input_root = '/linguistics/ethan/document_test/mxliff'
    # output_root = '/linguistics/ethan/document_test/source_segments'
    # for file in os.listdir(input_root):
    #     print("Convert file: {}".format(file))
    #     input_file = os.path.join(input_root, file)
    #     output_file = os.path.join(output_root, file + ".untranslated.xlsx")
    #     pipelineDetectLangOfTranslatedSegments(input_file, output_file, lang='en')

def test_1():
    mxliff_withTM = r'C:\Users\Ethan\Downloads\withTB-Standards_410-200312-001_AcSB March 3-4 2020 Decision summary v3_EN-en_ca-fr_ca-T.mxliff'
    mxliff_withoutTB = r'C:\Users\Ethan\Downloads\withoutTB-Standards_410-200312-001_AcSB March 3-4 2020 Decision summary v3_EN-en_ca-fr_ca-T.mxliff'

    excel_withTB = r'C:\Users\Ethan\Downloads\withTB-Standards_410-200312-001_AcSB March 3-4 2020 Decision summary v3_EN-en_ca-fr_ca-T.xlsx'
    excel_withoutTB = r'C:\Users\Ethan\Downloads\withoutTB-Standards_410-200312-001_AcSB March 3-4 2020 Decision summary v3_EN-en_ca-fr_ca-T.xlsx'

    mxliff_to_excel(mxliff_withTM, excel_withTB)
    mxliff_to_excel(mxliff_withoutTB, excel_withoutTB)

    compared_mt_tm = r'C:\Users\Ethan\Downloads\diff_src_tgt_same_tb.xlsx'

    compare_MT_TM(excel_withoutTB, excel_withTB, compared_mt_tm)

def test_2():
    file_dir = r'/linguistics/ethan/Downloads/comparison guarantee_redacted-en_ca-fr_ca-T.mxliff'
    output = r'/linguistics/ethan/Bicleaner/Client_TM/comparison_guarantee/comparison guarantee_redacted.xlsx'
    extract_src_tgt_score(file_dir, output, add_score=False, add_mt_origin='all')

def test_3():
    excel = '/linguistics/ethan/Bicleaner/Client_TM/comparison_guarantee/comparison guarantee_redacted.xlsx'
    df = pd.read_excel(excel, converters={'source': str})
    # with codecs.open("./data/client/merge_dedup.client.txt", 'r') as f:
    #     lines = f.readlines()
    df['source'] = removeMemsourceTag(df['source'])
    df.to_excel(excel, header=True, index=None)
    # with codecs.open("./data/client/merge_dedup.cleaned.txt", 'w') as f:
    #     f.writelines(lines)

def test_4():
    """Extract source segments from Memsource."""

    mxliff = '/linguistics/ethan/Downloads/195canlii1-en_ca-fr_ca-T.mxliff'
    output = "/linguistics/ethan/Crawled_data/Canlii/historic_monolingual/monolingual_AllTime/courts/PDF_segments/195canlii1-memsource.xlsx"
    df = extract_src_segment(mxliff)
    df['source'] = removeMemsourceTag(df['source'])
    df.to_excel(output, header=True, index=None)


if __name__ == '__main__':
    # test_0()
    # test_1()
    # test_2()
    # test_3()
    test_4()
