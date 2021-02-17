import os, time, pandas as pd, re, codecs
import requests, warnings
import urllib, urllib.request
from openpyxl import load_workbook
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from configparser import ConfigParser
from queue import Queue, Empty
from threading import Thread
from functools import lru_cache
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException
from html_crawler import CanliiCrawler, BrowserBasedCrawler
from utils.language_resources import Codes
NAME_YAPPN_MAPPINGS = Codes.mappings('name', 'yappn')
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')


@lru_cache(maxsize=128)
def get_response(url):
    """Access the url and get response, use cache to speed up crawling (avoid accessing same url via internet twice)"""
    res = None
    try:
        res = requests.get(url, allow_redirects=False)
        # res = requests.get(url, allow_redirects=True)
    except:
        print("Page failed to open: {}".format(url))
    return res


def _save_document(url_endpoint, save_path):
    """download URL content given url."""

    try:
        r = get_response(url_endpoint)
        if r:
            with open(save_path, 'wb') as f:
                f.write(r.content)
    except Exception as ex:
        print("Exception occurred during saving: {}".format(ex.__str__()))


def _save_urls(urls, columns, outputExcel, sheetname):
    """Save final monolingual/bilingual URLs."""
    writer = pd.ExcelWriter(outputExcel, engine='openpyxl')
    if os.path.exists(outputExcel):   # if file exists, add new sheet to that excel.
        book = load_workbook(outputExcel)
        writer.book = book

    df = pd.DataFrame(list(urls), columns=columns)
    df.to_excel(writer, sheet_name=sheetname, index=None)
    writer.save()
    writer.close()


def extract_text(soup):
    """extract text content from soup."""
    for script in soup(["script", "style"]):
        script.decompose()
    texts = list(dict.fromkeys([re.sub(r'\s+', ' ', text).strip() + '\n' for text in soup.stripped_strings]))
    return texts


def get_soup(src_url):
    """Get soup from given URL.
        Return:
             None if returned response is either unable to open or redirected.
             soup, otherwise."""
    soup = None
    try:
        res = get_response(src_url)
        if res.url == src_url and res.status_code == 200:
            soup = BeautifulSoup(res.content, features="html.parser")
    except:
        print("Page failed to open: {}".format(src_url))

    return soup


