import unittest, sys, os
from pathlib import Path
BASE_DIR = Path(os.path.abspath(__file__)).parent.parent.__str__()
sys.path.insert(0, BASE_DIR)
from tb_extractor import find_word_index_of_term, find_terminology_pairs, TbExtractor


class TestTbExtractor(unittest.TestCase):

    def setup(self):

        input_file = [os.path.join(BASE_DIR, "/test/data", "test.eng"),
                      os.path.join(BASE_DIR, "/test/data", "test.fra")]

        input_type = '2txt'
        output_rootpath = os.path.join(BASE_DIR, "test", "test_res")
        output_prefix = 'test_tbextractor'
        srcLang = 'eng'
        tgtLang = 'fra'

        self.tbe = TbExtractor(input_file, input_type,
                               output_rootpath, output_prefix,
                               srcLang=srcLang, tgtLang=tgtLang)

    def test_find_word_index_of_term(self):

        text_1 = "this method is awesome."
        term_1 = "this method"
        expected_res_1 = [[0, 1]]

        text_2 = "I think this test case works very well."
        term_2 = 'test case'
        expected_res_2 = [[3, 4]]

        text_3 = "I think different test cases can works very well."
        term_3 = 'different test cases'
        expected_res_3 = [[2, 3, 4]]

        text_4 = "I think this method can works very well and this method is awesome."
        term_4 = 'this method'
        expected_res_4 = [[2, 3], [9, 10]]

        text_5 = "I think this method can works very well and this method is awesome."
        term_5 = 'unrelated term'
        expected_res_5 = []

        self.assertEqual(find_word_index_of_term(text_1, term_1), expected_res_1)
        self.assertEqual(find_word_index_of_term(text_2, term_2), expected_res_2)
        self.assertEqual(find_word_index_of_term(text_3, term_3), expected_res_3)
        self.assertEqual(find_word_index_of_term(text_4, term_4), expected_res_4)
        self.assertEqual(find_word_index_of_term(text_5, term_5), expected_res_5)

    def test_find_terminology_pairs(self):

        src_line = "In the following examples the designated risk is the spot foreign exchange risk because the hedging instruments are not derivatives ."
        tgt_line = "Dans les exemples ci-dessous , le risque désigné est le risque de change au comptant parce que les instruments de couverture ne sont pas des dérivés ."
        forward_align = {0: [0], 1: [1], 2: [3], 3: [2], 4: [5], 5: [7], 6: [6], 7: [8], 8: [9], 9: [13, 14], 10: [12], 11: [12], 12: [10], 13: [15, 16], 14: [17], 15: [19, 20], 16: [18], 17: [22, 24], 18: [21, 23], 19: [25], 20: [26]}
        reverse_align = {0: [0], 1: [1], 3: [2], 2: [3], 5: [4], 7: [5], 6: [6], 8: [7], 9: [8], 13: [9], 14: [9], 12: [10, 11], 10: [12], 15: [13], 16: [13], 17: [14], 19: [15], 20: [15], 18: [16], 22: [17], 24: [17], 21: [18], 23: [18], 25: [19], 26: [20]}

        src_tgt_forward_alignment = {(src_line, tgt_line): forward_align}
        src_tgt_reverse_alignment = {(src_line, tgt_line): reverse_align}
        source_terms = ["designated risk"]

        expected_pairs= [("designated risk", "risque désigné")]
        pairs = find_terminology_pairs(src_tgt_forward_alignment, src_tgt_reverse_alignment, source_terms)

        self.assertEqual(pairs, expected_pairs)

    def teardown(self):
        self.input_file = None


if __name__ == '__main__':

    unittest.main()
