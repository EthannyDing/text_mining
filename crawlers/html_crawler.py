# -*- coding: utf-8 -*-

# data_curation/crawlers: html_crawler
#
# Author: Renxian Zhang 
# --------------------------------------------------
# This module implements html crawler

from configparser import ConfigParser
import os
from pathlib import Path
from time import sleep

import urllib.parse
import regex as re
from datetime import datetime, date, timedelta
import dateparser
import pandas as pd
from pandas import Timestamp

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from PIL import Image
from captcha_solver import CaptchaSolver
from pathvalidate import sanitize_filename

from utils.language_resources import Codes
from utils.file_io import OS, TXTWriter, ExcelReader
from apis.rest_api_requests import API as ApiCrawler

NAME_YAPPN_MAPPINGS = Codes.mappings('name', 'yappn')
NAME_ISO6391_MAPPINGS = Codes.mappings('name', 'iso-639-1')


class BrowserBasedCrawler:    
    """Browser-based crawler using Selenium
    """
    
    def __init__(self, configPath):
        """Intialize a BrowserBasedCrawler instance.           
        
           Args:             
              configPath (str): the path of the configure file
        """        
           
        self._cf = ConfigParser()
        self._cf.read(configPath)
                
        #self._FireFoxDriverPath = self._cf.get('resources', 'gecko_driver_path')
        self._inputConfigPath = self._cf.get('input', 'config_path')
        self._os = OS()
    
    def _getCaptchaServiceKey(self):
        """Get captcha service (antigate) key
        """
        
        self._antigateKey = self._cf.get('resources', 'antigate_key')
               
    def _configChromeDriver(self, downloadPath=None, showBrowser=True, enablePdfViewer=False):        
        """Config a Chrome webdriver
        
           Args:
              downloadPath (str): the download path
              showBrowser (bool): whether to show the browser during crawling
              enablePdfViewer (bool): whether to enable the Chrome PDF Viewer
        """
        
        self._ChromeDriverPath = self._cf.get('resources', 'chrome_driver_path')
        
        options = webdriver.ChromeOptions()
        
        profile = {'plugins.plugins_list': {'enabled': enablePdfViewer,
                                            'name': 'Chrome PDF Viewer'},
                   'plugins.always_open_pdf_externally': True}
        if downloadPath:
            profile['download.default_directory'] = downloadPath
        
        options.add_experimental_option('prefs', profile)
        options.add_experimental_option('excludeSwitches', ['ignore-certificate-errors'], )
        
        if not showBrowser:
            options.add_argument('--disable-gpu')
            options.add_argument('--headless')                   
        
        self.driver = webdriver.Chrome(executable_path=self._ChromeDriverPath, options=options)
        self.driver.implicitly_wait(30)
        self.driver.maximize_window()
    
    def _getChromeClearBrowsingButton(self, driver):        
        """Find the "CLEAR BROWSING BUTTON" on the Chrome settings page.
        
           Args:
              driver: Selenium driver
        """
        
        res = driver.find_element_by_css_selector('* /deep/ #clearBrowsingDataConfirm')        
        
        return res
    
    def _clearChromeCache(self, timeout=60):
        """Clear the cookies and cache for the ChromeDriver instance.
        """
        
        # navigate to the settings page
        self.driver.get('chrome://settings/clearBrowserData')
    
        # wait for the button to appear
        wait = WebDriverWait(self.driver, timeout)
        wait.until(self._getChromeClearBrowsingButton)
    
        # click the button to clear the cache
        self._getChromeClearBrowsingButton(self.driver).click()
    
        # wait for the button to be gone before returning
        wait.until_not(self._getChromeClearBrowsingButton)    
                
    def renameFileWithTimestamp(self, filename, prefix, timestamp, suffix):
        """Rename a file with specified prefix and suffix and the current timestamp
        
           Args:
              filename (str): the filename as input
              prefix (str): the prefix to the timestamp
              timestamp (str): the current timestamp
              suffix (str): the suffix to the timestamp
              
           Returns:
              (str): the new filename
        """
        
        ext = os.path.splitext(filename)[-1]        
        res = '_'.join([prefix, timestamp, suffix]) + ext
        
        return res
    
        