class BilingualCrawler(Thread):
    """Usage guideline in YDC.conf:

        1. specify Lang1 and Lang2, username and password if exists.
        2. inspect website and specify text, lang, hreflang, title of Lang1 and Lang2.
        3. set home_url as the homepage URL
        4. set head_url as the homepage URL of Lang1.

        Note: if crawling finishes as soon as program starts, try comment out line 320-322 and uncomment 323 & 324"""

    def __init__(self, cf):

        Thread.__init__(self)
        self.queue = Queue()
        self.visited = set()
        self.bilingual_url_pairs = set()
        self.pdf_links = set()

        self.start_url = cf.get("URL", "start_url")
        self.src_head = cf.get("URL", "src_head")
        self.tgt_head = cf.get("URL", "tgt_head")

        self.Lang1 = cf.get("Languages", "Lang1")
        self.Lang2 = cf.get("Languages", "Lang2")

        self.root_output = cf.get("Output", "root_output")
        self.url_list = cf.get("Output", "url_list")

        self.unwantedFormats = ["." + f for f in cf.get("Conditions", "unwantedFormat").split("|")]
        self.includeQuery = cf.getboolean("Conditions", "includeQuery")
        # self.SearchByHref = cf.getboolean("SearchMethod", "byhref")
        # # self.SearchByRule = cf.getboolean("SearchMethod", "byrule")
        # if self.SearchByHref:
        self.attributes = {key: value for key, value in cf._sections['SearchByHref_attr'].items()
                           if value != ""}
        self.attributes["href"] = True
        self.text = cf.get("SearchByHref_text", "text")
        print(self.attributes)
        # else:
        #     assert self.SearchByRule is True, 'Make sure one of the crawling methods is True.'
        #     self.srcUrlRegex = cf.get("SearchByRule", "srcUrlRegex")
        #     self.tgtUrlRegex = cf.get("SearchByRule", "tgtUrlRegex")

        self.queue.put(self.start_url)

        if not os.path.exists(self.root_output):
            os.makedirs(os.path.join(self.root_output, self.Lang1))
            os.makedirs(os.path.join(self.root_output, self.Lang2))

    def save_crawled_urls(self):
        """Save bilingual and PDF URLs."""
        html_columns = ["source", "target"]
        pdf_columns = ["source"]
        _save_urls(self.bilingual_url_pairs, html_columns, self.url_list, sheetname="html")
        _save_urls(self.pdf_links, pdf_columns, self.url_list, sheetname="pdf")

    def get_abs_url(self, href, source_url=True):
        """Get absolute URL.
            If source_url is True, parsed href will join with source head url,
            If source_url is False, parsed href will join with target head url.
        """

        if source_url:
            # head_url = self.src_head[:-1] if self.src_head[-1] == '/' else self.src_head
            head_url = self.src_head
            counter_lang_url = self.tgt_head
        else:
            # head_url = self.tgt_head[:-1] if self.tgt_head[-1] == '/' else self.tgt_head
            head_url = self.tgt_head
            counter_lang_url = self.src_head
            
        abs_url = urljoin(head_url, href)
        abs_url = urldefrag(abs_url).url.__str__()    # remove fragment in url.

        head_url = head_url[:-1] if head_url[-1] == '/' else head_url
        counter_lang_url = counter_lang_url[:-1] if counter_lang_url[-1] == '/' else counter_lang_url

        if head_url == counter_lang_url and abs_url.startswith(head_url):
            return abs_url
        elif head_url != counter_lang_url and abs_url.startswith(head_url) and (not abs_url.startswith(counter_lang_url)):
            return abs_url
        else:
            return None

        # if not abs_url.startswith(head_url):
        #     return None
        # else:
        #     return abs_url

    def add_new_urls_from_soup(self, soup, exclude_tgt_url):
        """Find all urls from the soup and add , excluding certain urls that end with e.g. .jpg, .aspx ..."""

        for anchor in soup.find_all('a', href=True):

            href = anchor['href']
            abs_url = self.get_abs_url(href, source_url=True)
            if abs_url:
                path = abs_url.split('/')[-2] if abs_url.split('/')[-1] == "" else abs_url.split('/')[-1]

                if any([path.endswith(uf) for uf in self.unwantedFormats]):
                    continue  # skip adding this URL if they ends with any of those unwanted formats.

                if not self.includeQuery and ("?" in path):
                    continue

                if path.lower().endswith('.pdf'):
                    self.pdf_links.add(abs_url)  # add pdf link
                    continue

                # Make sure new URL is not visited and not in current queue.
                if (abs_url not in self.visited) and (abs_url not in list(self.queue.queue)) and (abs_url not in exclude_tgt_url):
                    self.queue.put(abs_url)  # add new-founded URLs to queue

    def assign_parallel_path(self, pair, num):
        """Name parallel documents based on its URLs and save"""

        query = pair[0].split('/')[-2] if pair[0].split('/')[-1] == "" else pair[0].split('/')[-1]

        prefix, txt = os.path.splitext(query)
        if txt:  # if URL is ends with file extension, save it as the same extension, else save as html.
            l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_" + self.Lang1.upper() + txt
            l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_" + self.Lang2.upper() + txt
        else:
            l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_" + self.Lang1.upper() + ".html"
            l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_" + self.Lang2.upper() + ".html"

        l1_dir = os.path.join(self.root_output, self.Lang1, l1_name)
        l2_dir = os.path.join(self.root_output, self.Lang2, l2_name)
        
        return l1_dir, l2_dir

        # _save_document(pair[0], l1_dir)
        # _save_document(pair[1], l2_dir)

    def find_url_pairs_by_rule(self, src_url: str):

        base, last = os.path.split(src_url.__str__())
        fra_last = last

        if base + "/" == self.src_head:
            fra_url = self.tgt_head + fra_last

        else:
            body = base.replace(self.src_head, "")
            fra_body = body

            fra_url = self.tgt_head + fra_body + '/' + fra_last

        pair = (src_url, fra_url)

        try:

            page = urllib.request.urlopen(src_url).read()
            soup = BeautifulSoup(page, features="lxml")
            soup.prettify()
            # page = requests.get(host_url, auth=(self.username, self.password)).content
            # soup = BeautifulSoup(page, features="html.parser", from_encoding="iso-8859-1")
            return pair, soup

        except:
            return None, None

    def find_url_pairs_by_href(self, src_url: str):

        # if src_url.lower().endswith(".pdf"):
        #     # pdf_filename = src_url.lower().split("/")[-1]
        #     self.pdf_links.add(src_url)
        #     return None, None

        soup = get_soup(src_url)
        new_pair = None
        if soup:
            # Find the counterpart url of target language.
            try:
                tgt_href = soup.find('a', self.attributes, text=self.text)['href']
                tgt_url = self.get_abs_url(tgt_href, source_url=False)
            except TypeError as ex:
                tgt_url = None

            if tgt_url:
                new_pair = (src_url, tgt_url)

        return new_pair, soup

    def crawl(self):

        downloads = 0
        # find_url_pairs = self.find_url_pairs_by_href if self.SearchByHref else self.find_url_pairs_by_rule
        try:
            while True:

                src_url = self.queue.get_nowait()
                new_pair, soup = self.find_url_pairs_by_href(src_url)
                self.visited.add(src_url)

                if (new_pair is None) or (soup is None):
                    print("No pairs found or url cannot be opened for {}".format(src_url))
                    continue    # skip if host_url cannot opened or no pair found.

                # Save bilingual pages if they are new
                if new_pair not in self.bilingual_url_pairs:

                    self.add_new_urls_from_soup(soup, exclude_tgt_url=new_pair[1])  # 1. update queue with new urls from the current page.

                    print("\n\tSaving page of Lang1: {}".format(new_pair[0]))
                    print("\tSaving page of Lang2: {}\n".format(new_pair[1]))
                    l1_dir, l2_dir = self.assign_parallel_path(new_pair, downloads)
                    _save_document(new_pair[0], l1_dir)
                    _save_document(new_pair[1], l2_dir)
                    
                    self.bilingual_url_pairs.add(new_pair)
                    downloads += 1  # record the number of downloaded files, not necessarily accurate.

                print("\tTotal number of pairs is saved: {}".format(downloads))
                print("\tTotal number of URLs in queue: {}".format(self.queue.qsize()))

        except Empty:
            pass

    def run(self):

        start = time.time()
        workers = []
        max_threads = os.cpu_count()
        for i in range(max_threads):
            print('starting worker {}...'.format(i))
            worker = Thread(target=self.crawl)
            worker.start()
            workers.append(worker)

        # this would wait all threads to complete.
        for worker in workers:
            worker.join()

        # html_columns = ["source", "target"]
        # pdf_columns = ["source"]
        # _save_urls(self.bilingual_url_pairs, html_columns, self.url_list, sheetname="html")
        # _save_urls(self.pdf_links, pdf_columns, self.url_list, sheetname="pdf")
        self.save_crawled_urls()

        duration = time.time() - start
        print("Total time consumed: {} min".format(round(duration/60, 1)))


