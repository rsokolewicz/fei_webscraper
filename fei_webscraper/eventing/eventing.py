import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
import requests
from pandas import ExcelWriter
#from selenium.webdriver.common.by import By
import time
import pandas as pd
import datetime 
import numpy as np
import time
import re

class PaardenDatabase():
    def __init__(self):
        self.table_name = "eventing"
        self.time =  str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        self.db_name = 'database/DatabaseEventing_'+self.time+'.db'
        self.SQL_connector = self.setup_database()
        self.conn = ""
        
    def setup_database(self):
        self.conn = sqlite3.connect(self.db_name) 
        self.conn.cursor().execute('DROP TABLE IF EXISTS '+self.table_name+' ')
        self.initiate_table(self.conn ) 
        self.conn.commit()
        return self.conn
    
    def initiate_table(self, conn):
        #PLAATS	NF	Sterren	DTM	RUBRIEK	RULE	RANK	RIDERCODE	RIDER	FEI ID	HORSE	STUDBOOK	PRIZEMONEY	TOTAL
        #PLAATS	NF	COMP	DATUM	RUBRIEK	Pos.	FEI ID	Athlete	FEI ID	Horse	Studbook
        #MER	D	XC obs	XC tim	J obs	J tim	Prize Money		Score

        Kollomen ="" 

        Kollomen = Kollomen +"PLAATS text ," #0
        Kollomen = Kollomen +"NF  text ,"   #1
        Kollomen = Kollomen +"COMP text ," #2
        Kollomen = Kollomen +"DATUM text ," #3
        Kollomen = Kollomen +"RUBRIEK text ," #4
        Kollomen = Kollomen +"pos text ," #5
        Kollomen = Kollomen +"FEI ID text ," #6
        Kollomen = Kollomen +"Athlete text ," #7
        Kollomen = Kollomen +"HorseID text ," #8
        Kollomen = Kollomen +"Horse text ," #9
        Kollomen = Kollomen +"Studbook text ," #10
        Kollomen = Kollomen +"MET text ," #11
        Kollomen = Kollomen +"D text ," #12
        Kollomen = Kollomen +"XCobs text ," #13
        Kollomen = Kollomen +"XCtim text ," #14
        Kollomen = Kollomen +"Jobs text ," #15
        Kollomen = Kollomen +"Jtim text ," #16
        Kollomen = Kollomen +"Prize Money text ," #17
        Kollomen = Kollomen +"Score text ," #18
        Kollomen = Kollomen +"URL text " #19

        conn.cursor().execute("CREATE TABLE "+self.table_name+"("+Kollomen+")")
        conn.commit()
        
    def AddRowToSQL(self, dict_results):
        sql = 'insert into %s VALUES(' % self.table_name
        for key in dict_results:
            sql += '\"'+dict_results[key]+ '\"'
            sql += ', '
        sql = sql[:-2] + ');'
        #print(sql)
        self.SQL_connector.execute(sql)
        self.SQL_connector.commit()

    def DatabaseToExcel(self, excel_file_name):
        print("Nu alles naar excel zetten. Het excel bestand heet : "+excel_file_name )
        self.conn = sqlite3.connect(self.db_name)
        c = self.conn.cursor()
        df = pd.read_sql_query("SELECT * FROM "+self.table_name, self.conn)
        writer = ExcelWriter(excel_file_name)
        df.to_excel(writer,"Results",index=False)
        writer.save()
        self.conn.close()
        print("Helemaal klaar!! Geen crash, ga snel kijken of het klopt! ")

def search(searchquery, driver):
    driver.get("https://data.fei.org/Calendar/Search.aspx")
    def fillbox(key, value):
        fromDateBox = driver.find_element_by_id(key)
        fromDateBox.clear() 
        fromDateBox.send_keys(value)
    fillbox('PlaceHolderMain_dtCritDateTo_txtDate', searchquery['end date'])
    fillbox('PlaceHolderMain_dtCritDateFrom_txtDate', searchquery['start date'])
    fillbox('PlaceHolderMain_ccbCritNFs_I', searchquery['nf'])
    fillbox('PlaceHolderMain_txtCritEventCode', searchquery['event'])
    driver.find_element_by_id('PlaceHolderMain_btnSearch').click()

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