class DisclosurenetCrawler_SingleQuery(BrowserBasedCrawler):    
    """A crawler for DisclosureNet (with single query)
    """
    
    def __init__(self, configPath, query=None, startDate=None, startPage=None, startItem=None):
        """Intialize a DisclosurenetCrawler_SingleQuery instance with website-specific details.           
        
           Args:             
              configPath (str): the path of the configure file
              query (str or None): the query used for crawling, 
                                   if None, find it in the configuration file
              startDate (str or None): the start date of crawling
                                       if None, find it in the configuration file
              startPage (int or None): the start page of crawling
                                       if None, find it in the configuration file 
              startItem (int or None): the start item of crawling
                                       if None, find it in the configuration file
        """
        
        super().__init__(configPath)        
        self._cf.read(self._inputConfigPath)    
        
        self._startUrl = self._cf.get('url', 'start')
        self._usernameId = self._cf.get('login', 'username_id')
        self._passwordId = self._cf.get('login', 'password_id')
        self._loginId = self._cf.get('login', 'login_id')
        self._username = self._cf.get('login', 'username')
        self._password = self._cf.get('login', 'password')  
        self._numItems = self._cf.getint('download', 'num_of_items_per_page')
        self._download_root_path = self._cf.get('download', 'root_path')
        
        if isinstance(query, str) and query:
            self._query = query
        else:
            self._query = self._cf.get('download', 'query')
        
        self._year1 = self._cf.getint('download', 'system_start_year')
        
        if isinstance(startDate, str) and startDate:
            self._startDate = startDate
        else:
            self._startDate = self._cf.get('download', 'start_date')
        
        self._endDate = self._cf.get('download', 'end_date')
        
        if isinstance(startPage, int) and startPage:
            self._startPage = startPage
        else:        
            self._startPage = self._cf.getint('download', 'start_page')
            
        if isinstance(startItem, int) and startItem:
            self._startItem = startItem
        else:        
            self._startItem = self._cf.getint('download', 'start_item')
        
        self.sourceLang = self._cf.get('language', 'source')
        self.targetLang = self._cf.get('language', 'target')
                        
        self._sleepTimeout = 300
        self.queryAsFilename = sanitize_filename(self._query, ' ')
        self.queryAsPrefix = re.sub('\s+', '_', self.queryAsFilename)        
        self._downloadPath = os.path.join(self._download_root_path, self.queryAsFilename)
        self._maxPage = 0                    
                                
        self._configChromeDriver(self._downloadPath)
        self._setXpaths()
        self._setRegexPatterns()
        self._setOutputPaths()
            
    def _setXpaths(self):
        """Set the xpaths of elements
        """
        
        self._ENG_FRA_MATCH_Selector_Xpath = '//*[@id="cdk-drop-list-0"]/div[2]/dn-single-tree-criteria/div/div/span[1]'
        self._ENG_FRA_MATCH_Yes_Xpath = '//*[@id="cdk-overlay-0"]/ng-component/div/div/div/dn-single-tree-assistant/div/p-tree/div/ul/p-treenode[1]/li/div/div/div'
        self._ENG_FRA_MATCH_Input_Xpath = '//*[@id="cdk-drop-list-0"]/div[2]/dn-single-tree-criteria/div/div/input'
        
        self._LANGUAGE_Selector_Xpath = '//*[@id="cdk-drop-list-0"]/div[6]/dn-tree-criteria/div/div/span[1]'
        self._LANGUAGE_English_Xpath = '//*[@id="cdk-overlay-1"]/ng-component/div/div/div/dn-tree-assistant/div/p-tree/div/ul/p-treenode[1]/li/div/div/div'
        self._LANGUAGE_Input_Xpath = '//*[@id="cdk-drop-list-0"]/div[6]/dn-tree-criteria/div/div/input'
        
        self._COMPANY_Input_Xpath = '//*[@id="cdk-drop-list-0"]/div[5]/dn-autocomplete-criteria/div/div/input'
        self._COMPANY_SelectAll_Xpath = '//*[@id="cdk-overlay-2"]/ng-component/div/div/div/dn-autocomplete-assistant/div/p-tree[1]/div/ul/p-treenode/li/div/div/div'
        self._COMPANY_All_Xpath = '//*[@id="cdk-overlay-2"]/ng-component/div/div/div/dn-autocomplete-assistant/div/p-tree[1]/div/ul/p-treenode/li/div/span[2]/span/span'
        self._COMPANY_Background_Xpath = '/html/body/div[8]/div[1]'
        self._COMPANY_SearchFilings_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/div/dn-search-bar/div/div[2]/dn-full-text-criteria/div/dn-recent-searches-input/div/dn-input/div/span[2]'
             
        self._DATE_Selector_Xpath = '//*[@id="cdk-drop-list-0"]/div[7]/dn-date-range-criteria/div/div/span[1]'
        self._DATE_StartDate_Xpath = '//*[@id="cdk-overlay-3"]/ng-component/div/div/div/dn-date-range-assistant/div[4]/div[1]/input'
        self._DATE_EndDate_Xpath = '//*[@id="cdk-overlay-3"]/ng-component/div/div/div/dn-date-range-assistant/div[4]/div[2]/input'
        self._DATE_Date_Year_Xpath = '/html/body/div[9]/div/p-calendar/span/div/div/div/select[2]'
        self._DATE_Date_Year_Value_Xpath_template = '/html/body/div[9]/div/p-calendar/span/div/div/div/select[2]/option[%d]'
        self._DATE_Date_Month_Xpath = '/html/body/div[9]/div/p-calendar/span/div/div/div/select[1]'
        self._DATE_Date_Month_Value_Xpath_template = '/html/body/div[9]/div/p-calendar/span/div/div/div/select[1]/option[%d]'
        self._DATE_Date_Day_Value_Xpath_template = '/html/body/div[9]/div/p-calendar/span/div/table/tbody/tr[%d]/td[%d]'
                        
        self._SEARCH_Xpath = '//*[@id="gridSearchBtnMain"]'
        
        self._Table_MatRow_Xpath_template = '//*[@id="tableContainer"]/mat-table/div[%d]/mat-row/mat-cell[2]/div'
        self._Table_ItemNumber_Xpath = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/div/label[1]'
        self._Table_NextPage_Xpath = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/dn-paginator/div[1]/div[3]/a[1]'
        self._Table_MaxPage_Xpath = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/dn-paginator/div[1]/div[2]/div[2]'
        self._Table_SelectPage_Xpath = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/dn-paginator/div[1]/div[2]/div[1]/p-dropdown/div/div[2]/span'
        self._Table_Page_Xpath_template = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/dn-paginator/div[1]/div[2]/div[1]/p-dropdown/div/div[3]/div/ul/li[%d]'
        self._Table_CurrentPage_Xpath = '//*[@id="DivGridColumn"]/dn-search-results-grid/div/div[2]/div/dn-paginator/div[1]/div[2]/div[1]/p-dropdown/div/label'
        
        self._PDF_Iframe_Document_Xpath_template = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[%d]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-iframe/div/iframe'
        self._PDF_Iframe_Source_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-iframe/div/iframe'
        self._PDF_Iframe_Target_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[2]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-iframe/div/iframe'
        self._PDF_Iframe_Filename_Xpath = '//*[@id="main-message"]/h1'
        self._PDF_Iframe_Open_Xpath = '//*[@id="open-button"]'
        self._PDF_Iframe_Back_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[1]/dn-filing-detail-header/div/ul[1]/li[1]/a'
        
        self._PDF_Actions_Source_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[1]/dn-filing-detail-header/div/ul[2]/li[2]/div/button'
        self._PDF_Actions_Target_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[2]/dn-filing-detail/div/div[1]/dn-filing-detail-header/div/ul/li[2]/div/button'
        self._PDF_Print_Source_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[1]/dn-filing-detail-header/div/ul[2]/li[2]/div/div/div[3]/a'
        self._PDF_Print_Target_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[2]/dn-filing-detail/div/div[1]/dn-filing-detail-header/div/ul/li[2]/div/div/div[3]/a'
        self._PDF_Filelink_Source_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-pdfjs/div/iframe'
        self._PDF_Filelink_Target_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[2]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-pdfjs/div/iframe'
        #self._PDF_JS_Source_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[1]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-pdfjs/div/div/button/img'
        #self._PDF_JS_Target_Xpath = '/html/body/dn-app/ng-component/div[1]/div[2]/ng-component/div/div[2]/dn-filing-detail/div/div[3]/div[2]/dn-filing-document/div/dn-pdfjs/div/div/button/img'
            
    def _setRegexPatterns(self):
        """Set regular expression patterns
        """
        
        self._filenamePattern = r'(?i)^.+?/PDF/(?P<filename>\d+(.+)?\.PDF)&.+$'
        self._filenameCandidatePattern = r'(?i)^(?P<filename>.+)(.PDF){2,}$'
    
    def _setOutputPaths(self):
        """Set the output paths for source language and target language
        """
        
        self.srcPath = os.path.join(self._downloadPath, NAME_YAPPN_MAPPINGS[self.sourceLang])
        self.tgtPath = os.path.join(self._downloadPath, NAME_YAPPN_MAPPINGS[self.targetLang])
        
        if not os.path.exists(self.srcPath):
            os.makedirs(self.srcPath)
        if not os.path.exists(self.tgtPath):        
            os.makedirs(self.tgtPath)
                
    def _clearCache(self):
        """Clear the browser cache
        """
        
        self._clearChromeCache()
            
    def clearTempDownloads(self):
        """Clear the temporary downloaded files
        """
        
        for name in os.listdir(self._downloadPath):
            if os.path.isfile(os.path.join(self._downloadPath, name)):
                os.remove(os.path.join(self._downloadPath, name))
        
    def login(self):
        """Log in the start page using username and password
        """
        
        self.driver.get(self._startUrl)
               
        username = self.driver.find_element_by_id(self._usernameId)
        password = self.driver.find_element_by_id(self._passwordId)
        login = self.driver.find_element_by_id(self._loginId)
        
        username.clear()
        username.send_keys(self._username)
        password.clear()
        password.send_keys(self._password)
        login.click()        
        
    def selectEngFraMatch(self):
        """Select "Yes" for "ENG/FRA MATCH"
        """
       
        selector = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._ENG_FRA_MATCH_Selector_Xpath)))
        selector.click()
        yes = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._ENG_FRA_MATCH_Yes_Xpath)))
        yes.click()
        inp = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._ENG_FRA_MATCH_Input_Xpath)))
        inp.send_keys(Keys.ENTER)
    
    def selectLanguage(self):
        """Select "English" for "LANGUAGE"
        """
       
        selector = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._LANGUAGE_Selector_Xpath)))
        selector.click()
        english = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._LANGUAGE_English_Xpath)))
        english.click()
        inp = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._LANGUAGE_Input_Xpath)))
        inp.send_keys(Keys.ENTER)    
    
    def selectCompany(self):
        """Type and select a company for "COMPANY NAME"        
        """
       
        inp = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._COMPANY_Input_Xpath)))
        inp.clear()
        inp.send_keys(self._query)
        selectAll = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._COMPANY_SelectAll_Xpath)))
        selectAll.click()
        while 'ui-state-default' not in selectAll.get_attribute('class'):
            sleep(1)      
        
        try:            
            background = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._COMPANY_Background_Xpath)))        
            background.click()
        except:            
            self.driver.switch_to.default_content()
            #print('Switched to default content')
            inp = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._COMPANY_Input_Xpath)))
            #print('Found "Input"')
            inp.clear()
            inp.send_keys(Keys.ENTER)
            #print('Clicked "Input"')
    
    def selectFilingDate(self):
        """Select start and/or dates of filing        
        """    
        
        if self._startDate or self._endDate:
            start = dateparser.parse(self._startDate)
            end = dateparser.parse(self._endDate)
            if start and end:
                assert end >= start, 'End date cannot be earlier than start date'
                
            selectDate = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._DATE_Selector_Xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView();", selectDate)
            selectDate.click()
                   
            if start is not None:                        
                self._selectDate(start, 'start')
            if end is not None:                        
                self._selectDate(end, 'end')        
                        
            background = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._COMPANY_Background_Xpath)))
            background.click()               
       
    def _selectDate(self, date, dateType):
        """Select date by interacting with the date picker
        
           Args:
              date (datetime): a datetime object
              dateType (str): 'start' or 'end'
        """
        
        if dateType == 'start':
            date_xpath = self._DATE_StartDate_Xpath
        elif dateType == 'end':
            date_xpath = self._DATE_EndDate_Xpath    
            
        year_xpath = self._DATE_Date_Year_Xpath
        year_value_xpath_template = self._DATE_Date_Year_Value_Xpath_template
        month_xpath = self._DATE_Date_Month_Xpath
        month_value_xpath_template = self._DATE_Date_Month_Value_Xpath_template
        day_value_xpath_template = self._DATE_Date_Day_Value_Xpath_template
                
        selectDate = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
        selectDate.click()
        
        selectYear = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, year_xpath)))
        selectYear.click()      
        year = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, year_value_xpath_template % (date.year - self._year1 + 1,))))
        year.click()            
        sleepCounter = 0
        while sleepCounter < self._sleepTimeout and year.text != str(date.year):
            sleep(1)
            sleepCounter += 1   
            
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, month_xpath)))
        selectYear.click()      
        month = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, month_value_xpath_template % (date.month,))))
        month.click()            
        sleepCounter = 0
        while sleepCounter < self._sleepTimeout and month.get_attribute('value') != str(date.month - 1):
            sleep(1)
            sleepCounter += 1
            
        day1Idx, day1 = 0, 0
        while day1 != '1':
            day1Idx += 1
            day = self.driver.find_element_by_xpath(day_value_xpath_template % (1, day1Idx))
            day1 = day.text
        trIdx, tdIdx = (date.day - 1 + day1Idx) // 7 + 1, (date.day - 1 + day1Idx) % 7    
        if tdIdx == 0:
            trIdx -= 1
            tdIdx = 7
        day = self.driver.find_element_by_xpath(day_value_xpath_template % (trIdx, tdIdx))    
        #day = self.driver.find_element_by_xpath(day_value_xpath_template % ((date.day - 1 + day1Idx) // 7 + 1, (date.day - 1 + day1Idx) % 7))
        day.click()    
        
    
    def search(self):
        """Click "SEARCH"
        """
        
        search = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._SEARCH_Xpath)))
        search.click()
        
    def _getItemNumberOnPage(self):
        """Get the total number of items on the current page
        
           Returns:
              (int): the number of items
        """
        
        itemNumber = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._Table_ItemNumber_Xpath)))
        res = int(itemNumber.text)    
    
        return res
    
    def clickItemOnPage(self, itemIdx):
        """Click one item on the search result page
        
           Args:
              itemIdx (int): the index of the item on the page, starting with 0
        """
        
        item = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._Table_MatRow_Xpath_template % (itemIdx + 2,))))
        item.click()
        
    def downloadParallelFilesOld(self, pageIdx, itemIdx):
        """Download the parallel files on the page
        
           Args:
              pageIdx (int): the index of the current page, starting with 0
              itemIdx (int): the index of the current item, starting with 0
        """        
        
        # PDF in source language       
        
        WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, self._PDF_Iframe_Document_Xpath_template % (1,)))) 
        srcFilename = self._downloadFile()
        self.driver.switch_to.default_content()   
        
        # PDF in target language       
                
        WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, self._PDF_Iframe_Document_Xpath_template % (2,)))) 
        tgtFilename = self._downloadFile()       
        self.driver.switch_to.default_content()    
                        
        # Rename with timestamp and move
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = '_'.join([str(pageIdx + 1).zfill(self._digitsOfMaxPage), 
                           str(itemIdx + 1).zfill(self._digitsOfItemsPerPage), 
                           self.queryAsPrefix])[:80]
        
        self._os.moveFile(os.path.join(self._downloadPath, srcFilename), 
                          os.path.join(self.srcPath, self.renameFileWithTimestamp(srcFilename, prefix, timestamp, NAME_YAPPN_MAPPINGS[self.sourceLang])))
        self._os.moveFile(os.path.join(self._downloadPath, tgtFilename), 
                          os.path.join(self.tgtPath, self.renameFileWithTimestamp(tgtFilename, prefix, timestamp, NAME_YAPPN_MAPPINGS[self.targetLang])))        

    def downloadParallelFiles(self, pageIdx, itemIdx):
        """Download the parallel files on the page
        
           Args:
              pageIdx (int): the index of the current page, starting with 0
              itemIdx (int): the index of the current item, starting with 0
        """        
        
        # PDF in source language       
                
        WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, self._PDF_Filelink_Source_Xpath))) 
        self.driver.switch_to.default_content()         
            
        actions = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Actions_Source_Xpath)))
        actions.click()
        srcPrint = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Print_Source_Xpath)))
        srcPrint.click()
        srcLink = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._PDF_Filelink_Source_Xpath)))
        srcFilename = self._downloadFile(srcLink.get_attribute('src'))
        
        # PDF in target language       
                
        WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, self._PDF_Filelink_Target_Xpath))) 
        self.driver.switch_to.default_content()
            
        actions = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Actions_Target_Xpath)))
        actions.click()
        tgtPrint = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Print_Target_Xpath)))
        tgtPrint.click()
        tgtLink = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._PDF_Filelink_Target_Xpath)))
        tgtFilename = self._downloadFile(tgtLink.get_attribute('src'))      
                        
        # Rename with timestamp and move
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = '_'.join([str(pageIdx + 1).zfill(self._digitsOfMaxPage), 
                           str(itemIdx + 1).zfill(self._digitsOfItemsPerPage), 
                           self.queryAsPrefix])[:80]
        
        self._os.moveFile(os.path.join(self._downloadPath, srcFilename), 
                          os.path.join(self.srcPath, self.renameFileWithTimestamp(srcFilename, prefix, timestamp, NAME_YAPPN_MAPPINGS[self.sourceLang])))
        self._os.moveFile(os.path.join(self._downloadPath, tgtFilename), 
                          os.path.join(self.tgtPath, self.renameFileWithTimestamp(tgtFilename, prefix, timestamp, NAME_YAPPN_MAPPINGS[self.targetLang])))     

    def _downloadFileOld(self):
        """Download one file
        
           Returns:
              (str): the name of the downloaded file
        """
        
        filename = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, self._PDF_Iframe_Filename_Xpath))).text
        btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Iframe_Open_Xpath)))
        btn.click()
        self._checkFileExistence(filename)
        
        return filename

    def _downloadFile(self, link):
        """Download one file
        
           Args:
              link (str): the file link
        
           Returns:
              (str): the name of the downloaded file
        """
        
        remoteFilename = re.search(self._filenamePattern, link).group('filename')
        localFilename = self._checkFileExistence(remoteFilename)
        
        return localFilename    

    def _checkFileExistence(self, remoteFilename):
        """Check the existence of downloaded file
        
           Args:
              remoteFilename (str): the file name as it appears in the html
              
           Returns
              (str): the downloaded file name (which may be different from remoteFilename)
        """
        
        # Handle abnormal filenames e.g. xxx.PDF.PDF by getting a candidate list
        filenameCandidates = [remoteFilename]
        while re.search(self._filenameCandidatePattern, remoteFilename):
            remoteFilename = remoteFilename[:-4]
            filenameCandidates.append(remoteFilename)
                
        sleepCounter = 0
        res = None
        
        while sleepCounter < self._sleepTimeout:
            for fn in filenameCandidates:
                if os.path.exists(os.path.join(self._downloadPath, fn)):
                    res = fn            
            if not res:            
                sleep(1)    
                sleepCounter += 1
            else:
                break            
        assert res
        
        return res    
           
    def clickBack(self):
        """Click "<Back"
        """
        
        back = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._PDF_Iframe_Back_Xpath)))
        back.click()  
    
    def downloadParallelFilesOnResultPage(self, pageIdx, itemStartIdx):
        """Download all the parallel files on one result page
        
           Args:
              pageIdx (int): the index of the current page, starting with 0
              itemStartIdx (int): the index of the start item, starting with 0
        """
        
        numItems = min(self._getItemNumberOnPage(), self._numItems)
        self._digitsOfItemsPerPage = len(str(numItems))
        
        for itemIdx in range(itemStartIdx, numItems):
            print('\tDownloading parallel files: %d / %d from page %d ...' % (itemIdx + 1, numItems, pageIdx + 1))
            try:
                self.clickItemOnPage(itemIdx)
                self.downloadParallelFiles(pageIdx, itemIdx)
                self.clickBack()
                print('\tDone.')
            except AssertionError:    
                print('\n\tBrowser failure, restarting ...')
                self._terminated = (pageIdx, itemIdx)
                raise
            except:
                print('\n\tNo more files on the page, exiting ...')
                raise RuntimeError
                  
    def _getMaxPage(self):
        """Get the total number of search result pages           
        """
        
        maxPage = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, self._Table_MaxPage_Xpath)))
        
        self._maxPage = int(re.search(r'^\s*/\s*(\d+)\s*$', maxPage.text).group(1))                  
                    
    def getDigitsOfMaxPage(self):
        """Get the digits of total number of search result pages           
        """
                
        self._getMaxPage()
        self._digitsOfMaxPage = len(str(self._maxPage))     
                
    def switchToNextResultPage(self):
        """Switch to the next search result page
        
           Returns:
              A selenium WebElement if it is enabled, otherwise None
        """     
        
        nextPage = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._Table_NextPage_Xpath)))
        
        if (not nextPage.get_attribute('class').strip().endswith('disabled')) and nextPage.is_enabled() and nextPage.is_displayed():
            res = nextPage
        else:
            res = None
            
        return res
    
    def switchToIndexedResultPage(self, pageIdx):
        """Switch to the indexed search result page
        
           Args:
              pageIdx (int): the index of the page to switch to, starting with 0
        
           Returns:
              A selenium WebElement if it is enabled, otherwise None
        """
        
        select = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._Table_SelectPage_Xpath)))
        select.click()
        indexedPage = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._Table_Page_Xpath_template % (pageIdx + 1,))))
        
        if indexedPage.is_enabled() and indexedPage.is_displayed():
            res = indexedPage
        else:
            res = None
            
        return res        
    
    def prepareForDownload(self, pageIdx):
        """Do the intial steps to prepare for downloading
        
           Args:
              pageIdx (int): the index of the page to switch to, starting with 0
        """
        
        try:            
            self.clearTempDownloads()
            self.login()
            self.selectEngFraMatch()
            self.selectLanguage()
            self.selectCompany()
            self.selectFilingDate()
            self.search()
            self.getDigitsOfMaxPage() 
        except TimeoutException:
            raise
        except:
            print('\n\tBrowser failure, restarting ...')
            self._terminated = (pageIdx, 0)
            raise AssertionError       
                    
    def download(self, pageIdx, itemStartIdx, singlePage=False):
        """Download all the parallel files on all the result pages, starting from specified page and item     
        
           Args:
              pageIdx (int): the index of the page to switch to, starting with 0
              itemStartIdx (int): the index of the start item, starting with 0
              singlePage (bool): whether to download only from a single (current) page
        """        
                       
        try:              
            if self._maxPage == 1:
                nextPage = True
            else:
                nextPage = self.switchToIndexedResultPage(pageIdx)
                if nextPage is None:
                    print('Page %d does not exist or is inaccessible, exiting ...' % (pageIdx + 1,))
                    raise RuntimeError
                else:
                    nextPage.click()
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._Table_CurrentPage_Xpath)))
                    WebDriverWait(self.driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, self._Table_CurrentPage_Xpath), str(pageIdx + 1)))                                   
        except:
            print('\nNo more pages, exiting ...')
            raise            
        else:
            while nextPage:
                print('\nStarting page %d ...' % (pageIdx + 1,))
                try:
                    self.downloadParallelFilesOnResultPage(pageIdx, itemStartIdx)
                except RuntimeError:
                    print('Done.')
                    break
                except:
                    raise
                else:
                    print('Done.')    
                    
                if singlePage:
                    nextPage = None
                else:
                    try:
                        nextPage = self.switchToNextResultPage()
                        if nextPage is None:
                            print('\nNo more pages, exiting ...')
                            break
                        else:
                            pageIdx += 1
                            itemStartIdx = 0
                            nextPage.click()
                            
                            sleepCounter = 0
                            while sleepCounter < self._sleepTimeout:
                                try:
                                    if WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._Table_CurrentPage_Xpath))).text != str(pageIdx + 1):
                                        raise ValueError('page not updated')
                                    else:
                                        break
                                except:
                                    sleep(1)                           
                                    sleepCounter += 1                                
                                    continue                           
                    except:
                        print('\nError, exiting ...')
                        raise
    
    def pipeline(self, pageIdx, itemStartIdx):
        """Downloading pipeline    
        
           Args:
              pageIdx (int): the index of the page to switch to, starting with 0
              itemStartIdx (int): the index of the start item, starting with 0
        """
        
        self.prepareForDownload(pageIdx)
        self.download(pageIdx, itemStartIdx, singlePage=True)      
        self.driver.quit()
        
        if self._maxPage == 1:
            raise InterruptedError
                  
                                                          