class DynamicBilingualCrawler(BilingualCrawler):

    def __init__(self, cf):
        super().__init__(cf)

        self.executable_path = cf.get("SearchBySelenium", "chrome_executable_path")
        self.tgt_xpath = cf.get("SearchBySelenium", "tgt_xpath")

        self.login_required = cf.getboolean("Login", "login_required")
        self.username = cf.get("Login", "username")
        self.password = cf.get("Login", "password")
        self.steps = cf.get("Login", "steps")

        self.global_lang_switcher = cf.getboolean("GlobalLanguageSwitcher", "global_lang_switcher")
        self.src_xpath = cf.get("GlobalLanguageSwitcher", "src_xpath")

        self.delay = cf.getint("Conditions", "page_delay")
        self.driver = None
        self.setup()

        if self.login_required:
            self.login_mainpage()

    def login_mainpage(self):
        """Login to main page if it requires additional steps to access it."""
        steps = [tuple(step.split("&&")) for step in self.steps.split("|||")]
        print("Logging into main page...")

        self.driver.get(self.start_url)
        for action, xpath in steps:
            matchedElement = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if action == "click":
                matchedElement.click()
            elif action == "enter_username":
                matchedElement.clear()
                matchedElement.send_keys(self.username)
            elif action == "enter_password":
                matchedElement.clear()
                matchedElement.send_keys(self.password)
            else:
                raise Exception("No action: {} found.".format(action))

        print("Logged in.")

    def setup(self):
        """Set up selenium options."""
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")  # prevent interactable error if browser is not maximized.
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(executable_path=self.executable_path, chrome_options=options)

    def download_page(self, content, file_path):
        """Downlaod page and save it to specified file path."""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as ex:
            print("Exception occurred while saving file: {}".format(ex.__str__()))

    def switch_global_source_lang(self):
        """Switch the global langugae to source langugae."""

        print("Switching global langugae to: {}".format(self.Lang1))
        try:
            src_lang_node = WebDriverWait(self.driver, self.delay).until(
                            EC.presence_of_element_located((By.XPATH, self.src_xpath)))

        except Exception as ex:
            print("Switch to gloabl source langugae failed: {}".format(ex.__str__()))
            print("Opening starting source URL and switching to source language...")
            self.driver.get(self.start_url)
            src_lang_node = WebDriverWait(self.driver, self.delay).until(
                            EC.presence_of_element_located((By.XPATH, self.src_xpath)))
        finally:
            if src_lang_node.is_displayed():
                # directly click the element if it's clickable.
                src_lang_node.click()
            else:
                # apply JavaScript code to click invisible/unclickable element.
                self.driver.execute_script("arguments[0].click();", src_lang_node)

    def find_bilingual_content_url(self, tgt_lang_node):
        """Find content and URL from both source and target language page
            tgt_lang_node: target button that driver found.
            """
        try:
            src_content = self.driver.page_source
            src_url = self.driver.current_url

            if tgt_lang_node.is_displayed():
                # directly click the element if it's clickable.
                tgt_lang_node.click()
            else:
                # apply JavaScript code to click invisible/unclickable element.
                self.driver.execute_script("arguments[0].click();", tgt_lang_node)

            tgt_content = self.driver.page_source
            tgt_url = self.driver.current_url

        except Exception as ex:
            print("\tException occured: {}".format(ex.__str__()))
            return None, None, None, None

        return src_content, src_url, tgt_content, tgt_url

    def crawl(self):
        """ Main function, call it to start crawling
        :param delay: the number of seconds of waiting of driver to find the button that directs to target page.
        """
        start = time.time()
        downloads = 0
        try:
            while True:

                src_url = self.queue.get_nowait()
                self.visited.add(src_url)

                try:
                    if self.login_required:  # skip open start url if it's logged in.
                        self.login_required = False
                        tgt_lang_node = self.driver.find_element_by_xpath(self.tgt_xpath)
                    else:
                        self.driver.get(src_url)
                        tgt_lang_node = WebDriverWait(self.driver, self.delay).until(
                                        EC.presence_of_element_located((By.XPATH, self.tgt_xpath)))
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")

                except InvalidSessionIdException as ex:
                    print("Webdriver session deleted, restarting new session now.")
                    self.setup()
                    continue
                except Exception as ex:
                    print("\tException: {}, message: {}.".format(type(ex).__name__, ex.__str__()))
                    print("\tProblematic URL: {}".format(src_url))
                    continue

                # if target page found, download both source and target page.
                src_content, src_url, tgt_content, tgt_url = self.find_bilingual_content_url(tgt_lang_node)
                if src_content == src_url == tgt_content == tgt_url is None:
                    print("Error occurred on target element, skipping to next page.")
                    continue

                l1_dir, l2_dir = self.assign_parallel_path((src_url, tgt_url), downloads)
                print("\n\tSaving page of Lang1: {}".format(src_url))
                print("\tSaving page of Lang2: {}\n".format(tgt_url))
                self.download_page(src_content, l1_dir)
                self.download_page(tgt_content, l2_dir)
                downloads += 1

                # update queue with new urls from the current source page.
                self.add_new_urls_from_soup(soup, exclude_tgt_url=tgt_url)
                self.bilingual_url_pairs.add((src_url, tgt_url))

                print("\tTotal number of pairs is saved: {}".format(downloads))
                print("\tTotal number of URLs in queue: {}".format(self.queue.qsize()))

                # Swtich the global language to source language.
                if self.global_lang_switcher:
                    self.switch_global_source_lang()

        except Empty:
            pass

        self.save_crawled_urls()
        duration = time.time() - start
        print("Total time consumed: {} min".format(round(duration/60, 1)))


