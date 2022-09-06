#Import va function
# from pandas.core.frame import DataFrame
# from requests_html import HTMLSession
import os
from shutil import ExecError
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
# import pandas as pd
import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime


#Setup:
# 1. Bật command prompt -> cd /d C:\Program Files\Google\Chrome\Application
# 2. -> chrome.exe --remote-debugging-port=8989 --user-data-dir="F:\ASM Group\Tool Python\driver\chrome.existing"
#chrome_options.add_argument("--incognito") mở ẩn danh
#login account và vào url https://sellercentral.amazon.com/inventory

opt = webdriver.ChromeOptions()
opt.add_experimental_option("debuggerAddress","localhost:8989") 
MOVE_TO_NEXT_PRODUCT_STRING = "Move to the next product..."
BASE_DIRECTORY = "F:\\ASM Group\\Tool Python"
driver = webdriver.Chrome(executable_path=f'{BASE_DIRECTORY}\\driver\\chromedriver.exe',options=opt)
countSuccess = 0
productCount = 0

# ------------------------------ Prepare log file ------------------------------ #
todayString = datetime.now().strftime('%Y_%m_%d')
filepath = os.path.join(f'{BASE_DIRECTORY}\\logs', f'{todayString}_log.txt')
if not os.path.exists(f'{BASE_DIRECTORY}\\logs'):
    os.makedirs(f'{BASE_DIRECTORY}\\logs')
f = open(filepath, "a+")

