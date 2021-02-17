import requests
import pandas as pd, os, codecs, time, warnings
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from general_crawler import get_soup, _save_urls
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
warnings.filterwarnings('ignore', category=UserWarning, module='bs4')


def incremental_storing(URL_section, columns, excelPath):
    """incrementally save newly crawled urls into the same excel."""
    if os.path.exists(excelPath):
        df = pd.read_excel(excelPath)
        new_df = pd.DataFrame(URL_section, columns=columns)
        df = pd.concat([df, new_df])
    else:
        df = pd.DataFrame(URL_section, columns=columns)

    df.to_excel(excelPath, header=True, index=None)


########################################################## Responsible for main sections
def obtain_section_url(soup, domain_url,
                       main_attr, section_attr,
                       date_index, courts_sep, section='legislation', text='code', year='all'):
    """this function serves to extract all section related main urls."""

    province = domain_url.split('/')[-2]
    if section == 'legislation':
        section_nodes = soup.find('div', main_attr).find_all('div', section_attr)[:courts_sep]
    else:
        section_nodes = soup.find('div', main_attr).find_all('div', section_attr)[courts_sep:]
    main_urls = []
    for node in section_nodes:
        anchor = node.find('a')
        sub_url = anchor['href']
        if text == 'code':
            section_name = node.find('div').text.strip() if node.find('div').text.strip() else ""
        else:
            section_name = anchor.text.strip()
        date_info = node.find_all('div')[date_index].text.strip()
        abs_url = urljoin(domain_url, sub_url)

        if abs_url.startswith(domain_url):
            if year == 'all':
                main_urls.append((abs_url, section_name, province))
            elif date_info.split('-')[0] == year:
                main_urls.append((abs_url, section_name, province))

    return main_urls

def canlii_crawl_mainsection(province_url, rootOutput,
                             main_attr={'class': 'container pl-0'},
                             legislation_courts_attr={'class': 'row row-stripped py-1'},
                             tribunal_attr={'class': 'row row-stripped py-1 tribunalRow'},
                             date_index=3,
                             courts_sep=2,
                             year='all'):
    """crawl the URLs of three main sections of legislation, courts and tribunal."""
    soup = get_soup(province_url)
    if soup is None:
        print("Province URL cannot open: {}".format(province_url))
    else:
        main_legislation_urls = obtain_section_url(soup, province_url, main_attr, legislation_courts_attr,
                                                   date_index, courts_sep, section='legislation', text='name',year=year)
        main_court_urls = obtain_section_url(soup, province_url, main_attr, legislation_courts_attr,
                                             date_index, courts_sep, section='courts', text='code', year=year)
        main_tribunal_urls = obtain_section_url(soup, province_url, main_attr, tribunal_attr,
                                                date_index, courts_sep=0, section='tribunal', text='code', year=year)
        columns = ['URL', 'Code', 'Province']

        print("\n\t{} sections crawled from legislation".format(len(main_legislation_urls)))
        print("\t{} sections crawled from courts".format(len(main_court_urls)))
        print("\t{} sections crawled from tribunal\n".format(len(main_tribunal_urls)))
        incremental_storing(main_legislation_urls, columns, os.path.join(rootOutput, 'legislation.' + year + '.xlsx'))
        incremental_storing(main_court_urls, columns, os.path.join(rootOutput, 'courts.' + year + '.xlsx'))
        incremental_storing(main_tribunal_urls, columns, os.path.join(rootOutput, 'tribunal.' + year + '.xlsx'))
##########################################################################################


############################################################ Resonsible for URL subsection
def load_complete_page(driver, url, more_results_xpath, delay=5):
    """final the complete page by click 'Show More Results' button until no results to show.
       between each click there is a delay of default 5 seconds to let page fully load."""
    # url = 'https://www.canlii.org/en/ca/laws/regu/'
    # more_results_xpath = ".//span[@class='link showMoreResults']"
    print("\tOpening page: {}".format(url))
    driver.get(url)
    i = 1
    while True:
        try:
            print('\t\tClicking for more results: {} time(s)'.format(i))
            # WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, ".//div[@class='row row-stripped']")))
            more_result_element = driver.find_elements_by_xpath(more_results_xpath)[0]
            time.sleep(delay)
            more_result_element.click()
            time.sleep(delay)
        except Exception as ex:
            break
        i += 1
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

