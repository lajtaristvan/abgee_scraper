import requests
import re
import random
import pandas as pd
from bs4 import BeautifulSoup
from math import ceil
from tqdm import tqdm
from user_agents import user_agent_list


class AbgeeScraper():

    def __init__(self, url):
        self.url = url

    
    def scraper(self):
        # Pick a random uer agent
        user_agent = random.choice(user_agent_list.user_agent_list)

        # Set the headers
        headers = {
            'User-Agent': user_agent
        }

        # This is the session
        s = requests.Session()

        # Login payload data
        login_data = {
            'login[username]': 'yourusername',
            'login[password]': 'yourpassword',
            'send': ''
        }
                 
        # Define the Login url    
        login_url = 'https://www.abgee.co.uk/customer/account/loginPost/'

        # Login request
        r = s.get(login_url, headers=headers)

        # Scrape the content            
        soup = BeautifulSoup(r.content, 'lxml')

        # form key added to payload
        login_data['form_key'] = soup.find('input', {'name': 'form_key'})['value']

        # post request to login page
        r = s.post(login_url, data=login_data, headers=headers)

        # Make a request in a session
        r = s.get(self.url, headers=headers)

        # Scrape the content to end page
        soup = BeautifulSoup(r.content, 'lxml')

        # Scrape the end page number
        try:
            end_page_number = int(soup.find('p', class_='toolbar-amount').find_all('span', class_='toolbar-number')[2].string.strip())
        except:
            end_page_number = 'no end page'

        # Define the sum page number
        sum_page_number = 72        

        # Define the end page number
        try:
            end_page = ceil((end_page_number / sum_page_number) + 1)
        except:
            end_page = 0

        # print(end_page_number)
        # print(sum_page_number)
        # print(end_page)
        
        # A list to productlinks
        productlinks = []

        # Iterate all productlinks between a range
        for x in range(1, end_page):
            
            # Make a request in a session 
            r = s.get(self.url + f'?p={x}&product_list_limit=72')

            # Scrape the content
            soup = BeautifulSoup(r.content, 'lxml')

            # Identify all products
            productlist = soup.find_all('strong', class_='product name product-item-name')

            # Save all links in productlinks list
            for item in productlist:
                for link in item.find_all('a', href=True):
                    productlinks.append(link['href'])
                    #print(link['href'])

        # A list to the scraping data
        list = []

        # Iterate all links in productlinks
        for link in tqdm(productlinks):
            # Make requests with headers in one sessions (s)
            r = s.get(link, headers=headers)

            # Scrape the content in the soup variable with 'lxml' parser
            soup = BeautifulSoup(r.content, 'lxml')

            # Scrape name
            try:
                name = str(soup.title.string.strip())
            except:
                name = ''

            # Scrape barcode
            try:
                barcode = str(soup.find('div', class_='ean-row').text.strip()[5:])
            except:
                barcode = ''

            # Scrape pack size
            try:
                pack_size = str(soup.find('div', class_='pack-size-row').text.strip()[11:])

                if pack_size == 'Each':
                    pack_size = 1
                else:
                    pack_size = int(pack_size[5:-2])
            except:
                pack_size = 1

            # Scrape netto unit price and origi price
            try:
                price = float(soup.find('span', class_='trade-price').text.strip()[1:])
                netto_unit_price_origi_price = float(round(price / pack_size, 2))
            except:
                netto_unit_price_origi_price = float()

            try:
                # Define the gross unit price and origi price
                gross_unit_price_origi_price = float(round(netto_unit_price_origi_price * 1.2, 2))
                        
                # VAT calculation
                vat = round(((gross_unit_price_origi_price - netto_unit_price_origi_price) / netto_unit_price_origi_price) * 100)
            except:
                pass                        

            # Scrape product code
            try:                
                product_code = str(soup.find('div', class_='sku').text.strip()[5:])
            except:
                product_code = ''

            # Scrape availability
            try:
                availability = bool(soup.find('span', class_='stock-level').find(text=re.compile("In")))
            except:
                availability = bool(False)

            # Define a dictionary for csv
            abgee = {                   
                'link': link,
                'name': name,
                'barcode': barcode,
                'pack_size': pack_size,
                'netto_unit_price_origi_price': netto_unit_price_origi_price,
                'gross_unit_price_origi_price': gross_unit_price_origi_price,
                'vat': vat,                
                'product_code': product_code,        
                'availability': availability
            }

            # Add the dictionary to the list every iteration
            list.append(abgee)

            # Print every iteration        
            print(
                '\n--------- Saving: ---------\n'             
                'link: ' + str(abgee['link']) + '\n'
                'name: ' + str(abgee['name']) + '\n'
                'barcode: ' + str(abgee['barcode']) + '\n'
                'pack size: ' + str(abgee['pack_size']) + '\n'
                'netto unit price origi price: ' + str(abgee['netto_unit_price_origi_price']) + '\n'
                'gross unit price origi price: ' + str(abgee['gross_unit_price_origi_price']) + '\n'
                'vat: ' + str(abgee['vat']) + '\n'                
                'availability: ' + str(abgee['availability']) + '\n'
            )
            
        # Make table to list
        df = pd.DataFrame(list)

        # Save to csv 
        df.to_csv(r'C:\WEBDEV\abgee_scraper\abgee.csv', mode='a', index=False, header=True)
        

get_abgee = AbgeeScraper('https://www.abgee.co.uk/products.html')

get_abgee.scraper()