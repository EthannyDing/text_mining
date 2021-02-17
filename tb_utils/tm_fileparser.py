import os, codecs, sys
import pandas as pd, regex as re
from pathlib import Path
from bs4 import BeautifulSoup
from lxml import etree
# from .terms_io import loads_terms_from_pickle
base_dir = os.path.dirname(Path(__file__).parent.parent)
sys.path.append(base_dir)


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


def writeToTmxFile(outputPath, pairs, srcLang, tgtLang, segType='seg', encoding='utf8'):
    """Write to TMX (XML) file

       Args:
          outputPath (str): The path of the TMX file
          pairs (list): a list of (source_text, target_text) tuples
          segType (str): segment type, e.g., 'phrase'
          srcLang (str): source language code
          tgtLang (str): target language code
          encoding (str): the encoding method
    """

    try:
        soup = BeautifulSoup(features='xml')
        soup.append(soup.new_tag('tmx', version='1.4b'))

        # Write header
        header = soup.new_tag('header')
        header['creationtool'] = 'YappnTmxGenerator'
        header['creationtoolversion'] = '1.0.0.1905'
        header['o-tmf'] = 'TMX'
        header['adminlang'] = 'en'
        header['datatype'] = 'plaintext'
        header['segtype'] = segType
        header['srclang'] = srcLang
        tmx_tuTag = 'tu'
        tmx_tuPieceTag = 'tuv'
        tmx_textTag = 'seg'
        soup.tmx.append(header)

        # Write body
        soup.tmx.append(soup.new_tag('body'))

        for (src, tgt) in pairs:
            tu = soup.new_tag(tmx_tuTag)

            tuvSrc = soup.new_tag(tmx_tuPieceTag)
            tuvSrc['xml:lang'] = srcLang
            seg = soup.new_tag(tmx_textTag)
            seg.string = src
            tuvSrc.append(seg)

            tuvTgt = soup.new_tag(tmx_tuPieceTag)
            tuvTgt['xml:lang'] = tgtLang
            seg = soup.new_tag(tmx_textTag)
            seg.string = tgt
            tuvTgt.append(seg)

            tu.append(tuvSrc)
            tu.append(tuvTgt)

            soup.tmx.body.append(tu)

        with open(outputPath, 'wb') as f:
            f.write(soup.prettify().encode(encoding))

        return True

    except:

        return False


