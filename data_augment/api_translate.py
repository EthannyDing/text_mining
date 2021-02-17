import os, codecs, sys
import json
import requests
BASE = os.path.abspath("..")
sys.path.insert(0, BASE)
from tb_utils.tm_fileparser import txt_io
CREDENTIAL = 'beddbd04-8991-2318-6cc4-f8c76dc60c13'
ENDPOINT = "https://testing.alexatranslations.com/v2/translate/"


def separate_translated_and_nontranslated(src_file, tgt_file,
                                          translated_src_file, translated_tgt_file,
                                          nontranslated_file):
    """Since calling api to translate texts can save empty lines in target file, we need to
       separate translated pairs from source and target file."""
    src_lines = txt_io(src_file, "r")
    tgt_lines = txt_io(tgt_file, "r")

    translated_src_lines = []
    translated_tgt_lines = []
    nontranslated_src_lines = []
    print("Finding translated pairs.")
    for i, tgt in enumerate(tgt_lines):
        src = src_lines[i]
        if tgt.strip():
            print("translated segment: {}".format(tgt))
            translated_src_lines.append(src)
            translated_tgt_lines.append(tgt)

        else:
            nontranslated_src_lines.append(src)

    # remaining_nontranslated_src_lines =
    nontranslated_src_lines += src_lines[len(tgt_lines):]
    assert len(translated_src_lines) == len(translated_tgt_lines), "source and target length unequal."
    print("Saving {} translated source segments.".format(len(translated_src_lines)))
    txt_io(translated_src_file, action='w', write_lines=translated_src_lines)

    print("Saving {} translated target segments.".format(len(translated_tgt_lines)))
    txt_io(translated_tgt_file, action='w', write_lines=translated_tgt_lines)

    print("Saving {} non-translated source segments.".format(len(nontranslated_src_lines)))
    txt_io(nontranslated_file, action='w', write_lines=nontranslated_src_lines)


def call_alexa_api(source_texts, srcLang, tgtLang):

    data = {'input': source_texts,
            'from': srcLang,
            'to': tgtLang,
            'credential': CREDENTIAL}
    content = requests.post(ENDPOINT, data=data).content
    translation = json.loads(content)['Translation']

    return translation


def read_in_chunks(file_object, batch_size=200):
    """generate a number of batch_size lines each time, memory efficient"""
    while True:
        batch = []
        try:
            for i in range(batch_size):
                line = next(file_object)
                batch.append(line)
        except StopIteration:
            yield batch
            break

        yield batch


def append_result(file, lines):
    with open(file, 'a') as f:
        for line in lines:
            f.write(line.strip() + '\n')


def translate_batch(src_file, output_file, srcLang, tgtLang, batch_size=200):
    """Translate source texts stored in text file and save the translation in target file, batch-wise."""
    with open(src_file, 'r') as f:
        for i, lines in enumerate(read_in_chunks(f, batch_size)):
            print("--- translating lines {} - {}".format(i*batch_size, min((i+1)*batch_size, i*batch_size + len(lines))))
            try:
                translation = call_alexa_api(lines, srcLang, tgtLang)
            except:
                translation = ["\n"] * batch_size

            append_result(output_file, translation)


def test_translate_batch():
    src_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/untranslated_src_after_batch_1.fra"
    output_file = '/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/second_batch/batch_2_tgt.eng.translated'
    srcLang = 'fra'
    tgtLang = 'eng'
    batch_size = 100
    translate_batch(src_file, output_file, srcLang, tgtLang, batch_size=batch_size)


def test_separate_translated_and_nontranslated():
    src_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/canlii_monolingual_final.fra"
    tgt_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/canlii_monolingual_final.eng.translated"
    translated_src_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/first_batch/batch1_src.fra"
    translated_tgt_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/first_batch/batch1_tgt.eng"
    nontranslated_file = "/linguistics/ethan/Canlii_data/historic_html/Final_mono_fra/first_batch/untranslated_src.fra"
    separate_translated_and_nontranslated(src_file, tgt_file,
                                          translated_src_file, translated_tgt_file,
                                          nontranslated_file)


if __name__ == "__main__":

    test_translate_batch()
    # test_separate_translated_and_nontranslated()