class DisclosurenetCrawler(BrowserBasedCrawler):    
    """A crawler for DisclosureNet
    """
    
    def __init__(self, configPath):
        """Intialize a DisclosurenetCrawler instance with website-specific details.           
        
           Args:             
              configPath (str): the path of the configure file
        """
        
        super().__init__(configPath)        
        self._cf.read(self._inputConfigPath) 
        
        self._rootConfigPath = configPath
        
        self._tabbedQuerySheetPath = self._cf.get('query_sheet', 'raw_path')
        self._querySheetPath = self._cf.get('query_sheet', 'merged_path')
        self._queryColumn = self._cf.get('query_sheet', 'query_column')
        self._sizeColumn = self._cf.get('query_sheet', 'size_column')
        self._timeColumn = self._cf.get('query_sheet', 'time_column')
                
        self._frequencyInDays = self._cf.getint('update', 'frequency_in_days')
        self._skipZeroSize = self._cf.getboolean('update', 'skip_empty_from_last_time')
        self._continuous = self._cf.getboolean('update', 'continuous')
        
        self._download_root_path = self._cf.get('download', 'root_path')
        self.sourceLang = self._cf.get('language', 'source')
    
    def preprocessTabbedQuerySheet(self):
        """Preprocess the raw (tabbed) query sheet by deduplicating, trimming trailing periods, 
           and rearranging the sheet
        """
        
        TRIM_PATTERN = r'^\s*(?P<trimmed>.+?)(\.+)\s*$'
        
        df = pd.read_excel(self._tabbedQuerySheetPath, sheet_name=None, header=None)
        
        # Insert the "Industry" column
        for key in df:
            df[key].insert(0, 'Industry', key)
            
        dfMerged = pd.concat([df[key] for key in df], ignore_index=True)
        
        # Insert a header
        dfMerged.columns = ['Industry', 'Company name']
        for col in ('Size', 'Last updated'):
            dfMerged[col] = ''  
        
        dfMerged.to_excel(self._querySheetPath, 'merged', index=False)
        
        # Trim trailing periods
        dfMerged['Company name'] = dfMerged['Company name'].apply(lambda x: re.search(TRIM_PATTERN, x).group('trimmed') 
                                                                  if re.search(TRIM_PATTERN, x) else x)
        
        # Deduplicating
        dfMerged.drop_duplicates(inplace=True)
        
        # Exporting
        dfMerged.to_excel(self._querySheetPath, 'merged', index=False)
    
    def mergeQuerySheets(self, mergeFromBasePath, mergeFromNewPath, mergeToPath, 
                         keyCol='Company name', mergeCols=('Size', 'Last updated'), 
                         initialDate='19000102'):
        """Merge query sheets by combining the information
        
           Args:
              mergeFromBasePath (str): the path of the base sheet to merge from
              mergeFromNewPath (str): the path of the new sheet (with update information) to merge from
              mergeToPath (str): the path of the merge output           
              keyCol (str): the column that acts as the "key"
              mergeCols (list): the columns to merge
              initialDate (str): the date to initialize datetime fields
        """
        
        dfBase = pd.read_excel(mergeFromBasePath)
        for col in mergeCols:
            if col == 'Last updated':
                dfBase[col] = dfBase[col].fillna(Timestamp(initialDate))
            else:
                dfBase[col] = dfBase[col].fillna('')
        dfBase = dfBase.set_index(keyCol)
          
        dfNew = pd.read_excel(mergeFromNewPath)
        dfNew = dfNew.set_index(keyCol)
        
        dfBase.update(dfNew)        
        dfBase.reset_index(inplace=True)
        dfBase.drop_duplicates([keyCol], inplace=True)
        
        dfBase.to_excel(mergeToPath, index=False, freeze_panes=(1, len(dfBase.columns)))
        
    def _readFromQuerySheet(self):
        """Read query information from the query sheet
        """
             
        df = pd.read_excel(self._querySheetBackupPath)
        df[self._sizeColumn] = df[self._sizeColumn].fillna('')
        df[self._timeColumn] = df[self._timeColumn].fillna('')
        
        self._queryInfo = df
        
    def prepareWithQuerySheet(self):
        """Prepare for crawling by preprocessing and reading from query sheets
        """
        
        self._querySheetBackupPath = os.path.splitext(self._querySheetPath)[0] + '_bak' + os.path.splitext(self._querySheetPath)[1]
        OS().copyFile(self._querySheetPath, self._querySheetBackupPath)
        self._readFromQuerySheet()        
        
    def checkTotal(self):
        """Check the total number of crawled queries and update the query sheet.
        """
        
        self._querySheetBackupPath = os.path.splitext(self._querySheetPath)[0] + '_bak' + os.path.splitext(self._querySheetPath)[1]
        OS().copyFile(self._querySheetPath, self._querySheetBackupPath)
        
        df = pd.read_excel(self._querySheetBackupPath)
        df[self._sizeColumn] = df[self._sizeColumn].fillna(0)
        df[self._timeColumn] = df[self._timeColumn].fillna('')
                
        for (index, row) in df.iterrows():
            query = row[self._queryColumn]
            print('\nCounting: %s' % query)
            queryAsFilename = sanitize_filename(query, ' ')        
        
            try:
                df.at[index, self._sizeColumn] += len(os.listdir(os.path.join(self._download_root_path, queryAsFilename, 
                                                                              NAME_YAPPN_MAPPINGS[self.sourceLang])))                        
            except:
                pass    
        
        df.to_excel(self._querySheetPath, 'total', index=False)
        
    def crawl(self):
        """Crawl using the queries from the sheet
        """
        
        try:
            for (index, row) in self._queryInfo.iterrows():
                query = row[self._queryColumn]
                print('\nCrawling: %s' % query)
                queryAsFilename = sanitize_filename(query, ' ')
                
                if self._skipZeroSize and row[self._sizeColumn] == 0:
                    print('\n\tNo parallel files found last time, skipping ...')
                    continue
                elif row[self._timeColumn]:
                    # If stale data, crawl incrementally
                    if datetime.today() - row[self._timeColumn] >= timedelta(days=self._frequencyInDays):                                    
                        crawlDisclosureNet_singleQuery(self._rootConfigPath, query, str(row[self._timeColumn]), 1, 1)
                        sizeOld = row[self._sizeColumn] if isinstance(row[self._sizeColumn], int) else 0
                        self._queryInfo.at[index, self._sizeColumn] = sizeOld + len(os.listdir(os.path.join(self._download_root_path, queryAsFilename, 
                                                                                                            NAME_YAPPN_MAPPINGS[self.sourceLang])))
                        self._queryInfo.at[index, self._timeColumn] = str(date.today())
                    # No incremental crawl, but do a house check if it was done before
                    elif row[self._sizeColumn] == '':
                        try:
                            self._queryInfo.at[index, self._sizeColumn] = len(os.listdir(os.path.join(self._download_root_path, queryAsFilename, 
                                                                                                      NAME_YAPPN_MAPPINGS[self.sourceLang])))                        
                        except:
                            self._queryInfo.at[index, self._sizeColumn] = 0
                else:
                    crawlDisclosureNet_singleQuery(self._rootConfigPath, query, None, 1, 1)
                    self._queryInfo.at[index, self._sizeColumn] = len(os.listdir(os.path.join(self._download_root_path, queryAsFilename, 
                                                                                              NAME_YAPPN_MAPPINGS[self.sourceLang])))
                    self._queryInfo.at[index, self._timeColumn] = str(date.today())               
        except:
            self._queryInfo.to_excel(self._querySheetPath, index=False, freeze_panes=(1, len(self._queryInfo.columns))) 
        finally:
            self._queryInfo.to_excel(self._querySheetPath, index=False, freeze_panes=(1, len(self._queryInfo.columns))) 