class GeneralBilingualCrawler:

    def __init__(self, configPath):

        self.cf = ConfigParser()
        self.cf.read(configPath)
        self.request_based = self.cf.getboolean("SearchMethod", "request_based")
        self.selenium_based = self.cf.getboolean("SearchMethod", "selenium_based")

    def crawl(self):

        if self.request_based:
            bc = BilingualCrawler(self.cf)
            bc.run()

        elif self.selenium_based:
            dbc = DynamicBilingualCrawler(self.cf)
            dbc.crawl()

        else:
            raise Exception("Choose one crawling method!")


class MonolingualCrawler(Thread):
    """Crawl texts from monolingual websites.
        Notes:
            1. Before crawling, it's better to observe the website to see if it's multilingual,
                                if so, add a regex pattern of URLs of other languages, excludeTgtRegex.
            2. So far only HTML documents will be processed to extract texts.
            3. Three files will be generated. Excel: list of URLs,
                                              Raw.txt: crawled and merged text without processing,
                                              Refine.txt: processed text, so far only de-depulicate.
            """
    def __init__(self, cf):

        Thread.__init__(self)
        self.queue = Queue()
        self.visited = set()

        self.start_url = cf.get("URL", "start_url")
        self.src_head = cf.get("URL", "src_head")
        self.Lang = cf.get("Languages", "Lang")

        self.root_output = cf.get("Output", "root_output")
        self.url_list = cf.get("Output", "url_list")
        self.extracted_raw_dir = os.path.join(self.root_output, "extracted.raw." + self.Lang)
        self.extracted_refine_dir = os.path.join(self.root_output, "extracted.refine." + self.Lang)

        self.unwantedFormats = ["." + f for f in cf.get("Conditions", "unwantedFormat").split("|")]
        self.excludeTgtRegex = cf.get("Conditions", "excludeTgtRegex")
        self.queue.put(self.start_url)

        if not os.path.exists(self.root_output):
            os.makedirs(self.root_output)

    def save_text_locally(self, texts):
        """save extracted texts directly into local file."""
        with open(self.extracted_raw_dir, 'a') as f:
            for text in texts:
                f.write(text)

    def finalize_texts(self):
        """Reopen extracted raw text file and refine text.
            e.g. de-duplicate. Further text modification can be performed here."""
        with codecs.open(self.extracted_raw_dir, 'r') as f:
            raw_texts = f.readlines()

        dedup_texts = list(dict.fromkeys(raw_texts))  # de-duplicate
        with codecs.open(self.extracted_refine_dir, 'w') as f:
            f.writelines(dedup_texts)

    def get_abs_url(self, href):
        """Get absolute URL. parsed href will join with source head url"""
        # head_url = self.src_head[:-1] if self.src_head[-1] == '/' else self.src_head

        abs_url = urljoin(self.src_head, href)
        abs_url = urldefrag(abs_url).url.__str__()    # remove fragment in url.

        head_url = self.src_head[:-1] if self.src_head[-1] == '/' else self.src_head
        if not abs_url.startswith(head_url):
            return None
        else:
            return abs_url

    def add_new_urls_from_soup(self, soup):
        """Find all urls from the soup and add , excluding certain urls that end with e.g. .jpg, .aspx ..."""

        for anchor in soup.find_all('a', href=True):

            href = anchor['href']
            abs_url = self.get_abs_url(href)
            if abs_url:
                query = abs_url.split('/')[-2] if abs_url.split('/')[-1] == "" else abs_url.split('/')[-1]

                if any([query.endswith(uf) for uf in self.unwantedFormats]):
                    continue  # skip adding this URL if they ends with any of those unwanted formats.

                # Make sure new URL is not visited and not in current queue.
                if (abs_url not in self.visited) and (abs_url not in list(self.queue.queue)) and \
                        (re.match(self.excludeTgtRegex, abs_url) is None):
                    self.queue.put(abs_url)  # add new-founded URLs to queue

    def crawl(self):

        extracted = 0
        try:
            while True:

                src_url = self.queue.get_nowait()
                soup = get_soup(src_url)
                self.visited.add(src_url)

                if soup is None:
                    continue    # skip if host_url cannot opened.

                self.add_new_urls_from_soup(soup)  # 1. update queue with new urls from the current page.

                print("\n\tExtracting texts from: {}".format(src_url))
                texts = extract_text(soup)  # 2. add new texts to local file instead of memory.
                self.save_text_locally(texts)
                extracted += 1  # record the number of downloaded files, not necessarily accurate.

                print("\tTotal number of URLs in queue: {}".format(self.queue.qsize()))
                print("\tNumber of URL from which texts are extracted: {}".format(extracted))

        except Empty:
            pass

    def run(self):

        start = time.time()
        workers = []
        max_threads = os.cpu_count()
        for i in range(max_threads):
            print('starting worker {}...'.format(i))
            worker = Thread(target=self.crawl)
            worker.start()
            workers.append(worker)

        # this would wait all threads to complete.
        for worker in workers:
            worker.join()

        print("\nSaving visited URLs")
        columns = ['Visited URL']
        _save_urls(self.visited, columns, self.url_list)

        print("Refining extracted texts ...")
        self.finalize_texts()

        print("Done.")
        duration = time.time() - start
        print("Total time consumed: {} min".format(round(duration/60, 1)))


