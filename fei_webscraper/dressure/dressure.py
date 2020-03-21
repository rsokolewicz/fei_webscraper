import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
import requests
from pandas import ExcelWriter
#from selenium.webdriver.common.by import By
#import time
import pandas as pd
import datetime 
import numpy as np
import time
import re

def initiate_table(conn,db_table_name):
    #PLAATS	NF	Sterren	DTM	RUBRIEK	RULE	RANK	RIDERCODE	RIDER	FEI ID	HORSE	STUDBOOK	PRIZEMONEY	TOTAL

    Kollomen ="" 
    Kollomen = Kollomen +"PLAATS text ," #0
    Kollomen = Kollomen +"NF  text ,"   #1
    Kollomen = Kollomen +"STERREN text ," #2
    Kollomen = Kollomen +"DTM text ," #3
    Kollomen = Kollomen +"RUBRIEK text ," #4
    Kollomen = Kollomen +"RULE text ," #5
    Kollomen = Kollomen +"Rank text ," #6
    Kollomen = Kollomen +"RIDERCODE text ," #7
    Kollomen = Kollomen +"RIDER text ," #8
    Kollomen = Kollomen +"FEI CODE text ," #9
    Kollomen = Kollomen +"HORSE text ," #10
    Kollomen = Kollomen +"STUDBOOK  text ," #11
    Kollomen = Kollomen +"PRIZEMONEY text ," #12
    Kollomen = Kollomen +"TOTAL text ," #13
    Kollomen = Kollomen +"URL text " #14
    
    conn.cursor().execute("CREATE TABLE "+db_table_name+"("+Kollomen+")")
    conn.commit()

def setup_database(db_name, db_table_name):
    conn = sqlite3.connect(db_name) 
    conn.cursor().execute('DROP TABLE IF EXISTS '+db_table_name+' ')
    initiate_table(conn,db_table_name ) 
    conn.commit()
    return conn

def search(searchquery, web_driver):
    web_driver.get("https://data.fei.org/Calendar/Search.aspx")
    def fillbox(key, value):
        fromDateBox = web_driver.find_element_by_id(key)
        fromDateBox.clear() 
        fromDateBox.send_keys(value)
    fillbox('PlaceHolderMain_dtCritDateTo_txtDate', searchquery['end date'])
    fillbox('PlaceHolderMain_dtCritDateFrom_txtDate', searchquery['start date'])
    fillbox('PlaceHolderMain_ccbCritNFs_I', searchquery['nf'])
    fillbox('PlaceHolderMain_txtCritEventCode', searchquery['event'])
    web_driver.find_element_by_id('PlaceHolderMain_btnSearch').click()

def GetNumberOfShowsAndPages(source):
    pattern = r'(\d+) Show\(s\)  /  (\d+) Page\(s\)'
    m = re.search(pattern, source)
    num_shows, num_pages = m.group(1), m.group(2)
    return num_shows, num_pages

def GetEvent(event, driver):    
    source = str(BeautifulSoup(driver.page_source,'lxml'))
    els = driver.find_elements_by_xpath("//a[@href]")
    return [el.get_attribute('href') for el in els if strip_event(el.text) == strip_event(event)][0]

def strip_event(event):
    return event.split("(")[0].strip()

def GetEventDetails(event_url, driver):
    driver.get(event_url)
    els = driver.find_elements_by_xpath("//a[@href]")
    return [el.get_attribute('href') for el in els if el.text == 'Individual Results']

def ExtractInfo(url, dict_results, SQL_connector, table_name,driver):
    def GetNumberOfResultsAndPages(driver):
        source = driver.page_source   
        #print(source)
        pattern = r'(\d+).{1,4}Result.{1,10}(\d+).+?Page'
        m = re.search(pattern, source)
        num_shows, num_pages = m.group(1), m.group(2)
        return int(num_shows), int(num_pages)

    def ProcessPage():
            #get all the rest
            event_soup = BeautifulSoup(requests.get(url,headers=headers).text, "html.parser")  
            table = event_soup.find("table", {"class": "grid sc"})

            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                if len(cols) >4:
                    cols = cols[:7]+cols[-1:]
                    ColToDict(cols, dict_results)
                    AddRowToSQL(SQL_connector, table_name, dict_results)
                    #PrintDict(dict_results)

    headers = {
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 
        'Accept-Encoding' : 'gzip, deflate, br', 
        'Accept-Language' : 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7', 
        'Cache-Control' : 'max-age=0', 
        'Connection' : 'keep-alive', 
        'Cookie' : 'cas_gateway_status=Failed; ASP.NET_SessionId=zrkzsm1hczghp3bhr1pxxoos; _ga=GA1.2.811109565.1537216629; _gid=GA1.2.1503092513.1537216629; datadome=A5cH_aMS3raSSpJ9-wpd9KUUWoJ3eNU~kLQTNUj01K', 
        'Host' : 'data.fei.org', 
        'Referer' : 'https://data.fei.org/Calendar/Search.aspx', 
        'Upgrade-Insecure-Requests' : '1', 
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }
    #get "rubriek", "rule", "date"
    driver.get(url)
    soup = BeautifulSoup(driver.page_source,'lxml')
    rubriek = soup.find('td', text=re.compile(".*Schedule Competition Nr.*")).find_next('td').text.strip()
    rule = soup.find('td', text=re.compile(".*Competition Rule.*")).find_next('td').text.strip()
    rule = (rule.split("-"))[0]
    date = soup.find('td', text=re.compile(".*Date.*")).find_next('td').text.strip()
    date = ConvertDate(date)
    dict_results['RUBRIEK'] = rubriek
    dict_results['RULE'] = rule
    dict_results['DTM'] = date
    dict_results['url'] = url
    
    #process each page
    num_shows, num_pages = GetNumberOfResultsAndPages(driver)
    #print("pages = %d" % num_pages)
    ProcessPage()
    if num_pages > 1:
        for page in range(2,num_pages+1):
            driver.find_element_by_link_text(str(page)).click()
            ProcessPage() 
