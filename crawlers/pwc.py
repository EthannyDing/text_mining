import os, time, pandas as pd
import requests
import urllib
import urllib.request
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from configparser import ConfigParser
from queue import Queue, Empty
from threading import Thread


class PwcCrawl(Thread):
    """Usage guideline in YDC.conf:

        1. specify Lang1 and Lang2, username and password if exists.
        2. inspect website and specify text, lang, hreflang, title of Lang1 and Lang2.
        3. set home_url as the homepage URL
        4. set head_url as the homepage URL of Lang1.

        Note: if crawling finishes as soon as program starts, try comment out line 320-322 and uncomment 323 & 324"""

    def __init__(self, cf):

        Thread.__init__(self)
        self.downloads = 0
        self.queue = Queue()
        self.visited = set()
        self.bilingual_url_pairs = set()

        self.home_url = cf.get("URL", "home_url")
        self.eng_head = cf.get("URL", "eng_head")
        self.fra_head = cf.get("URL", "fra_head")

        self.Lang1 = cf.get("Languages", "Lang1")
        self.Lang2 = cf.get("Languages", "Lang2")

        self.root_output = cf.get("Output", "matched_root_output")
        self.url_list = cf.get("Output", "url_list")

        self.queue.put(self.eng_head)
        self.visited.add(self.eng_head)
        self.bilingual_url_pairs.add((self.eng_head, self.fra_head))

        if not os.path.exists(self.root_output):
            os.makedirs(os.path.join(self.root_output, self.Lang1))
            os.makedirs(os.path.join(self.root_output, self.Lang2))

    def save_html(self, url_endpoint, save_path):
        """download html content given url."""
        try:
            print(save_path)
            urllib.request.urlretrieve(url_endpoint, save_path)
        # will so far not list all types of error saving given url.
        except:
            print("\t\tPage not founded or saved:{} ".format(url_endpoint))

    def save_parallel_html(self, pair, num):

        # keep parallel documents in a same prefix in order for Alignfactory to recognize.
        # l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + pair[0].split("/")[-2] + ".html"
        # l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + pair[0].split("/")[-2] + ".html"

        mirror = pair[0].split("/")
        if mirror[-1]:
            # base, name = os.path.split(pair[0])
            prefix, txt = os.path.splitext(mirror[-1])
            if txt:
                l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_ENG" + txt
                l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_FRA" + txt
            else:
                l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_ENG" + ".html"
                l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + prefix + "_FRA" + ".html"
        else:
            l1_name = (6 - len(str(num))) * "0" + str(num) + "_" + mirror[-2] + "_ENG" + ".html"
            l2_name = (6 - len(str(num))) * "0" + str(num) + "_" + mirror[-2] + "_FRA" + ".html"

        l1_dir = os.path.join(self.root_output, self.Lang1, l1_name)
        l2_dir = os.path.join(self.root_output, self.Lang2, l2_name)

        self.save_html(pair[0], l1_dir)
        self.save_html(pair[1], l2_dir)

    def get_abs_url(self, href):

        if 'https://' not in href:
            href = urljoin(self.eng_head, href)

        href = urldefrag(href).url.__str__()    # remove fragment in url.

        if not href.startswith(self.eng_head):
            return None
        else:
            return href

    def find_url_pairs_pwc(self, host_url):
        # self.eng_head = "https://www.justice.gc.ca/eng/"
        # self.fra_head = "https://www.justice.gc.ca/fra/"
        base, last = os.path.split(host_url.__str__())

        fra_last = last

        if base + "/" == self.eng_head:
            fra_url = self.fra_head + fra_last

        else:
            body = base.replace(self.eng_head, "")
            fra_body = body

            fra_url = self.fra_head + fra_body + '/' + fra_last

        pair = (host_url, fra_url)

        try:

            page = urllib.request.urlopen(host_url).read()
            soup = BeautifulSoup(page, features="lxml")
            soup.prettify()
            # page = requests.get(host_url, auth=(self.username, self.password)).content
            # soup = BeautifulSoup(page, features="html.parser", from_encoding="iso-8859-1")
            return pair, soup

        except:
            return None, None

    def find_url_pairs_law_lois(self, host_url):
        # self.eng_head = "https://www.justice.gc.ca/eng/"
        # self.fra_head = "https://www.justice.gc.ca/fra/"
        base, last = os.path.split(host_url.__str__())

        fra_last = last
        # if "-" in last:
        #     prefix, txt = os.path.splitext(last)
        #     pair = prefix.split("-")
        #     fra_prefix = pair[1] + "-" + pair[0]
        #     fra_last = fra_prefix + txt

        if base + "/" == self.eng_head:
            fra_url = self.fra_head + fra_last

        else:
            body = base.replace(self.eng_head, "")
            fra_body = body
            # for eng_fra in body.split("/"):
            #     if eng_fra:
            #         if "-" in eng_fra:
            #             pair = eng_fra.split("-")
            #             fra_eng = pair[1] + "-" + pair[0]
            #             fra_body = fra_body.replace(eng_fra, fra_eng)

            fra_url = self.fra_head + fra_body + '/' + fra_last

        pair = (host_url, fra_url)

        # body = base.replace(self.eng_head, "")
        # fra_body = body
        # for eng_fra in body.split("/"):
        #     if eng_fra:
        #         if "-" in eng_fra:
        #             pair = eng_fra.split("-")
        #             fra_eng = pair[1] + "-" + pair[0]
        #             fra_body = fra_body.replace(eng_fra, fra_eng)
        #
        # fra_url = self.fra_head + fra_body + '/' + last
        # print(host_url)
        # print(fra_url)

        try:

            page = urllib.request.urlopen(host_url).read()
            soup = BeautifulSoup(page, features="lxml")
            soup.prettify()
            # page = requests.get(host_url, auth=(self.username, self.password)).content
            # soup = BeautifulSoup(page, features="html.parser", from_encoding="iso-8859-1")
            return pair, soup

        except:
            return None, None

    def crawl(self):

        try:
            while True:

                host_url = self.queue.get_nowait()
                new_pair, soup = self.find_url_pairs_pwc(host_url)

                if new_pair is None:
                    # print("No pair founded.")
                    continue    #skip if host_url cannot opened or no pair found.

                saved_l2_urls = [bp[1] for bp in self.bilingual_url_pairs]
                if new_pair[1] in saved_l2_urls:
                    # print("L2 Url saved before.")
                    continue    #skip if new-founded l2 url already saved before.

                # if new_pair not in self.bilingual_url_pairs:
                print("\n\tSaving page of Lang1: {}".format(new_pair[0]))
                print("\tSaving page of Lang2: {}\n".format(new_pair[1]))
                self.bilingual_url_pairs.add(new_pair)
                self.save_parallel_html(new_pair, self.downloads)
                self.downloads += 1 # record the number of downloaded files

                for anchor in soup.find_all('a', href=True):

                    href = anchor['href']
                    href = self.get_abs_url(href)

                    if (href is None) or href.endswith(".aspx" ) or href.endswith(".asp") or href.endswith(".jpg"):
                    # if (href is None) or (not (href.endswith(".html") or href.endswith(".pdf"))):
                        continue    # skip adding pages of language 2 and those outside domain.

                    if href not in self.visited:
                        self.visited.add(href)      # add new-founded URLs of language 1 to visited
                        self.queue.put(href)        # add new-founded URLs of language 1 to queue

                        print("\tTotal number of pairs is saved: {}".format(self.downloads))
                        print("\n\tTotal number of URLs in queue: {}".format(self.queue.qsize()))

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

        # self.queue.join()
        # for i in range(max_threads):
        #     self.queue.put(None)

        # this would wait all threads to complete.
        for worker in workers:
            worker.join()

        eng_url = [pair[0] for pair in self.bilingual_url_pairs]
        fra_url = [pair[1] for pair in self.bilingual_url_pairs]
        df = pd.DataFrame({"source": eng_url, "target": fra_url}, columns=["source", "target"])
        df.to_excel(self.url_list, index=None, header=True)

        duration = time.time() - start
        print("Total time consumed: {} min".format(round(duration/60, 1)))


def test_find_url_pairs_pwc():
    website = "https://www.pwc.com/ca/en/industries.html"
    configPath = "YDC_pwc.conf"
    cf = ConfigParser()
    cf.read(configPath)
    pc = PwcCrawl(cf)
    pair, soup = pc.find_url_pairs_pwc(website)
    print(pair)

def download_pdf_from_url(url):

    r = requests.get(url, stream=True)
    # with open('E:\YDC\matched\metadata.pdf', 'wb') as f:
    #     f.write(r.content)
    # with open('E:\YDC\matched\metadata2.pdf', 'wb') as fd:
    #     for chunk in r.iter_content(2000):
    #         fd.write(chunk)


if __name__ == "__main__":

    # test_find_url_pairs_pwc()
    # url = 'https://www.hrecos.org/images/Data/forweb/HRTVBSH.Metadata.pdf'
    # download_pdf_from_url(url)

    configPath = "YDC_pwc.conf"
    cf = ConfigParser()
    cf.read(configPath)

    pc = PwcCrawl(cf)
    pc.run()

"https://www.pwc.com/ca/en/industries/private-equity.html"
"https://www.pwc.com/ca/fr/industries/private-equity.html"