def find_all_years_from_code(driver, code_url, select_attr):
    """Find all years information from the dropdown and return complete URLs of each year."""
    try:
        driver.get(code_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        selector = soup.find('select', select_attr)
        code_all_years = []
        for option in selector.find_all('option', value=True):
            year_suburl = option['value']
            abs_year_url = urljoin(code_url, year_suburl)
            code_all_years.append(abs_year_url)
    except:
        code_all_years = None

    return code_all_years


def obtain_Legislation_url(soup, domain_url, main_node_attr):
    """Get all URLs from the main body section."""
    main_node = soup.find('div', main_node_attr)
    new_urls = []
    if main_node:
        for anchor in main_node.find_all('a'):
            sub_url = anchor['href']
            abs_url = urljoin(domain_url, sub_url)
            if abs_url.startswith(domain_url):
                new_urls.append(abs_url)
    else:
        print("Main body node is not found.")

    return new_urls


def obtain_CourtTribunal_url(driver, code_url_by_year, more_results_xpath, main_attr):
    """obtain all urls of law documents based on section url."""
    # section_url_by_year = code_url + 'nav/date/' + year + '/'
    soup = load_complete_page(driver, code_url_by_year, more_results_xpath)
    if soup is None:
        return None
    else:
        new_urls = []
        main_node = soup.find('div', main_attr)
        if main_node:
            for anchor in main_node.find_all('a'):
                href = anchor['href']
                abs_url = urljoin(code_url_by_year, href)
                new_urls.append(abs_url)

    return new_urls


def canlii_crawl_CourtTribunal(driver, mainsection_path, subsectionOutput,
                               select_attr={'id': 'navYearsSelector'},
                               more_results_xpath=".//span[@class='link showMoreResults']",
                               main_attr={'id': 'decisionsListing'},
                               year='all',
                               sheetname='bilingual'):
    """Open URls of *Courts* and *Tribunal* section. For each URL after entering, there are a list of url
       of new documents to be crawled."""
    df_courts = pd.read_excel(mainsection_path, sheet_name=sheetname)
    all_courts = []

    for code_url, code_name in zip(df_courts['URL'], df_courts['Code']):

        code_all_years = find_all_years_from_code(driver, code_url, select_attr)
        if code_all_years is None:
            continue

        if year == 'all':
            selected_years = code_all_years
        else:
            selected_years = [cy for cy in code_all_years if cy.split('/')[-2] == year]

        for code_year in selected_years:
            new_urls = obtain_CourtTribunal_url(driver, code_year, more_results_xpath, main_attr)

            if new_urls:
                # names = [code_name] * len(new_urls)
                # all_courts += list(zip(new_urls, names))
                all_courts += new_urls
    print(len(all_courts))
    # columns = ['URL', 'Code']
    # incremental_storing(all_courts, columns, subsectionOutput)
    with codecs.open(subsectionOutput, 'w') as f:
        for url in all_courts:
            f.write(url + '\n')

def canlii_crawl_Legislation(driver, mainsection_path, subsectionOutput, sheet_name="bilingual",
                                     main_attr={'id': 'legislationsContainer'},
                                     more_results_xpath=".//span[@class='link showMoreResults']"):
    """Open URls of *Legislation* section. For each URL after entering, there are a list of url
       of new documents to be crawled."""
    df_leg = pd.read_excel(mainsection_path, sheet_name=sheet_name)
    all_legislation_urls = []

    for section_url, pn in zip(df_leg['URL'], df_leg['Province']):
        soup = load_complete_page(driver, section_url, more_results_xpath)
        new_urls = obtain_Legislation_url(soup, section_url, main_attr)
        province_name = [pn] * len(new_urls)
        all_legislation_urls += list(zip(new_urls, province_name))

    columns = ['URL', "Province"]
    incremental_storing(all_legislation_urls, columns, subsectionOutput)
##########################################################################################

def test_canlii_mainsection():
    # codes = ['ca', 'yk', 'ab', 'nb', 'nt', 'sk', 'ns', 'nu', 'mb', 'pe', 'on', 'nl', 'bc', 'qc']
    # leg_sections = [3, 2, 3, 3, 2, 3, 2, 2, 3, 2, 2, 2, 2, 3]
    # prov_code_leg_section = dict(zip(codes, leg_sections))
    prov_code_leg_section = {'ca': 3, 'yk': 2, 'ab': 3, 'nb': 3, 'nt': 2, 'sk': 3, 'ns': 2,
                             'nu': 2, 'mb': 3, 'pe': 2, 'on': 2, 'nl': 2, 'bc': 2, 'qc': 3}

    rootOutput = '/linguistics/ethan/Canlii_data/Crawl_2021'
    for code, cs in prov_code_leg_section.items():
        province_url = 'https://www.canlii.org/en/' + code + '/'
        print("Crawling province: {}".format(province_url))
        canlii_crawl_mainsection(province_url, rootOutput,
                                 main_attr={'class': 'container pl-0'},
                                 legislation_courts_attr={'class': 'row row-stripped py-1'},
                                 tribunal_attr={'class': 'row row-stripped py-1 tribunalRow'},
                                 date_index=3,
                                 courts_sep=cs)  # <--- this number can change.

def test_canlii_CourtTribunal_subsection():
    executable_path = '/linguistics/ethan/Downloads/chromedriver_version87'
    driver = webdriver.Chrome(executable_path=executable_path)

    mainsection_path = '/linguistics/ethan/Canlii_data/summary/tribunal.bi-mono-lingual.xlsx'
    subsectionOutput = '/linguistics/ethan/Canlii_data/Crawl_2021/bilingual_urls/tribunal_codes_bilingual.2021.xlsx'

    # if year=all, all historic urls, otherwise specify the year to crawl, e.g. 2020
    canlii_crawl_CourtTribunal(driver, mainsection_path, subsectionOutput, year='2021', sheetname="bilingual")

def test_canlii_Legislation_subsection():
    executable_path = '/linguistics/ethan/Downloads/chromedriver_version87'
    driver = webdriver.Chrome(executable_path=executable_path)

    mainsection_path = '/linguistics/ethan/Canlii_data/summary/legislation.bi-mono-lingual.xlsx'
    subsectionOutput = '/linguistics/ethan/Canlii_data/Crawl_2021/bilingual_urls/legislation_codes_bilingual.2021.xlsx'
    canlii_crawl_Legislation(driver, mainsection_path, subsectionOutput, sheet_name="bilingual",
                                        main_attr={'id': 'legislationsContainer'},
                                        more_results_xpath=".//span[@class='link showMoreResults']")


if __name__ == '__main__':

    # test_canlii_mainsection()
    # test_canlii_CourtTribunal_subsection()
    test_canlii_Legislation_subsection()