class CanliiMonolingualCrawler(CanliiCrawler):
    """Crawl monolingual data from Canlii monolingual URLs."""

    def __init__(self, configPath):

        super().__init__(configPath)
        self._cf.read(self._inputConfigPath)

        prefix = self._cf.get('monolingual', 'prefix')
        self.monolingual_url_path = self._cf.get('monolingual', 'monolingual_url_path')
        self.rootPath = self._cf.get('output', 'crawl_root_path')

        self.engTextPath = os.path.join(self.rootPath, prefix + '.eng')
        self.fraTextPath = os.path.join(self.rootPath, prefix + '.fra')
        self.engPdfUrlPath = os.path.join(self.rootPath, prefix + '.pdf_urls.eng')
        self.fraPdfUrlPath = os.path.join(self.rootPath, prefix + '.pdf_urls.fra')

        self._setup()
        self._configChromeDriver(downloadPath=self.pdf_rootpath)

    def _setup(self):

        self.text_content_name = 'div'
        self.text_content_id = 'originalDocument'
        self.pdf_id = 'pdf-viewer'
        self.pdf_link_xpath = '//div[@id="metas"]/div[1]/div/div/a'

        self.pdf_rootpath = os.path.join(self.rootPath, 'pdf')
        if not os.path.exists(self.pdf_rootpath):
            os.makedirs(self.pdf_rootpath)

        srcpath = os.path.join(self.rootPath, NAME_YAPPN_MAPPINGS[self.sourceLang])
        tgtpath = os.path.join(self.rootPath, NAME_YAPPN_MAPPINGS[self.targetLang])
        os.rmdir(srcpath)
        os.rmdir(tgtpath)

    def append_pdf_url(self, url, lang):
        print("\t\tSaving {} PDF URL: {}".format(lang, url))
        textPath = self.engPdfUrlPath if lang == 'en' else self.fraPdfUrlPath
        with open(textPath, 'a') as f:
            f.write(url + '\n')

    def append_text(self, texts, lang):

        print("\t\tSaving {} segments".format(len(texts)))
        textPath = self.engTextPath if lang == 'en' else self.fraTextPath
        with open(textPath, 'a') as f:
            for text in texts:
                f.write(text)

    def read_line(self, text_path):
        """A generator to read lines from large text file for memory efficient purpose."""
        for r in open(text_path, 'r'):
            yield r

    def finalize_text(self, text_dir):

        try:
            with codecs.open(text_dir, 'r') as f:
                raw_texts = f.readlines()

            # de-duplicate and filter out segments with single token.
            dedup_texts = list(filter(lambda x: len(x.split()) > 1, dict.fromkeys(raw_texts)))
            print("\nAfter deduplicating, file {} has {} segments".format(text_dir, len(dedup_texts)))
            with codecs.open(text_dir, 'w') as f:
                f.writelines(dedup_texts)
        except Exception as ex:
            print("Error occurred during finalizing texts: {}".format(ex.__str__()))

    def download_pdf(self, delay=10):
        """Download PDF file from the page if texts in webpage is in pdf format."""
        try:
            pdf_link = WebDriverWait(self.driver, delay).until(
                EC.element_to_be_clickable((By.XPATH, self.pdf_link_xpath)))
            pdf_link.click()

        except:
            print("\t\tDownloading PDF failed.")

    def access_page(self, url, delay=3):
        """Get soup from given URL while save captcha images and its texts.
        """
        self.driver.get(url)

        if self.driver.title == self._captchaTitle:
            print('\t**Solving captcha ...')
            self._solveCaptcha()
            self.access_page(url)
        else:
            try:
                contentNode = WebDriverWait(self.driver, delay).until(
                    EC.presence_of_element_located((By.ID, self.text_content_id)))
            except:
                pass

    def determine_format(self, soup):
        """Determine if text in the webpage is in PDF or Word format.
           Return:
                 1. type: 'pdf' or 'word'
                 2. text_section_names: original content soup if text type is word, None if pdf."""
        try:
            originalDoc = soup.find(self.text_content_name, {'id': self.text_content_id})
            type = None
            content_soup = None
            if originalDoc:
                isPDF = originalDoc.find(self.text_content_name, {'id': self.pdf_id})
                if isPDF:
                    type = 'pdf'
                else:
                    type = 'word'
                    content_soup = originalDoc
        except:
            print("\t\tSoup is empty")
            return None, None

        return type, content_soup

    def crawl(self):

        mono_urls = self.read_line(self.monolingual_url_path)
        for i, url in enumerate(mono_urls):
            print("\n\t{}. Crawling content from: {}".format(i + 1, url))
            try:
                url = url.strip()
                lang = url.split("/")[3]

                # soup = get_soup(url)
                self.access_page(url)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                type, content_soup = self.determine_format(soup)

                if type == 'pdf':
                    self.append_pdf_url(url, lang)  # save pdf-text url
                    self.download_pdf()             # download pdf file

                elif type == 'word':
                    texts = extract_text(content_soup)  # direcly extract texts
                    self.append_text(texts, lang)
                else:
                    print("\t\tNo original document content found.")

            except:
                print("\t\tUnexpected Error occurred, skip this page.")

        self.finalize_text(self.engTextPath)
        self.finalize_text(self.fraTextPath)
        print("\nDone.")