class CanliiCrawler(BrowserBasedCrawler):    
    """A crawler for CanLII.org
    """
    
    def __init__(self, configPath):
        """Intialize a CanliiCrawler instance with website-specific details.           
        
           Args:             
              configPath (str): the path of the configure file
        """
        
        super().__init__(configPath)        
        self._cf.read(self._inputConfigPath)    
        
        self._domain = self._cf.get('url', 'domain')
        self._captchaTitle = self._cf.get('url', 'captcha_title')
        self._urlRootPath = self._cf.get('input', 'url_root_path')
        self._prevUrlRootPath = self._cf.get('input', 'previous_url_root_path')
        self._urlSheetSuffix = self._cf.get('input', 'url_sheet_suffix')
        self._startWebpage = self._cf.getint('input', 'start_webpage')
        self._crawlRootPath = self._cf.get('output', 'crawl_root_path')
        self.sourceLang = self._cf.get('language', 'source')
        self.targetLang = self._cf.get('language', 'target')
                                      
        #self._configChromeDriver(showBrowser=False)
        self._configChromeDriver()
        self._configAntigateCaptchaService()
        self._setXpaths()
        self._setOutputPaths()
    
    def _configAntigateCaptchaService(self):
        """Configure the Antigate captcha service
        """
        
        self._getCaptchaServiceKey()
        self._captchaSolver = CaptchaSolver('antigate', api_key=self._antigateKey)
        
    def _setXpaths(self):
        """Set the xpaths of elements
        """
        
        self._LANGUAGE_SWITCH_Xpath = '//*[@id="languageSwitch"]/ul/li[1]/a'
        self._DOCUMENT_Xpath = '//*[@id="originalDocument"]'
        self._CAPTCHA_IMAGE_Xpath = '//*[@id="captchaTag"]'
        self._CAPTCHA_RESPONSE_Xpath = '//*[@id="captchaResponse"]'
        self._CAPTCHA_SUBMIT_Xpath = '//*[@id="captchaForm"]/form/input[6]'
        
    def _setOutputPaths(self):
        """Set the output paths for source language and target language
        """
        
        self.srcPath = os.path.join(self._crawlRootPath, NAME_YAPPN_MAPPINGS[self.sourceLang])
        self.tgtPath = os.path.join(self._crawlRootPath, NAME_YAPPN_MAPPINGS[self.targetLang])
        self.captchaRootPath = os.path.join(self._crawlRootPath, 'captcha')
        
        for path in (self.srcPath, self.tgtPath, self.captchaRootPath):
            if not os.path.exists(path):        
                os.makedirs(path)
                
        self.screenshotPath = os.path.join(self.captchaRootPath, 'screenshot.png')
        self.captchaPath = os.path.join(self.captchaRootPath, 'captcha.png')
            
    def _getInputUrlSheetPaths(self, urlRootPath):
        """Get the input url sheet paths
        
           Args:
              urlRootPath (str): the url root path
              
           Returns:
              (list): url sheet paths
        """    
        
        res = [os.path.join(urlRootPath, path) 
               for path in os.listdir(urlRootPath) 
               if os.path.isfile(os.path.join(urlRootPath, path))]
        
        return res
           
    def _getSourceUrlsFromExcel(self, urlSheetPaths):
        """Get the source urls from url sheets (Excel)
        
           Args:
              urlSheetPaths (list): url sheet paths
              
           Returns:
              (list): source urls
        """
                
        res = []
        
        for urlSheetPath in urlSheetPaths:
            er = ExcelReader(urlSheetPath)
            for ws in er.worksheets:
                if ws.endswith(self._urlSheetSuffix):
                    er = ExcelReader(urlSheetPath, worksheetName=ws)
                    urls = er.readColAsString(0, 0)
                    res += urls
        
        return res            
                      
    def _getIncrementalSourceUrlsFromExcel(self, currentUrls):
        """Get the incremental source urls from url sheets (Excel)
        
           Args:
              currentUrls (list): current urls
        """
        
        if self._prevUrlRootPath:
            prevUrlSheetPaths = self._getInputUrlSheetPaths(self._prevUrlRootPath)
            prevUrls = self._getSourceUrlsFromExcel(prevUrlSheetPaths)
            self._srcUrls = [url for url in currentUrls if url not in prevUrls] 
        else:
            self._srcUrls = currentUrls
                              
    def _downloadWebpage(self, url, outputPath, getParallelUrl):
        """Download the webpage content and save as html to output path
        
           Args:
              url (str): the url of the destination webpage
              outputPath (str): the output path
              getParallelUrl (bool): whether to get the parallel url by looking for "languageSwitch"
        """
        
        self.driver.get(url)
        
        if self.driver.title == self._captchaTitle:
            print('\t**Solving captcha ...')
            self._solveCaptcha()
            self._downloadWebpage(url, outputPath, getParallelUrl)
        else:
            if getParallelUrl:
                try:
                    paraUrlNode = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, self._LANGUAGE_SWITCH_Xpath)))
                    self._paraUrl = urllib.parse.urljoin(self._urlRootPath, paraUrlNode.get_attribute('href'))                
                except:
                    self._paraUrl = None
                else:
                    self._writePageContent(outputPath)
            else:
                self._writePageContent(outputPath)

    def _downloadCaptchaImage(self):
        """Download the captcha image
        """
        
        self.driver.save_screenshot(self.screenshotPath)
        
        img = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, self._CAPTCHA_IMAGE_Xpath)))
        topLeft_x, topLeft_y = img.location['x'], img.location['y']
        bottomRight_x, bottomRight_y = topLeft_x + img.size['width'], topLeft_y + img.size['height']
        
        screenshot = Image.open(self.screenshotPath)
        area = screenshot.crop((topLeft_x, topLeft_y, bottomRight_x, bottomRight_y))
        area.save(self.captchaPath, 'png')
        
    def _solveCaptchaInImage(self):
        """Solve the captcha in the downloaded image
        """ 
    
        img = open(self.captchaPath, 'rb').read()
        captchaText = self._captchaSolver.solve_captcha(img) 
        
        inp = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._CAPTCHA_RESPONSE_Xpath)))
        inp.clear()
        inp.send_keys(captchaText)    
        
        submit = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, self._CAPTCHA_SUBMIT_Xpath)))
        submit.click()        
                    
    def _solveCaptcha(self):
        """Solve captcha to make the process continue
        """
        
        self._downloadCaptchaImage()
        self._solveCaptchaInImage()

    def _writePageContent(self, outputPath):
        """Write page content to output path
        
           Args:
              outputPath (str): the output path
        """
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self._DOCUMENT_Xpath)))
        except:
            print('\t**Found no legal text ...')
        page = self.driver.page_source
        writer = TXTWriter(outputPath)
        writer.writeFromString(page)
        
    def _nameDownloadedWebpages(self, url, index, language, timestamp):
        """Name downloaded webpages (.html) in a systematic way
        
           Args:
              url (str): the url of one webpage
              index (int): the index of the downloaded webpage, starting with 0
              language (str): the language of crawled html
              timestamp (str): the current timestamp 
              
           Returns:
              (str): the name of the downloaded html to be saved
        """
        
        assert hasattr(self, '_num')
        
        htmlName = url.split('/')[-1]
        prefix = '_'.join([str(index + 1).zfill(len(str(self._num))), 
                           os.path.splitext(htmlName)[0]])[:80]
        suffix = NAME_YAPPN_MAPPINGS[language]
        
        res = self.renameFileWithTimestamp(htmlName, prefix, timestamp, suffix)
        
        return res
        
    def crawlParallelWebpages(self, url, index):
        """Download parallel webpage content and save as htmls to output path
        
           Args:
              url (str): the url of one webpage
              index (int): the index of the downloaded webpage, starting with 0
        """
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        self._downloadWebpage(url, os.path.join(self.srcPath, 
                                                self._nameDownloadedWebpages(url, index, self.sourceLang, timestamp)), 
                              getParallelUrl=True)
        if self._paraUrl:
            self._downloadWebpage(self._paraUrl, os.path.join(self.tgtPath, 
                                                              self._nameDownloadedWebpages(url, index, self.targetLang, timestamp)), 
                                  getParallelUrl=False)
        
    def prepareForCrawling(self):
        """Do the intial steps to prepare for downloading
        """
        
        print('\nPreparing for crawling ...')
        urlSheetPaths = self._getInputUrlSheetPaths(self._urlRootPath)
        currentUrls = self._getSourceUrlsFromExcel(urlSheetPaths)     
        self._getIncrementalSourceUrlsFromExcel(currentUrls)
        self._num = len(self._srcUrls)
        print('\tGot %d source urls' % (self._num, ))
        print('Done.')
    
    def pipeline(self, webpageStartIdx):
        """Crawling pipeline   
        
           webpageStartIdx (int): the index of the webpage to start, starting with 0
        """
        
        assert hasattr(self, '_num')
        
        for (idx, srcUrl) in enumerate(self._srcUrls):
            if idx < webpageStartIdx:
                continue
            print('\nCrawling %s (%d / %d) ...' % (srcUrl, idx + 1, self._num))
            self.crawlParallelWebpages(srcUrl, idx)
            if self._paraUrl:
                print('\tCrawled parallel htmls')
            else:
                print('\tFailed')
            print('Done.')
            