def ConvertDate(datum):
    d, m, y =re.search('(\d+)/(\d+)/(\d+)',datum).groups()
    return y+m+d

def PrintDict(dict_results):
    mystring = ""
    for key in dict_results:
        mystring += dict_results[key]+" "
    print(mystring)

def ColToDict(cols, dict_result):
    dict_result['RANK'] = cols[0] 
    dict_result['RIDERCODE'] = cols[1]
    dict_result['RIDER'] = cols[2]
    dict_result['FEI'] = cols[3]
    dict_result['HORSE'] = cols[4]
    dict_result['STUDBOOK'] = cols[5]
    dict_result['PRIZEMONEY'] = cols[6]
    dict_result['TOTAL'] = cols[-1]

def InitializeResultsDict(searchquery):
    return {'PLAATS' : searchquery['show'],
               'NF' : searchquery['nf'],
               'Sterren' : searchquery['event full'],
               'DTM' : 'NULL',
               'RUBRIEK' : 'NULL',
               'RULE' : 'NULL',
               'RANK' : 'Null', 
               'RIDERCODE' : 'Null',
               'RIDER' : 'Null',
               'FEI' : 'Null',
               'HORSE' : 'Null',
               'STUDBOOK' : 'Null',
               'PRIZEMONEY' : 'Null',
               'TOTAL' : 'Null',
               'url' : 'NULL'}

def AddRowToSQL(SQL_connector, table, dict_results):
    sql = 'insert into %s VALUES(' % table
    for key in dict_results:
        sql += '\"'+dict_results[key]+ '\"'
        sql += ', '
    sql = sql[:-2] + ');'
    SQL_connector.execute(sql)
    SQL_connector.commit()



def DatabaseToExcel(db_name, db_table_name,excel_file_name):
    print("Nu alles naar excel zetten. Het excel bestand heet : "+excel_file_name )
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM "+db_table_name, conn)
    writer = ExcelWriter(excel_file_name)
    df.to_excel(writer,"Results",index=False)
    writer.save()
    conn.close()
    print("Helemaal klaar!! Geen crash, ga snel kijken of het klopt! ")

def InitializeDriver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'")
    prefs = {'profile.managed_default_content_settings.images':2}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(r'chromedriver',chrome_options=options)
    return driver

def ProcessExcel(db_name, db_table_name, input_file, output_file, driver, SQL_connector):
    xl = pd.read_excel(input_file)
    excel_lines=(xl.values)
    for line in excel_lines:
        show, nf, start_date, end_date, events = line
        start_date = start_date.date().strftime("%d/%m/%y")
        end_date = end_date.date().strftime("%d/%m/%y")

        for event in events.split(","):
            event=event.lstrip()
            searchquery = {"show" : show,
                           "nf" : nf,
                           "start date" : start_date,
                           "end date" : end_date,
                           "event" : strip_event(event),
                           "event full" : event}
            dict_results = InitializeResultsDict(searchquery)

            search(searchquery, driver)
            print(show,nf,event)
            try:
                event_url = GetEvent(event, driver)
            except:
                print("can't find event:")
                print(searchquery)
                AddRowToSQL(SQL_connector, db_table_name, dict_results)
            print(event_url)

            for url in GetEventDetails(event_url, driver):
                dict_results['url'] = url
                try:
                    ExtractInfo(url, dict_results, SQL_connector, db_table_name,driver)
                except:
                    print("cannot extract info from: % " % url)
                    AddRowToSQL(SQL_connector, db_table_name, dict_results)
