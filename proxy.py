import logging
import requests
import random
import pandas as pd
import os
import csv
from datetime import datetime
from io import StringIO
from bs4 import BeautifulSoup
from logs import logger
from dotenv import load_dotenv
from rich import print
from config import load_settings
from db import DatabaseManagerSettings, ProxySettings


# Load environment variables
load_dotenv()

# Load logger settings from .env file
LOG_DIR_PROXIES = os.getenv('LOG_DIR_PROXIES')

# Create logger object
logger = logger.get_logger(log_file=LOG_DIR_PROXIES, log_level=logging.INFO)


class ProxyScraper:
    def __init__(self) -> None:
        """
        Initializes the ProxyScraper class.
        """
        self.db_manager_settings = DatabaseManagerSettings()
    

    # Function to get proxy list from csv file and return random sample
    def get_proxy_list(self):
        """
        Function to get proxy list from csv file and return random sample
        """
        try:
            # Read number of proxies to use from database
            proxy_settings: pd.DataFrame = self.db_manager_settings.read_data(ProxySettings)
            number_of_proxies: int = proxy_settings['number_of_proxies'][0]
            self.db_manager_settings.close_connection()

            # Check if proxy list file exists
            proxy_list_file: str = load_settings()['proxy_settings']['proxy_list3']
            if not os.path.isfile(proxy_list_file):
                raise FileNotFoundError(f'Proxy list file not found: {proxy_list_file}')

            # Read proxy list from file
            proxy_list = []
            with open(proxy_list_file, 'r') as file:
                reader: csv.reader = csv.reader(file)
                proxy_list: list = [row[0] for row in reader]

            # Return random sample of proxies
            if len(proxy_list) == 0:
                raise ValueError('Proxy list is empty')
            return random.sample(proxy_list, k=number_of_proxies)
        except FileNotFoundError as e:
            logger.error(f'{e}')
            raise
        except ValueError as e:
            logger.error(f'{e}')
            raise
        except Exception as e:
            logger.error(f'{e}')
            raise


    # Function to check availability of proxies and return list of available proxies
    def check_proxies(self, proxies: list):
        """
        Function to check availability of proxies and return list of available proxies
        """
        if proxies is None:
            raise ValueError('Proxy list is empty')

        proxy_check_url: str = load_settings()['proxy_settings']['proxy_check_url']
        if proxy_check_url is None:
            raise ValueError('Proxy check URL is empty')

        start_time = datetime.now()
        
        available_proxies = []
        print(f'\n\t*** Number proxies to check: {len(proxies)} ***')
        for index, proxy in enumerate(proxies, start=1):
            if proxy is None:
                raise ValueError('Proxy is null')

            try:
                response: requests.models.Response = requests.get(proxy_check_url, proxies={"http": proxy, "https": proxy}, timeout=3)
                if response is None:
                    logger.error(f'Proxy {index} :: {proxy}  --  Null Response')
                elif response.status_code == 200:
                    logger.info(f'Proxy {index} :: {proxy}  --  Available')
                    available_proxies.append(response.json()["origin"])
                else:
                    logger.info(f'Proxy {index} :: {proxy}  --  Not Available ({response.status_code})')
            except requests.exceptions.ConnectTimeout as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Connect Timeout')
            except requests.exceptions.ConnectionError as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Connection Error')
            except requests.exceptions.InvalidURL as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Invalid URL')
            except requests.exceptions.ProxyError as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Proxy Error')
            except requests.exceptions.SSLError as e:
                logger.error(f'Proxy {index} :: {proxy}  --  SSL Error')
            except requests.exceptions.Timeout as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Timeout')
            except requests.exceptions.TooManyRedirects as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Too Many Redirects')
            except Exception as e:
                logger.error(f'Proxy {index} :: {proxy}  --  Unhandled Exception: {e}')

        end_time = datetime.now()
        logger.info(f'Total time to check all proxies: {end_time - start_time}')
        logger.info(f'Total available proxies for scraping: {len(available_proxies)}\n')
        return available_proxies



    # Function to get proxy list from API and return list of proxies
    def get_proxy_list_from_api(self):
        url: str = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&skip=0&proxy_format=protocolipport&format=json&limit=7"  # limit=20 = 20 proxies at once 

        headers: dict = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'sk-SK,sk;q=0.9,cs;q=0.8,en-US;q=0.7,en;q=0.6',
        'origin': 'https://proxyscrape.com',
        'priority': 'u=1, i',
        'referer': 'https://proxyscrape.com/',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        response: requests.models.Response = requests.request("GET", url, headers=headers)
        json_data: dict = response.json()
        start_point: list = json_data['proxies']

        list_proxies = []
        for point in start_point:
            proxies: str = f'{point['ip']}:{point['port']}'
            list_proxies.append(proxies)
        return list_proxies


# proxy_scraper = ProxyScraper()
# list_proxies = proxy_scraper.get_proxy_list_from_api()
# print(list_proxies)
# df = pd.DataFrame(list_proxies)
# df.to_csv('multi-cars-scraping/proxy_scraper_list1.csv', index=False)




class FreeProxyList:
    def __init__(self) -> None:
        pass


    def get_free_proxy_list(self):
        url = 'https://free-proxy-list.net'
        response: requests.models.Response = requests.get(url)
        soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
        table: BeautifulSoup = soup.find('table')

        proxy_list = []
        html_stringio: StringIO = StringIO(str(table))
        for index, row in enumerate(pd.read_html(html_stringio)[0].values):
            print(f'Proxy {index}: {row[0]}:{row[1]}')
            proxy_list.append(f'{row[0]}:{row[1]}')
        return proxy_list


    def check_proxies(self, url, proxies):
        available_proxies = []
        for index, proxy in enumerate(proxies, start=1):
            try:
                response: requests.models.Response = requests.get(url, proxies={"http": proxy, "https": proxy})
                if response.status_code == 200:
                    print(f'Num. {index} Available proxy: {proxy}')
                    available_proxies.append(response.json()["origin"])
            except:
                pass
                # print(f'Proxy {index} is not available: {proxy}')
        return available_proxies

            
            
# proxies = FreeProxyList().get_free_proxy_list()
# list_available_proxies = FreeProxyList().check_proxies(url = "http://httpbin.org/ip", proxies = proxies)
# df = pd.DataFrame(list_available_proxies)
# # print(df)
# df.to_csv('multi-cars-scraping/available_proxy1.csv', index=False)