class HansardsCrawler(ApiCrawler):    
    """A crawler for sencanada.ca and www.ourcommons.ca
    """
    
    def __init__(self, configPath):
        """Intialize a HansardsCrawler instance with website-specific details.           
        
           Args:             
              configPath (str): the path of the configure file
        """
        
        super().__init__() 
        
        self._cf = ConfigParser()        
        self._cf.read(configPath)
        inputConfigPath = self._cf.get('input', 'config_path')
        self._cf.read(inputConfigPath)
        
        self.sourceLang = self._cf.get('language', 'source')
        self.targetLang = self._cf.get('language', 'target')  
        self.srcLang = NAME_YAPPN_MAPPINGS[self.sourceLang]
        self.tgtLang = NAME_YAPPN_MAPPINGS[self.targetLang]        
        self.srLang = NAME_ISO6391_MAPPINGS[self.sourceLang]
        self.tgLang = NAME_ISO6391_MAPPINGS[self.targetLang]    
        self.inputPath = self._cf.get('input', 'url_path') 
        self._col = self._cf.getint('input', 'column') - 1
        self._startRow = self._cf.getint('input', 'start_row') - 1
                
        self._setPaths()
        self._setRegexPatterns()
        
    def _setPaths(self):
        """Set the output paths for source and target languages
        """
                
        self.outputRootPath = self._cf.get('output', 'crawl_root_path')         
        
        if not os.path.exists(os.path.join(self.outputRootPath, self.srcLang)):
            os.makedirs(os.path.join(self.outputRootPath, self.srcLang))
        if not os.path.exists(os.path.join(self.outputRootPath, self.tgtLang)):
            os.makedirs(os.path.join(self.outputRootPath, self.tgtLang)) 
            
    def _setRegexPatterns(self):
        """Set regular expression patterns
        """
        
        self._worksheetNameTemplate = r'^(?P<session>\d\d-\d)_(%s)$'        
        self._urlPattern = r'(?P<url>https:\S+)'
            
    def getParallelUrls(self):        
        """Gets parallel urls
        """            
        
        er = ExcelReader(self.inputPath)
        
        worksheetNamePattern = self._worksheetNameTemplate % (self.srLang + '|' + self.tgLang,)
        
        # Get all worksheet names
        worksheetNames = [ws for ws in er.worksheets if re.search(worksheetNamePattern, ws)]
        sessions = sorted(set([re.search(worksheetNamePattern, ws).group('session') for ws in worksheetNames]))
        
        # Get parallel urls
        self.urlPairsWithSession = []
        
        for session in sessions:
            erSrc = ExcelReader(self.inputPath, worksheetName=session + '_' + self.srLang)
            erTgt = ExcelReader(self.inputPath, worksheetName=session + '_' + self.tgLang)
            urlsSrc = [re.search(self._urlPattern, url).group('url') for url in erSrc.readColAsString(self._col, self._startRow)]                       
            urlsTgt = [re.search(self._urlPattern, url).group('url') for url in erTgt.readColAsString(self._col, self._startRow)]
            self.urlPairsWithSession += zip([session]*len(urlsSrc), urlsSrc, urlsTgt)

    def crawlPair(self, filenamePrefix, urlPairWithSession, maxRetries=5):        
        """Crawl pages using the url pair
        
           Args:
              filenamePrefix (str): the filename prefix
              urlPairWithSession (iterable): a tuple of (session, source url, target url)
              maxRetries (int): maximum number of retries
        """
        
        session, urlSrc, urlTgt = urlPairWithSession        
        
        retry = 0
        while retry < maxRetries:        
            try:
                rawSrc = self.s.get(urlSrc)
                rawTgt = self.s.get(urlTgt)        
                                               
                filenameSrc = '_'.join([filenamePrefix, session, self.srcLang]) + '.html'
                filenameTgt = '_'.join([filenamePrefix, session, self.tgtLang]) + '.html'
              
                # Write to html
                for filename in (filenameSrc, filenameTgt):
                    if filename == filenameSrc:                    
                        writer = TXTWriter(os.path.join(self.outputRootPath, self.srcLang, filename))
                        writer.writeFromString(rawSrc.text)                                 
                    else:
                        writer = TXTWriter(os.path.join(self.outputRootPath, self.tgtLang, filename))
                        writer.writeFromString(rawTgt.text)   
                break
            except:
                sleep(2)
                retry += 1                
        
        if retry >= 5:
            print('Failed to crawl data after trying %d times' % (retry,))    
        
    def crawlPairs(self):        
        """Crawl pages using url pairs
        """        

        total = len(self.urlPairsWithSession)

        for (idx, urlPairWithSession) in enumerate(self.urlPairsWithSession):            
            print('\nCrawling from \n\t%s\n\t%s\nProgress: %d / %d ...' % (urlPairWithSession[1], urlPairWithSession[2], idx + 1, total))
            self.crawlPair(str(idx + 1).zfill(len(str(total))), urlPairWithSession)
            print('\nDone.')    


