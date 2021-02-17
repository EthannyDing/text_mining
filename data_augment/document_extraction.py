import os
from configparser import ConfigParser
from ..apis.memsource import MemsourceJobs, MemsourceAPI
from ..tb_utils.mxliff_manager import removeMemsourceTag, extract_src_segment
from .html_text_process import HtmlTextProcess


class DocumentExtraction(HtmlTextProcess):
    """Process crawled files from website and extract segments from them using Memsource."""
    def __init__(self, configFile):
        cf = ConfigParser()
        cf.read(configFile)
        lang = cf.get("language", "lang")
        super().__init__(lang)

        username = cf.get("credential", "username")
        password = cf.get("credential", "password")
        projectID = cf.get("credential", "projectID")
        self.input_rootpath = cf.get("input", "input_rootpath")
        self.mxliff_rootpath = cf.get("output", "mxliff_rootpath")
        self.memsource_text_path = cf.get("output", "memsource_text_path")
        self.final_text_path = cf.get("output", "final_text_path")

        ma = MemsourceAPI()
        token = ma.getToken(username, password)

        self.mj = MemsourceJobs(memsourceAPI=ma, token=token, projectID=projectID, mdbinfo=None)
        self.fileImportSetting = {'html': {'convertNonHtml': True},
                                  'ppt': {'importNote': False}}
        if not os.path.exists(self.mxliff_rootpath):
            os.makedirs(self.mxliff_rootpath)

    def upload_file(self, filePath):
        self.mj.create_job(inputPath=filePath, fileImportSetting=None)

    def download_file(self):
        print("\tDownloading MXLIFF file.")
        file_name = self.mj.download_bilingual_file(self.mxliff_rootpath)
        return file_name

    def extract_segments(self, file):
        filePath = os.path.join(self.mxliff_rootpath, file)
        srcTexts = extract_src_segment(filePath, return_dataframe=False)

        return srcTexts

    def remove_memsourceTag(self, texts):

        texts = removeMemsourceTag(texts)
        texts = list(dict.fromkeys(texts))
        print("\t{} segments extracted.".format(len(texts)))

        return texts

    def save_text_locally(self, texts):
        """save extracted texts directly into local file."""
        with open(self.memsource_text_path, 'a') as f:
            for text in texts:
                f.write(text)

    def start_extraction(self):

        # input_files = [os.path.join(self.input_rootpath, file) for file in os.listdir(self.input_rootpath)]
        input_files = os.listdir(self.input_rootpath)
        print("Extracting segments from total {} files.".format(len(input_files)))

        for i, file in enumerate(input_files):

            print("\n{}/{} Extracting segments from {}".format(i+1, len(input_files), file))
            filePath = os.path.join(self.input_rootpath, file)
            try:
                self.upload_file(filePath)
                filename = self.download_file()
                self.mj.delete_job()

                srcTexts = self.extract_segments(filename)
                srcTexts = self.remove_memsourceTag(srcTexts)
                self.save_text_locally(srcTexts)

            except:
                print("Error occurred, skip this document.")

        final_res = self.start_text_process(self.memsource_text_path)
        with open(self.final_text_path, 'w') as f:
            for l in final_res:
                f.write(l.strip() + "\n")

        print("Done.")


def test_document_extraction():

    configPath = "alexa_text_mining/data_process/config/document_extraction.conf"
    de = DocumentExtraction(configPath)
    de.start_extraction()


if __name__ == "__main__":

    test_document_extraction()