with open(f'{BASE_DIRECTORY}\\Freelancer.csv','r') as csv_file:
    csv_reader = csv.reader(csv_file)
    row_count = len(list(csv_file))
    csv_file.seek(0)
    for line in csv_reader:
        try: 

            shouldContinue = False

            def skipProductIfCan():
                if shouldContinue:
                    continue

            productCount += 1
            productAsin = line[0]

            # ------------------------------ Logging function ------------------------------ #
            def log(logContent, save = False):
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logString = f"{productAsin}: {now}: {logContent}"
                print(logString)
                if save:
                    f.write(f'{logString}\n')

            log(f'Start offering item {productCount}/{row_count}...', True)  
            url = f'https://sellercentral.amazon.com/abis/listing/syh?asin={productAsin}&ref_=xx_addlisting_dnav_xx#offer'
            driver.get(url)
            time.sleep(1)

            # ------------------------------ Brand Approval ------------------------------ #
            try: 
                isBrandNeedAprove = driver.find_element_by_xpath('//*[@id="marathonUI"]//span[text()="Error!"]')
                if isBrandNeedAprove:
                    log(f'Brand need approval. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                    continue
            except NoSuchElementException:
                log('Brand does not need Approval')

            # ------------------------------ ASIN Approval ------------------------------ #
            try: 
                if driver.find_element_by_xpath('//*[@id="marathonUI"]/div/div/div/div[2]/section[2]/ul[1]').tag_name == 'ul':
                    log(f'ASIN needs Approval. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                    continue
            except:
                log('ASIN does not need Approval')

            # ------------------------------ ???? ------------------------------ #
            try: 
                while driver.find_element_by_xpath('//*[@id="marathonUI"]/div/div/div/div[2]/section[2]/kat-alert').get_attribute('variant') == 'danger':
                    driver.get(url)
                    time.sleep(1)
            except:
                log('ASIN ok')

            # ------------------------------ Check Layout ------------------------------ #
            try:
                WebDriverWait(driver,2).until(EC.presence_of_element_located((By.XPATH,"//span[contains(text(),'You are currently viewing a new version of Add a P')]")))
                newLayout = True
                log('This product use NEW layout', True)
            except TimeoutException:
                log('This product use OLD layout', True)
                newLayout = False

            # ------------------------------ All attribute mode ------------------------------ # 
            # try:
            #     allAttributeRadio = driver.find_element_by_xpath(".//input[@type='radio' and @value='ALL_ATTRIBUTES_VIEW_MODE']")
            #     driver.execute_script("arguments[0].click();", allAttributeRadio)
            #     # time.sleep(1)
            #     if (allAttributeRadio is not None):
            #         break 
            # except NoSuchElementException:
            #     log(f'Cant find All Attribute element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
            #     continue   


            # ------------------------------ Advanced View Switch ------------------------------ # 
            try:
                advancedViewSwitch = driver.find_element_by_xpath(".//*[@id='advanced-view-switch']")
                advancedViewSwitch.click()
            except NoSuchElementException:
                log(f'Cant find Advanced View Switch element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue 

            # ------------------------------ Fulfill by Merchant ------------------------------ # 
            try:
                fbm = driver.find_element_by_xpath(".//input[@type='radio' and @value='MFN']")
                driver.execute_script("arguments[0].click();", fbm)
                # time.sleep(1)
                if (fbm is not None):
                    break 
            except NoSuchElementException:
                log(f'Cant find Fulfill by Merchant element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue


            # ------------------------------ Product Condition ------------------------------ #
            _count = 0
            while True:
                try:
                    if newLayout:
                        element = driver.find_element(By.XPATH, '//*[@name="condition_type-0-value"]')
                        newValue = 'new_new' 
                    else:
                        element = driver.find_element_by_xpath('//*[@id="condition_type"]')
                        newValue = 'new, new'
                    
                    action = ActionChains(driver)
                    action.move_to_element(element).perform()
                    element.click()
                    time.sleep(0.5)
                    action.send_keys(Keys.ARROW_DOWN,Keys.ARROW_DOWN,Keys.ENTER).perform()
                    _count += 1
                    dropdownValue = element.get_attribute('value')
                    log(f'dropdown value is: {dropdownValue}')
                    if (dropdownValue == newValue):
                        log('Product condition is now selected "New"')
                        break
                    # break after 10 times failed
                    if _count >= 10:
                        log('Cant find the element "New" after 10 times. Skip to next field...', True)
                        break
                    # time.sleep(1)
                except NoSuchElementException:
                    log(f'Cant find Product condition element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                    shouldContinue = True
                    break
            skipProductIfCan()

            # ------------------------------ Product SKU ------------------------------ #     
            try:
                if newLayout:
                    driver.find_element(By.XPATH,"//kat-input[@name='contribution_sku-0-value']").send_keys(line[2])
                else: 
                    driver.find_element_by_xpath('//*[@id="item_sku"]').send_keys(line[2])
                log('Import SKU: OK')
            except NoSuchElementException:
                log(f'Cant find Contribution SKU element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue        

            # ------------------------------ Handling Time ------------------------------ # 
            try:
                if newLayout:
                    driver.find_element(By.XPATH,"//kat-input[@id='fulfillment_availability#1.lead_time_to_ship_max_days']").send_keys("5")
                else: 
                    driver.find_element_by_xpath('//*[@id="fulfillment_latency"]').send_keys('5')
                log('Handling Time: OK')
            except NoSuchElementException:
                log(f'Cant find Handling time element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue

            # ------------------------------ Product Quantity ------------------------------ # 
            try:
                if newLayout:
                    driver.find_element(By.XPATH,"//kat-input[@id='fulfillment_availability#1.quantity']").send_keys("11")
                else: 
                    driver.find_element_by_xpath('//*[@id="quantity"]').send_keys('11')
                
                log('Quantity: OK')
            except NoSuchElementException:
                log(f'Cant find Quantity element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue

            # ------------------------------ Product Price ------------------------------ #
            try:
                if newLayout:
                    driver.find_element(By.XPATH,"//kat-input[@id='purchasable_offer#1.our_price#1.schedule#1.value_with_tax']").send_keys(line[1])     
                else: 
                    driver.find_element_by_xpath('//*[@id="standard_price"]').send_keys(line[1])
                
                log('Price: OK')
            except NoSuchElementException:
                log(f'Cant find Price element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue

            # ------------------------------ Save and Finish ------------------------------ #
            try:
                if newLayout:    
                    driver.find_element(By.XPATH,"//kat-button[@id='EditSaveAction']").click()
                else:
                    driver.find_element_by_xpath('//*[@id="EditSaveAction"]').click()
                countSuccess += 1
                log('Save and finish: OK')
                log(f'Product offer successfuly. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
            except NoSuchElementException:
                log(f'Cant find Save and finish element. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
                continue

            time.sleep(1)
        except Exception as e:
            log(f'Catched exception. Check stack trace below. {MOVE_TO_NEXT_PRODUCT_STRING}', True)
            f.write(e)
            continue
    log(f'End session! {countSuccess} / {productCount} / {row_count} (total) products offer successfully!', True)
    f.close()