def crawlDisclosureNet_singleQuery(configPath, query=None, startDate=None, startPage=None, startItem=None):
    
    crawler = DisclosurenetCrawler_SingleQuery(configPath, query, startDate, startPage, startItem)        
    pageIdx = crawler._startPage - 1
    itemStartIdx = crawler._startItem - 1
    
    while True:
        try:            
            crawler.pipeline(pageIdx, itemStartIdx)                        
        except (InterruptedError, RuntimeError, TimeoutException):            
            break
            #raise
        except (AssertionError, ElementClickInterceptedException):
            if hasattr(crawler, '_terminated'):
                terminated_pageIdx, terminated_itemStartIdx = crawler._terminated
                crawler.driver.quit()
                crawler = DisclosurenetCrawler_SingleQuery(configPath, query, startDate, startPage, startItem)
                pageIdx, itemStartIdx = terminated_pageIdx, terminated_itemStartIdx
            else:
                raise
        except:
            raise
        else:
            #break
            crawler = DisclosurenetCrawler_SingleQuery(configPath, query, startDate, startPage, startItem)
            pageIdx += 1
            itemStartIdx = 0            
    
    if crawler._maxPage == 0:
        print('\nFound no results, exiting ...')
    
    try:       
        crawler.driver.quit()
    except:
        pass

