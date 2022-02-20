#CoinMarketCap.py

from audioop import add
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from sqlalchemy import false, true
from pythonpancakes import PancakeSwapAPI 
import time
import json
import cakebot
import sell

#Global Crap
purchasedTokens = {}

hoursAgo = 1
driverPath = r'C:\Users\Michael\ChromeDriver\chromedriver'
options = webdriver.ChromeOptions()
#options.add_argument('headless')
ps = PancakeSwapAPI()

blackList = []

foundDict = {}

#Methods
def getCarat(carat):
    if('down' in str(carat)):
        return '-'
    else:
        return '+'

def refreshSymDict():
    printStatus('REFRESHING SYMBOL DICTIONARY')

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
    return symbolDict

def findEligibleTokens(symbolDict, eligibleAgo=30):
    printStatus('FINDING ELIGIBLE TOKENS')

    newSymbolDict = {}
    for sym in symbolDict:
        #symbolDict.get(sym).get('Added Ago') == str(str(hoursAgo) + ' hours ago') or 
        howManyAgo = int(str(symbolDict.get(sym).get('Added Ago')).split(' ')[0])
        if(str('minutes') in symbolDict.get(sym).get('Added Ago')):
            if(howManyAgo <= eligibleAgo):
                if(symbolDict.get(sym).get('Network') == 'BNB'):
                    printStatus(str(sym) + ': POTENTIAL')
                    newSymbolDict.update({sym: symbolDict.get(sym)})

        if(sym in purchasedTokens.keys()):
            newSymbolDict.update({sym: symbolDict.get(sym)})

    for sym in newSymbolDict:
        address = ''
        if(sym not in purchasedTokens):
            driver = webdriver.Chrome(executable_path=driverPath)
            driver.minimize_window()
            driver.get(str(newSymbolDict.get(sym).get('HREF')))

            addresses =  driver.find_elements_by_tag_name('a')
            for addres in addresses:
                adres = addres.get_attribute('href')
                if(adres is not None):
                    if('https://bscscan.com/token/' in adres):
                        address = str(adres).replace('https://bscscan.com/token/', '')

            driver.quit()
        else:
            address = purchasedTokens.get(sym).get('Address')

        try:   
            token = ps.tokens(address=str(address))

            tempDict = symbolDict.get(sym)
            tempDict.update({'Address': address})

            symbolDict.update({sym: tempDict})
            newSymbolDict.update({sym: symbolDict.get(sym)})

            printStatus(str(sym) + ': ELIGIBLE')
        except Exception:
            printStatus(str(sym) + ' Not On PancakeSwap')

    return newSymbolDict

def updatePurchasedTokens(eligibleTokenDict):
    printStatus('UPDATING PURCHASED TOKENS')

    for sym in purchasedTokens:
        tempDict = purchasedTokens.get(sym)
        tempDict.update({   'Last Perf 24': eligibleTokenDict.get(sym).get('Perf 24'),
                            'Last Perf 1': eligibleTokenDict.get(sym).get('Perf 1')})
        purchasedTokens.update({sym: tempDict})

def determineTokenSellable(address):
    printStatus('DETERMINING IF TOKEN IS SELLABLE')

    if(address in blackList):
        return False

    printStatus('Determining ' + str(address) + ' Sellable')
    purchased = tryBuy(address,percent=.001)
    if(purchased):
        return trySellHoneyPot(address)

    blackList.append(address)
    return False

