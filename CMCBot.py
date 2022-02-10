#CoinMarketCap.py

from audioop import add
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from sqlalchemy import false, true
import time

def getCarat(carat):
    if('down' in str(carat)):
        return '-'
    else:
        return '+'

hoursAgo = '1'
driverPath = r'C:\Users\Michael\ChromeDriver\chromedriver'
options = webdriver.ChromeOptions()
#options.add_argument('headless')

foundDict = {}

found = false
while(found == false):
    driver = webdriver.Chrome(executable_path=driverPath)
    driver.minimize_window()
    driver.get("https://coinmarketcap.com/new/")

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.cmc-cookie-policy-banner__close"))).click()
    #WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button/b[text()='No, thanks']"))).click()
    
    symbols =  [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td/a//p[@color='text']")))]
    network =  [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[9]")))]
    addedAgo = [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[10]")))]
    
    perf1 =    [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[5]")))]
    perf24 =   [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[6]")))]
    perf1_carat =    [my_elem.get_attribute('class') for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[5]//span//span")))]
    perf24_carat =   [my_elem.get_attribute('class') for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[6]//span//span")))]
    
    href =     [my_elem.get_attribute('href') for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[contains(@class, 'cmc-table')]//tbody//tr//td[3]//a")))]

    driver.quit()

    symbolDict = {}
    i = 0
    for sym in symbols:
        symbolDict.update({sym: {   'Network': network[i], 
                                    'Added Ago': addedAgo[i],
                                    'Perf 1': str(getCarat(perf1_carat[i]) + perf1[i]),
                                    'Perf 24': str(getCarat(perf24_carat[i]) + perf24[i]),
                                    'HREF': href[i]}})
        i = i + 1

    #print(symbolDict)
    newSymbolDict = {}
    for sym in symbolDict:
        if(symbolDict.get(sym).get('Added Ago') == str(hoursAgo + ' hours ago') or str('minutes') in symbolDict.get(sym).get('Added Ago')):
            if(symbolDict.get(sym).get('Network') == 'BNB'):
                newSymbolDict.update({sym: symbolDict.get(sym)})
                foundDict.update({sym: newSymbolDict.get(sym)})

    for sym in newSymbolDict:
        driver = webdriver.Chrome(executable_path=driverPath)
        driver.minimize_window()
        driver.get(str(newSymbolDict.get(sym).get('HREF')))

        #address =  driver.find_element_by_class_name('mobileContent') #sc-10up5z1-5 jlEjUY
        #address =  WebElement(address).find_element_by_class_name('cmc-link')
        #address = WebElement(address).get_attribute('href')

        address = ''
        addresses =  driver.find_elements_by_tag_name('a')


        tempDict = symbolDict.get(sym)
        tempDict.update({'Address': address})

        symbolDict.update({sym: tempDict})
        newSymbolDict.update({sym: symbolDict.get(sym)})

    for sym in foundDict:
        foundDict.update({sym: symbolDict.get(sym)})

    print('\nNEWEST: \n'+ str(newSymbolDict))
    print('\nUPDATED: \n' + str(foundDict))
    time.sleep(1* 60)