def crawlDisclosureNet(configPath):
    
    crawler = DisclosurenetCrawler(configPath)
    
    if crawler._continuous:
        while True:            
            crawler.prepareWithQuerySheet()
            crawler.crawl()
    else:
        crawler.prepareWithQuerySheet()
        crawler.crawl()        

def crawlCanlii(configPath):
  
    crawler = CanliiCrawler(configPath)        
    webpageStartIdx = crawler._startWebpage - 1
    
    crawler.prepareForCrawling()
    crawler.pipeline(webpageStartIdx)
    
    try:       
        crawler.driver.quit()
    except:
        pass        

def crawlHansards(configPath):
    
    crawler = HansardsCrawler(configPath)
    
    crawler.getParallelUrls()
    crawler.crawlPairs()

def test1():
    
    configPath = r'D:\CODE\yappn-mt\data_curation\config\crawlers.conf'
    
    #res = crawlDisclosureNet_singleQuery(configPath)
    res = crawlDisclosureNet(configPath)
    
    return res

def test2():
    
    configPath = str(Path.joinpath(Path(__file__).parent, 'config', 'crawlers_canlii.conf'))
    
    res = crawlCanlii(configPath)
    
    return res

def test3():
    
    configPath = r'D:\CODE\yappn-mt\data_curation\config\crawlers.conf'
    #mergeFromBasePath = r'D:\TQI\Crawling\Sedar_merged_20190802_2.xlsx'
    #mergeFromNewPath = r'D:\TQI\Crawling\Sedar_prioritized_20190807.xlsx'
    #mergeToPath = r'D:\TQI\Crawling\Sedar_merged_20190807.xlsx'
        
    crawler = DisclosurenetCrawler(configPath)
    #res = crawler.preprocessTabbedQuerySheet()
    #res = crawler.mergeQuerySheets(mergeFromBasePath, mergeFromNewPath, mergeToPath)
    res = crawler.checkTotal()
    
    return res    

def test4():
    
    configPath = r'D:\CODE\yappn-mt\data_curation\test\config\crawlers_hansards.conf'
    
    res = crawlHansards(configPath)
    
    return res 


if __name__ == '__main__':
    
    #res = test1()
    res = test2()
    #res = test3()
    #res = test4()
        
    print('\nCompleted successfully')