def test_crawl_bilingual():

    configPath = "./config/bilingual_crawl.conf"
    cf = ConfigParser()
    cf.read(configPath)

    pc = BilingualCrawler(cf)
    pc.run()

def test_crawl_monolingual():

    configPath = "./config/monolingual_crawl.conf"
    cf = ConfigParser()
    cf.read(configPath)

    mc = MonolingualCrawler(cf)
    mc.run()

def test_CanliiMonolingualDownloader():
    rootOutput = "./config/crawlers_canlii.conf"
    # mono_urls = '/linguistics/ethan/Crawled_data/Canlii/historic_monolingual/all_time/courts.monolingual.AllTime.url'
    cmd = CanliiMonolingualCrawler(rootOutput)
    cmd.crawl()

def test_DynamicBilingualCrawler():
    configPath = "./config/bilingual_crawl.conf"
    cf = ConfigParser()
    cf.read(configPath)

    dbc = DynamicBilingualCrawler(cf)
    dbc.crawl()

def test_GeneralBilingualCrawler():

    configPath = "./config/bilingual_crawl.conf"
    gbc = GeneralBilingualCrawler(configPath)
    gbc.crawl()

def test_node():
    url = "http://legisquebec.gouv.qc.ca/en/home"
    attibutes = {"href": True}
    text = "Français"

    soup = get_soup(url)
    node = soup.find("a", attibutes, text=text)
    print(node)


if __name__ == "__main__":

    # test_node()
    # test_crawl_bilingual()
    # test_crawl_monolingual()
    # test_CanliiMonolingualDownloader()
    # test_DynamicBilingualCrawler()
    test_GeneralBilingualCrawler()