def ExtractInfo(url, dict_results, db, driver):
    def GetNumberOfResultsAndPages(driver):
            source = driver.page_source   
            #print(source)
            pattern = r'(\d+).{1,4}Result.{1,10}(\d+).+?Page'
            m = re.search(pattern, source)
            num_shows, num_pages = m.group(1), m.group(2)
            return int(num_shows), int(num_pages)

    def ProcessPage():
            #get all the rest
            event_soup = BeautifulSoup(driver.page_source,'lxml')
            table = event_soup.find("table", {"class": "grid sc"})

            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if HasCheckMark(cols):
                    cols = [ele.text.strip() for ele in cols]
                    cols[6]='x'
                else:
                    cols = [ele.text.strip() for ele in cols]
                if len(cols)>8:
                    #print(cols)
                    ColToDict(cols,dict_results)
                    db.AddRowToSQL(dict_results)
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
    #get "rubriek", "rule", "
    driver.get(url)
    soup = BeautifulSoup(driver.page_source,'lxml')
    rubriek = soup.find('td', text=re.compile(".*Schedule Competition Nr.*")).find_next('td').text.strip()
    rule = soup.find('td', text=re.compile(".*Competition Rule.*")).find_next('td').text.strip()
    rule = (rule.split("-"))[0]
    date = soup.find('td', text=re.compile(".*Date.*")).find_next('td').text.strip()
    date = ConvertDate(date)
    dict_results['RUBRIEK'] = rubriek
    dict_results['COMP'] = rule
    dict_results['DATUM'] = date
    dict_results['URL'] = url

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
    dict_result['POS'] = cols[0] 
    dict_result['FEI ID'] = cols[1] 
    dict_result['ATHLETE'] = cols[2]
    dict_result['HORSE ID'] = cols[3]
    dict_result['HORSE'] = cols[4]
    dict_result['STUDBOOK'] = cols[5]
    dict_result['MER'] = cols[6]
    dict_result['D'] = cols[7]
    dict_result['XC OBS'] = cols[8]
    dict_result['XC TIM'] = cols[9]
    dict_result['J OBS'] = cols[10]
    dict_result['J TIM'] = cols[11]
    dict_result['PRIZE MONEY'] = cols[12]
    dict_result['SCORE'] = cols[-1]
    #PrintDict(dict_result)
    


def InitializeResultsDict(searchquery):
    return {'PLAATS' : searchquery['show'],
               'NF' : searchquery['nf'],
               'COMP' : searchquery['event full'],
               'DATUM' : 'NULL',
               'RUBRIEK' : 'NULL',
               'POS' : 'NULL',
               'FEI ID' : 'Null', 
               'ATHLETE' : 'Null',
               'HORSE ID' : 'Null',
               'HORSE' : 'Null',
               'STUDBOOK' : 'Null',
               'MER' : 'Null',
               'D' : 'Null',
               'XC OBS' : 'Null',
               'XC TIM' : 'NULL',
               'J OBS' : 'Null',
               'J TIM' : 'NULL',
               'PRIZE MONEY' : 'NULL',
               'SCORE' : 'NULL',
               'URL' : 'NULL'
           }

def AddRowToSQL(SQL_connector, table, dict_results):
    sql = 'insert into %s VALUES(' % table
    for key in dict_results:
        sql += '\"'+dict_results[key]+ '\"'
        sql += ', '
    sql = sql[:-2] + ');'
    #print(sql)
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

def HasCheckMark(col):
    mystring = str(col)
    if ('img' in mystring):
            return True
    else:
        return False
    
def ProcessExcel(input_file, output_file, db):
    driver=InitializeDriver()
    xl = pd.read_excel(input_file)
    excel_lines=(xl.values)
    for line in excel_lines:
        show, nf, start_date, end_date, events = line[:5]
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
            try:
                search(searchquery, driver)
            except:
                print("can't search. Closed Chrome window?")
                db.DatabaseToExcel(output_file)
                exit()
            print(show,nf,event)
            try:
                    event_url = GetEvent(event, driver)
                    print(event_url)
            except:
                print("can't find event:")
                print(searchquery)
                db.AddRowToSQL(dict_results)
                print(event_url)
            for url in GetEventDetails(event_url, driver):
                dict_results['URL'] = url
                #PrintDict(dict_results)
                try:
                    ExtractInfo(url, dict_results, db, driver)
                    
                except:
                    print("cannot extract info from: %s " % url)
                    db.AddRowToSQL(dict_results)