class TmFileParser(object):
    """This class is dedicated to parse TM from different types of TM files."""

    # 1, For TMX, MXLIFF and SDLXLIFF, verify the TM file, throw exception if:
    #   * source is empty, target is non-empty
    #   * source and target lengths not equal.
    # 2, For EXCEL, verify the TM file throw exception if following conditions aren't meet:
    #   * only one sheet in Excel file.
    #   * source and target TM are placed on first two columns
    #   * header are required, the header names of first and second columns are "Source" and "Target", case-insensitive,respectively.

    def __init__(self, fileType="tmx"):

        if fileType not in ["tmx", "mxliff", "excel", "sdlxliff", "2txt", "pickle", "xml"]:
            raise Exception("Only support tmx, mxliff, excel, sdlxliff, 2txt, pickle and xml.")
        # assert srcLang in ["eng", "fra"], "source language code must be either eng or fra."
        # assert tgtLang in ["eng", "fra"], "target language code must be either eng or fra."

        self.fileType = fileType

        self.srcTexts = []
        self.tgtTexts = []

    def parse_excel(self, file_dir):
        """Parse TM from excel file, only first columns are inspected and header included"""

        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext not in (".xlsx", ".xls"):
            raise Exception("please select a XLSX or XLS (Excel) file.")

        try:

            excel_file = pd.ExcelFile(file_dir)
            if len(excel_file.sheet_names) != 1:
                raise AssertionError("Only one sheet is allowed in Excel file.")
            del excel_file

            df = pd.read_excel(file_dir, dtype=str, na_filter=False)

            columns = list(df.columns)

            if len(columns) != 2:
                raise AssertionError("Source and target should be on the first two columns.")
            # if columns[0].lower() != "source":
            #     raise AssertionError("First column name is not 'source'.")
            # if columns[1].lower() != "target":
            #     raise AssertionError("Second column name is not 'target'.")

            try:
                self.srcTexts = [str(s).strip() for s in df[columns[0]]]
            except IndexError:
                raise IndexError("Source text column is missing.")
            try:
                self.tgtTexts = [str(s).strip() for s in df[columns[1]]]
            except IndexError:
                raise IndexError("Target text column is missing.")

            # if "" in self.srcTexts:
            #     raise AssertionError("Empty cell(s) exist in source column.")
            # if "" in self.tgtTexts:
            #     raise AssertionError("Empty cell(s) exist in target column.")

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "IndexError", "ImportError"):
                raise Exception(ex.__str__())
            print(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")

    def parse_tmx(self, file_dir, textTag="seg", pairTag="tu", tmxHasAlignedFilenames=False):
        """parse TM from TMX file.
           Note: this function will only extract valid TM (source and target text both exist)."""

        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext != ".tmx":
            raise AssertionError("Please select a TMX file.")

        try:

            try:
                with open(file_dir, 'rb') as f:
                    raw = f.read()

                soup = BeautifulSoup(raw, 'lxml')

            except:
                raise ImportError("TMX cannot be opened.")

            for i, tu in enumerate(soup.findAll(pairTag)):

                pair = tu.findAll(textTag)
                if len(pair) == 2:
                    #self.srcTexts.append(re.sub(r'\s+', ' ', pair[0].text))
                    #self.tgtTexts.append(re.sub(r'\s+', ' ', pair[1].text))
                    self.srcTexts.append(pair[0].text.strip())
                    self.tgtTexts.append(pair[1].text.strip())

                # else:
                #     raise AssertionError("#%d tu tag doesn't contain both source and target text" % i)

            if tmxHasAlignedFilenames:
                self.srcTexts = self.srcTexts[1:]
                self.tgtTexts = self.tgtTexts[1:]

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "ImportError"):
                raise Exception(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")

    def parse_mxliff(self, file_dir):
        """extract pairs from Memsource bilingual mxliff file based on trans-origin type."""

        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext != ".mxliff":
            raise AssertionError("Please select a MXLIFF file.")

        try:

            try:
                parser = etree.XMLParser(strip_cdata=False)
                doc = etree.parse(file_dir, parser)
            except:
                raise ImportError("MXLIFF cannot be opened.")

            xmlNamespace = '{' + doc.getroot().nsmap[None] + '}'
            transNodes = doc.findall('.//' + xmlNamespace + "trans-unit")

            for i, trans_unit in enumerate(transNodes):

                if trans_unit is not None:

                    src_node = trans_unit.find('.//' + xmlNamespace + "source")  # layer 3
                    tgt_node = trans_unit.find('.//' + xmlNamespace + "target")

                    if (src_node is not None) and (tgt_node is not None):
                        if (src_node.text is not None) and (tgt_node.text is not None):
                            self.srcTexts.append(re.sub(r'\s+', ' ', src_node.text).strip())
                            self.tgtTexts.append(re.sub(r'\s+', ' ', tgt_node.text).strip())

                        else:
                            raise AssertionError("Source or target text is empty in #%d trans-unit tag." % i)

                    else:
                        raise AssertionError("#%d trans-unit doesn't contain both source and target text." % i)

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "ImportError"):
                raise Exception(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")

    def parse_sdlxliff(self, file_dir, sdlTgtTagName="mrk"):
        """Parse TM from SDLXliff file"""

        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext != ".sdlxliff":
            raise AssertionError("Please select a SDLXliff file.")

        try:

            try:
                parser = etree.XMLParser(strip_cdata=False)
                doc = etree.parse(file_dir, parser)

            except:
                raise ImportError("SDLXLIFF cannot be opened.")

            xmlNamespace = '{' + doc.getroot().nsmap[None] + '}'
            transNodes = doc.findall('.//' + xmlNamespace + "trans-unit")

            for i, trans_unit in enumerate(transNodes):

                if trans_unit is not None:
                    try:
                        src_node = trans_unit.find('.//' + xmlNamespace + "source")  # layer 3
                    except:
                        raise IndexError("#%d trans-unit tag doesn't contain source tag." % i)
                    try:
                        tgt_node = trans_unit.find('.//' + xmlNamespace + "target").find('.//' + xmlNamespace + sdlTgtTagName)
                    except:
                        raise IndexError("#%d trans-unit tag doesn't contain target tag." % i)

                    if (src_node is not None) and (tgt_node is not None):
                        if (src_node.text is not None) and (tgt_node.text is not None):
                            self.srcTexts.append(re.sub(r'\s+', ' ', src_node.text).strip())
                            self.tgtTexts.append(re.sub(r'\s+', ' ', tgt_node.text).strip())

                        else:
                            raise AssertionError("Source or target text is empty in #%d trans-unit tag." % i)

                    else:
                        raise AssertionError("#%d trans-unit doesn't contain both source and target text." % i)

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "ImportError", "IndexError"):
                raise Exception(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")

    def parse_2txt(self, file_dir):
        """Parse TM from 2txt file"""

        if len(file_dir) != 2:
            raise Exception("please select 2txt files.")

        src_file, tgt_file = file_dir[0], file_dir[1]

        try:
            with codecs.open(src_file, 'r') as f:
                self.srcTexts = f.readlines()

            with codecs.open(tgt_file, 'r') as f:
                self.tgtTexts = f.readlines()

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "IndexError", "ImportError"):
                raise Exception(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")

    def parse_pickle(self, file_dir):
        """Parse TM from pickle file that contains dataframe object with 'source' and 'target' column."""

        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext != ".pkl":
            raise AssertionError("Please select a pickle file.")

        data = loads_terms_from_pickle(file_dir)
        try:
            self.srcTexts = data['source'].tolist()
            self.tgtTexts = data['target'].tolist()
        except Exception as ex:
            raise Exception(ex.__str__())

    def parse_xml(self, file_dir, xml_seg='seg', src_tag="src", tgt_tag="tgt"):
        
        base, filename = os.path.split(file_dir)
        prefix, ext = os.path.splitext(filename)

        if ext != ".xml":
            raise AssertionError("Please select a XML file.")

        try:

            try:
                parser = etree.XMLParser(strip_cdata=False)
                doc = etree.parse(file_dir, parser)
            except:
                raise ImportError("MXLIFF cannot be opened.")

            # xmlNamespace = '{' + doc.getroot().nsmap[None] + '}'
            xmlNamespace = "{}"
            bi_segs = doc.findall('.//' + xmlNamespace + xml_seg)

            for i, seg in enumerate(bi_segs):

                if seg is not None:

                    src_node = seg.find('.//' + xmlNamespace + src_tag)  # layer 3
                    tgt_node = seg.find('.//' + xmlNamespace + tgt_tag)

                    if (src_node is not None) and (tgt_node is not None):
                        if (src_node.text is not None) and (tgt_node.text is not None):
                            self.srcTexts.append(re.sub(r'\s+', ' ', src_node.text).strip())
                            self.tgtTexts.append(re.sub(r'\s+', ' ', tgt_node.text).strip())

                    else:
                        raise AssertionError("#%d trans-unit doesn't contain both source and target text." % i)

        except Exception as ex:
            if type(ex).__name__ in ("AssertionError", "ImportError"):
                raise Exception(ex.__str__())
            raise Exception("Unidentified error occurred during parsing.")
    
    
    def parse(self, file_dir, textTag="seg", tmxHasAlignedFilenames=False, sdlTgtTagName="mrk"):
        """parse TM files and source text and target text are in self.srcTexts and self.tgtTexts."""

        if self.fileType == "excel":
            self.parse_excel(file_dir)

        if self.fileType == "tmx":
            self.parse_tmx(file_dir, textTag=textTag, tmxHasAlignedFilenames=tmxHasAlignedFilenames)

        if self.fileType == "mxliff":
            self.parse_mxliff(file_dir)

        if self.fileType == "sdlxliff":
            self.parse_sdlxliff(file_dir, sdlTgtTagName=sdlTgtTagName)

        if self.fileType == "2txt":
            self.parse_2txt(file_dir)

        if self.fileType == "pickle":
            self.parse_pickle(file_dir)
            
        if self.fileType == "xml":
            self.parse_xml(file_dir)

        # print(self.srcTexts[:5])
        # print(self.tgtTexts[:5])

        # verify if lengths are equal on both sides
        if len(self.srcTexts) != len(self.tgtTexts):
            print("length of src text: {} \nlength of tgt text: {}".format(len(self.srcTexts), len(self.tgtTexts)))
            raise Exception("Lengths of source and target TM not equal.")

        # final_pairs = [p for p in zip(self.srcTexts, self.tgtTexts) if p[0] and p[1]]
        # self.srcTexts = [p[0] for p in final_pairs]
        # self.tgtTexts = [p[1] for p in final_pairs]

        print("\n\tThe number of TM pairs parsed: {}".format(len(self.srcTexts)))


def test_TmParser():

    tfp = TmFileParser(fileType="2txt")

    mxliff = r"E:\Ethan_Github\TM_Operations\TM_fileTypes\mxliff\sample.mxliff"
    tmx = r"E:\Ethan_Github\TM_Operations\TM_fileTypes\tmx\sample.tmx"
    excel = r"E:\Ethan_Github\TM_Operations\TM_fileTypes\excel\sample.xlsx"
    sdlxliff = r"E:\Ethan_Github\TM_Operations\TM_fileTypes\sdlxliff\incorrect_sample2.sdlxliff"
    xml = r'C:\Users\Ethan\Downloads\565-200714-002_CA22007E_Webinar_Week 3.xml'

    tfp.parse(xml)


def test_TmUploader():

    username = "Ethan"
    password = "ethandingtest"
    tmp_tmx_rootpath = "./test/tmp"
    tu = TmUploader(username, password, tmp_tmx_rootpath)

    # dict = {"tm_name": "test_tm_uploader",
    #         "tm_id": None,
    #         "srcTexts": ["second one", "third one"],
    #         "tgtTexts": ["deuxième", "le troisième"],
    #         "srcLang": "en",
    #         "tgtLang": "fr"
    #         }

    dict = {"tm_name": "test_tm_uploader2",
            "tm_id": str(1118563),
            "srcTexts": ["fourth one"],
            "tgtTexts": ["quatrième rang"],
            "srcLang": "en",
            "tgtLang": "fr"
            }

    res = tu.UploadTM(dict)
    print(res)

if __name__ == "__main__":

    # test()
    test_TmParser()