def detectHoneyPot(address='0xed74bc5dc139356e08de28143996f5ef6e4334a4'):
    printStatus('DETECTING HONEYPOT: ' + address)
    url = str('https://honeypot.is/?address=' + address)
    driver = webdriver.Chrome(executable_path=driverPath)
    driver.minimize_window()
    driver.get(url)
    status = [my_elem for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//div[contains(@class, 'success')]")))]
    driver.close()
    if(len(status) > 0):
        return False
    else:
        return True

def decidePurchaseToken(eligibleTokenDict):
    printStatus('DECIDING TO PURCHASE TOKEN')

    purchaseFile = open("purchases.txt", "w")
    for sym in eligibleTokenDict:
        if(sym not in purchasedTokens):
            try:
                address = eligibleTokenDict.get(sym).get('Address')
                if(detectHoneyPot(address) == False):
                    purchased = tryBuy()
                    if(purchased):
                        purchasedTokens.update({sym: {  'Address': address,
                                                        'Initial Perf 24': eligibleTokenDict.get(sym).get('Perf 24'),
                                                        'Last Perf 24': eligibleTokenDict.get(sym).get('Perf 24')}})
                        purchaseFile.write(str(purchasedTokens))
            except Exception as e:
                printStatus(str(e))
    
    purchaseFile.close()

def decideSellToken(eligibleTokenDict):
    printStatus('DECIDING TO SELL TOKEN')

    soldFile = open("sold.txt", "a")
    purchaseFile = open("purchases.txt", "w")

    for sym in purchasedTokens:
        perf24 = str(eligibleTokenDict.get(sym).get('Perf 24'))
        perf24Direction = str(perf24)[0]
        perf24Num = perf24.replace('+', '')
        perf24Num = perf24Num.replace('-', '')
        perf24Num = float(perf24Num.replace('%', ''))

        lastPerf24 = str(purchasedTokens.get(sym).get('Last Perf 24'))
        lastPerf24Direction = str(lastPerf24)[0]
        lastPerf24Num = lastPerf24.replace('+', '')
        lastPerf24Num = lastPerf24Num.replace('-', '')
        lastPerf24Num = float(lastPerf24Num.replace('%', ''))

        perf1 = str(eligibleTokenDict.get(sym).get('Perf 1'))
        perf1Direction = str(perf1)[0]
        perf1Num = perf1.replace('+', '')
        perf1Num = perf1Num.replace('-', '')
        perf1Num = float(perf1Num.replace('%', ''))

        lastPerf1 = str(purchasedTokens.get(sym).get('Last Perf 1'))
        lastPerf1Direction = str(lastPerf1)[0]
        lastPerf1Num = lastPerf24.replace('+', '')
        lastPerf1Num = lastPerf1Num.replace('-', '')
        lastPerf1Num = float(lastPerf1Num.replace('%', ''))

        #Sell For Profit
        if(perf24Direction == '+'):
            if(perf24Num > float(10)):
                if(perf24Num < lastPerf24Num):
                    print('Sell For Profit')
                    try:
                        sold = trySell(contract_id=purchasedTokens.get(sym).get('Address'))
                        if(sold):
                            soldFile.write(str(str(sym) + ' ' + str(purchasedTokens.get(sym).get('Address'))))
                            purchasedTokens.pop(sym)
                            purchaseFile.write(str(purchasedTokens))
                    except Exception as e:
                        printStatus(str(e))
                    continue

        #Sell To Stop Loss
        if(perf1Direction == '-'):
            print('Sell To Stop Loss')
            try:    
                sold = trySell(contract_id=purchasedTokens.get(sym).get('Address'))
                if(sold):
                    soldFile.write(str(str(sym) + ' ' + str(purchasedTokens.get(sym).get('Address'))))
                    purchasedTokens.pop(sym)
                    purchaseFile.write(str(purchasedTokens))
            except Exception as e:
                printStatus(str(e))
            continue
    soldFile.close()
    purchaseFile.close()
    return

def verifyTxnHash(txnHash, attempts=5):
    printStatus('VERIFYING TXN: ' + txnHash)
    for i in range(attempts):
        time.sleep(5)
        driver = webdriver.Chrome(executable_path=driverPath)
        driver.minimize_window()
        driver.get("https://bscscan.com/tx/" + str(txnHash))
        status = [my_elem.text for my_elem in WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//span[contains(@class, 'u-label u-label--sm u-label--success rounded')]")))]
        driver.close()
        if('SUCCESS' in str(status[0]).upper()):
            return True

    return False

def tryBuy(address, attempts=5, percent=0.5):
    printStatus('ATTEMPTING TO BUY: ' + address)
    for i in range(attempts):
        try:
            txnHash = cakebot.mainBuy(tokenToBuy=address, totalPercent=percent)
            
            verified = verifyTxnHash(txnHash)
            if(verified):
                printStatus('PURCHASED')
                return True
        except Exception as e:
            printStatus(str(e))

        time.sleep(15)
    return False

def trySell(address, attempts=5):
    printStatus('ATTEMPTING TO SELL: ' + address)
    for i in range(attempts):
        try:
            txnHash = sell.mainSpend(contract_id=address)
            verified = verifyTxnHash(txnHash)
            if(verified):
                printStatus('SOLD')
                return True
        except Exception as e:
            printStatus(str(e))
        time.sleep(15)
    return False

def trySellHoneyPot(address, attempts=5):
    printStatus('ATTEMPTING TO SELL: ' + address)
    for i in range(attempts):
        try:
            txnHash = sell.mainSpend(contract_id=address)
            verified = verifyTxnHash(txnHash)
            if(verified):
                printStatus('SOLD')
                return True
        except Exception as e:
            printStatus(str(e))
            if('TransferHelper: TRANSFER_FROM_FAILED' in str(e)):
                return False
        time.sleep(15)
    return True

def printStatus(status='STATUS', header=True):
    f = open("logFile.txt", "a")
    
    if(header):
        printString = '\n***** | '+ str(status) +' | *****'
    else:
        printString = '\n********** | ' + str(status)
    print(printString)

    f.write(printString)
    f.close()

def loadPurchaseDictionary():
    printStatus('LOADING PURCHASE DICTIONARY FROM FILE')
    try:
        purchaseFile = open('purchases.txt', 'r')
        dictString = purchaseFile.read()
        purchaseFile.close()

        dictString = dictString.replace('\'','"')
        purchasedTokens = json.loads(dictString)
    except Exception as e:
        printStatus(str(e))
        purchasedTokens = {}

    return purchasedTokens

        

def main():
    printStatus('***** | STARTING MAIN | *****')
    purchasedTokens = loadPurchaseDictionary()

    found = false
    while(found == false):
        printStatus('\t')
        printStatus('***** | STARTING LOOP | *****')
        
        refreshedDict = {}
        for i in range(5):
            try:
                refreshedDict = refreshSymDict()
                break
            except Exception as e:
                print(str(e))
                return

        eligibleTokens = findEligibleTokens(refreshedDict, 30)

        printStatus('REFRESHED TOKENS TOTAL--', False)
        printStatus(str(len(refreshedDict.keys())), False)

        if(len(refreshedDict.keys()) > 0):
            printStatus('5 REFRESHED TOKEN SUMMARY--', False)
            for i in range(5):
                printStatus(str(list(refreshedDict.keys())[i]) + ': ' + str(list(refreshedDict.values())[i]), False)
        
        printStatus('ELIGIBLE TOKENS TOTAL--', False)
        printStatus(str(len(eligibleTokens.keys())), False)

        if(len(eligibleTokens.keys()) > 0):
            printStatus('ELIGIBLE TOKEN SUMMARY--', False)
            printStatus(eligibleTokens, False)

        updatePurchasedTokens(eligibleTokens)

        decidePurchaseToken(eligibleTokens)
        decideSellToken(eligibleTokens)

        printStatus('SLEEPING')
        time.sleep(1* 60)

#Start Main
main()
