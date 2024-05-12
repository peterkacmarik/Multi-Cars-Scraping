from datetime import datetime
import time
import traceback
from typing import Iterator
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import logging
from db import DatabaseManagerSettings, CarData
from itertools import cycle
from proxy import ProxyScraper
from logs import logger
from dotenv import load_dotenv
import os
from rich import print
from config import load_settings


# Load environment variables
load_dotenv()

# Load logger settings from .env file
LOG_DIR_SCRAPING = os.getenv('LOG_DIR_SCRAPING')

# Create logger object
logger = logger.get_logger(log_file=LOG_DIR_SCRAPING, log_level=logging.INFO)


class Scraper:
    def __init__(self, request_call_limit: int, request_period_seconds: int, requests_made: int, number_of_attempts: int) -> None:
        """
        Initializes a new instance of the class.

        Args:
            request_call_limit (int): The maximum number of requests that can be made to the server within a certain period of time.
            request_period_seconds (int): The duration of the period in seconds.
            requests_made (int): The number of requests made to the server during the current period.
            number_of_attempts (int): The number of times the scraper will attempt to fetch a page before giving up.

        Returns:
            None
        """
        self.request_call_limit = request_call_limit
        self.request_period_seconds = request_period_seconds
        self.requests_made = requests_made  # Tracking the number of requests your scraper sent to the server during a certain period of time
        self.last_request_time = None
        self.number_of_attempts = number_of_attempts
    
    def fetch_page(self, base_url: str, page_url: str, proxy: str, headers: dict):
        """
        Fetches a web page using the specified proxy and headers.

        Args:
            base_url (str): The base URL of the website.
            page_url (str): The URL of the page to fetch.
            proxy (str): The proxy to use for the request.
            headers (dict): The headers to include in the request.

        Returns:
            str: The content of the fetched page as a string, or None if the page could not be fetched.
        """
        logger.info(f'Using proxy for scraping: {proxy}')
        logger.info(f'Fetching page: {page_url}')
        
        # Obmedzenie počtu volaní
        if self.requests_made >= self.request_call_limit:
            time_elapsed = time.time() - self.last_request_time
            if time_elapsed < self.request_period_seconds:
                time.sleep(self.request_period_seconds - time_elapsed)
            self.requests_made = 0
        
        # Opätovné skúšanie
        for attempt in range(self.number_of_attempts):  # Počet pokusov
            try:
                try:
                    response: requests.models.Response = requests.get(url=base_url + str(page_url), proxies={"http": f'{proxy}'}, headers=headers)
                except Exception as e:
                    logger.error(f'Failed to get page: {e}')
                    logger.error(traceback.format_exc())
                    return None
                if response is None:
                    logger.error('Fetched page is None')
                    return None
                try:
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f'Failed to get page: {e}')
                    logger.error(traceback.format_exc())
                    return None
                
                self.requests_made += 1
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response.text
            except requests.exceptions.RequestException as e:
                wait: int = 2 ** attempt  # Exponenciálne zvyšovanie času čakania
                time.sleep(wait)
        return None

    def edit_list_cars_details(self, list_cars: list):
        """
        Edits the details of a list of cars by creating a new list of rows.

        Parameters:
            list_cars (list): A list of dictionaries representing car details.

        Returns:
            list: A list of dictionaries representing the edited car details.

        Raises:
            Exception: If there is an error getting the number of values from detail_dict.
            KeyError: If there is an error creating a row from detail_dict.
        """
        all_rows = []
        for detail_dict in list_cars:
            try:
                num_values: int = len(next(iter(detail_dict.values())))
            except:
                logger.exception('Error getting number of values from detail_dict')
                raise
            
            for index in range(num_values):
                try:
                    row: dict = {key: detail_dict[key][index] for key in detail_dict}
                except KeyError:
                    logger.exception('Error creating row from detail_dict')
                    raise
                all_rows.append(row)
        return all_rows
    
    
class AaaAutoScraper(Scraper):
    def __init__(self, request_call_limit: int, request_period_seconds: int, requests_made: int, number_of_attempts: int) -> None:
        """
        Initializes a new instance of the class.

        Args:
            request_call_limit (int): The maximum number of requests that can be made to the server within a certain period of time.
            request_period_seconds (int): The duration of the period in seconds.
            requests_made (int): The number of requests made to the server during the current period.
            number_of_attempts (int): The number of times the scraper will attempt to fetch a page before giving up.

        Returns:
            None
        """
        super().__init__(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
        
    def fetch_page(self, base_url: str, page_url: str, proxy: str, headers: dict):
        """
        Fetches a web page using the specified base URL, page URL, proxy, and headers.

        Args:
            base_url (str): The base URL of the website.
            page_url (str): The URL of the page to fetch.
            proxy (str): The proxy to use for the request.
            headers (dict): The headers to include in the request.

        Returns:
            str: The content of the fetched page as a string, or None if the page could not be fetched.
        """
        return super().fetch_page(base_url, page_url, proxy, headers)
    
    def parse_page(self, response: requests.models.Response, page_url: str):
        """
        Parses the content of a web page to extract car information.

        Args:
            response (requests.models.Response): The response object containing the web page content.
            page_url (str): The URL of the web page.

        Returns:
            dict or None: A dictionary containing the extracted car information, with the following keys:
                - 'znacka' (list): The list of car brands.
                - 'model' (list): The list of car models.
                - 'rok' (list): The list of car years.
                - 'km' (list): The list of car mileages.
                - 'palivo' (list): The list of car fuel types.
                - 'prevodovka' (list): The list of car transmission types.
                - 'vykon_motora' (list): The list of car engine power outputs.
                - 'objem_motora' (list): The list of car engine displacements.
                - 'cena' (list): The list of car prices.
                - 'url' (list): The list of car URLs.
                - 'krajina' (list): The list of car countries (all set to 'Czech Republic').
                - 'datum_pridania' (list): The list of dates the car information was added.

                If the page does not contain any car information, None is returned.
        """
        logger.info(f'Parsing page: {page_url}\n')
        
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        start_point = soup.find_all('div', class_ = 'card box')
        
        result: BeautifulSoup = soup.find('nav', class_ = 'pagenav noprint center')

        if result is not None:
            # no_result = result.find_all('a')[9]['href']
            # print(no_result)
        
            list_cars = {
                'znacka': [],
                'model': [],
                'rok': [],
                'km': [],
                'palivo': [],
                'prevodovka': [],
                'vykon_motora': [],
                'objem_motora': [],
                'cena': [],
                'url': [],
                'krajina': [],
                'datum_pridania': [],
            }
            for car_item in start_point:
                try:
                    list_cars['znacka'].append(car_item.find('a', class_ = 'primary notranslate').text.split()[0])
                except:
                    list_cars['znacka'].append(np.nan)
                try:
                    list_cars['model'].append(car_item.find('a', class_ = 'primary notranslate').text.split(',')[0].split('\n\n\t\t\t\t\t').pop().strip().replace('\n\t\t\t\t\t\n\t\t\t\t\t', ' ')) 
                except:
                    list_cars['model'].append(np.nan)
                try:    
                    list_cars['rok'].append(car_item.find('a', class_ = 'primary notranslate').text.split(',')[1].strip())
                except:
                    list_cars['rok'].append(np.nan)
                try:
                    list_cars['km'].append(car_item.find('ul', class_ = 'carFeaturesList').li.text.replace('km', '').replace(' ', '').strip())
                except:
                    list_cars['km'].append(np.nan)
                try:
                    list_cars['palivo'].append(car_item.find('ul', class_ = 'carFeaturesList').find('li', class_ = 'odd').next_sibling.next_sibling.text.strip().replace('\n\t\t\t\t\t\t', ''))
                except:
                    list_cars['palivo'].append(np.nan)
                try:
                    list_cars['prevodovka'].append(car_item.find('ul', class_ = 'carFeaturesList').find_all('li', class_ = 'odd')[0].text.split('/')[0].strip())
                except:
                    list_cars['prevodovka'].append(np.nan)
                try:
                    list_cars['vykon_motora'].append(car_item.find('ul', class_ = 'carFeaturesList').find('li', class_ = 'odd').next_sibling.next_sibling.next_sibling.next_sibling.text.split('/')[1].replace(', 4x4', '').strip().replace('kW', ''))
                except:
                    list_cars['vykon_motora'].append(np.nan)
                try:
                    list_cars['objem_motora'].append(car_item.find('ul', class_ = 'carFeaturesList').find('li', class_ = 'odd').next_sibling.next_sibling.next_sibling.next_sibling.text.split('/')[0].strip())
                except:
                    list_cars['objem_motora'].append(np.nan)
                try:
                    list_cars['cena'].append(car_item.find('h3', class_ = 'notranslate').text.replace('Kč', '').strip().replace(' ', ''))
                except:
                    list_cars['cena'].append(np.nan)
                try:
                    list_cars['url'].append(car_item.find('a', class_ = 'primary notranslate').get('href'))
                except:
                    list_cars['url'].append(np.nan)
                list_cars['krajina'].append('Czech Republic')
                list_cars['datum_pridania'].append(datetime.now().date())
            
            return list_cars
        else:
            result: BeautifulSoup = soup.find_all('div', class_ = 'paragraphWithIcon')
            no_result: str = result[0].h3.text
            # print('Page not found:', no_result)
            return None
    
    def edit_list_cars_details(self, list_cars: list):
        """
        Edit the details of a list of cars by creating a new list of rows.

        Parameters:
            list_cars (list): A list of dictionaries representing car details.

        Returns:
            list: A list of dictionaries representing the edited car details.
        """
        return super().edit_list_cars_details(list_cars)


class CheckNewItems:
    def __init__(self) -> None:
        """
        Initializes the CheckNewItems class.
        """
        self.db_manager_settings  = DatabaseManagerSettings()
    
    def compare_details_with_db(self, cars_details: list):
        """
        Compares the given list of car details with the database and returns a dataframe of new details to insert.

        Parameters:
            cars_details (list): A list of dictionaries representing car details.

        Returns:
            pd.DataFrame: A dataframe containing the new car details to insert into the database.

        Raises:
            ValueError: If the cars_details parameter is empty.
            TypeError: If the cars_details parameter is not a list.
            Exception: If an unexpected error occurs during the comparison process.
        """
        print('\t*** Start comparing details with database ***')
        if not cars_details:
            logger.error('The parameter cars_details cannot be empty')
            # raise ValueError('The parameter cars_details cannot be empty')
        if not isinstance(cars_details, list):
            logger.error('The parameter cars_details must be a list')
            # raise TypeError('The parameter cars_details must be a list')

        # Create dataframe from list
        df: pd.DataFrame = pd.DataFrame(cars_details)
        
        # Create blank dataframe to store new details
        column_names: list = ['znacka', 'model', 'rok', 'km', 'palivo', 'prevodovka', 'vykon_motora', 'objem_motora', 'cena', 'url', 'krajina', 'datum_pridania']
        df_to_insert: pd.DataFrame = pd.DataFrame(columns=column_names)
        
        start_time = datetime.now()

        try:
            for index, row in df.iterrows():
                # Get URL
                url: str = row['url']
                # Check if URL already exists in the database
                df_database: pd.DataFrame = self.db_manager_settings.read_data(model=CarData, conditions=CarData.url == url)
                                
                if url not in df_database['url'].values:
                    logger.info(f'New URL found: {url}')
                    # If a new URL is found, return the corresponding row
                    row_to_insert: pd.DataFrame = pd.DataFrame([row.values], columns=column_names)
                    df_to_insert: pd.DataFrame = pd.concat([df_to_insert, row_to_insert], ignore_index=True)
                
                if url in df_database['url'].values:
                    logger.info(f'Skipping... URL already exists in the database: {url}')
                    continue
                
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise
        
        self.db_manager_settings.close_connection()
        end_time = datetime.now()
        logger.info(f'Elapsed time for comparing details with database: {end_time - start_time}')
        return df_to_insert

    
class SautoScraper(Scraper):
    def __init__(self, request_call_limit: int, request_period_seconds: int, requests_made: int, number_of_attempts: int) -> None:
        """
        Initializes a new instance of the class.

        Args:
            request_call_limit (int): The maximum number of requests that can be made to the server within a certain period of time.
            request_period_seconds (int): The duration of the period in seconds.
            requests_made (int): The number of requests made to the server during the current period.
            number_of_attempts (int): The number of times the scraper will attempt to fetch a page before giving up.

        Returns:
            None
        """
        super().__init__(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
    
    def fetch_page(self, base_url: str, page_url: str, proxy: str, headers: dict):
        """
        Fetches a web page using the specified base URL, page URL, proxy, and headers.

        Args:
            base_url (str): The base URL of the website.
            page_url (str): The URL of the page to fetch.
            proxy (str): The proxy to use for the request.
            headers (dict): The headers to include in the request.

        Returns:
            str: The content of the fetched page as a string, or None if the page could not be fetched.
        """
        return super().fetch_page(base_url, page_url, proxy, headers)
    
    def get_parsed_data(self, response: str, page: int):
        """
        Parses the given response and extracts data from it.

        Args:
            response (str): The response to parse.
            page (int): The page number.

        Returns:
            dict: A dictionary containing the parsed data. The dictionary has the following keys:
                - 'znacka' (list): A list of car brands.
                - 'model' (list): A list of car models.
                - 'rok' (list): A list of car years.
                - 'km' (list): A list of car mileages.
                - 'palivo' (list): A list of car fuels.
                - 'prevodovka' (list): A list of car transmissions.
                - 'vykon_motora' (list): A list of car engine power values.
                - 'objem_motora' (list): A list of car engine displacement values.
                - 'cena' (list): A list of car prices.
                - 'url' (list): A list of car URLs.
                - 'krajina' (list): A list of countries.
                - 'datum_pridania' (list): A list of dates when the cars were added.

            Returns None if the response does not contain any data.
        """
        logger.info(f'Start parsing page {page}\n')
        
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        start_point: list = soup.find_all('div', class_='c-item__data-wrap')
        
        result: BeautifulSoup = soup.find('h1', class_ = 'c-error-box__title')
        
        if result is None:
            parsed_data = {
                    'znacka': [],
                    'model': [],
                    'rok': [],
                    'km': [],
                    'palivo': [],
                    'prevodovka': [],
                    'vykon_motora': [],
                    'objem_motora': [],
                    'cena': [],
                    'url': [],
                    'krajina': [],
                    'datum_pridania': [],
                }
            for point in start_point:
                try:
                    parsed_data['znacka'].append(point.find('span', class_='c-item__name c-item__name--hide').text.split(',')[0].split(' ')[0])
                except:
                    parsed_data['znacka'].append(np.nan)
                try:
                    parsed_data['model'].append(point.find('span', class_='c-item__name c-item__name--hide').text.split(',')[0].split(' ')[1])
                except:
                    parsed_data['model'].append(np.nan)
                try:
                    parsed_data['rok'].append(point.find('div', class_='c-item__info').text.split(',')[0])
                except:
                    parsed_data['rok'].append(np.nan)
                try:
                    parsed_data['km'].append(point.find('div', class_='c-item__info').text.split(',')[1].replace('km', '').strip().replace('\xa0', ''))
                except:
                    parsed_data['km'].append(np.nan)
                try:
                    parsed_data['palivo'].append(point.find('span', class_='c-item__info-mobile-medium').text.replace(', ', ''))
                except:
                    parsed_data['palivo'].append(np.nan)
                try:
                    parsed_data['prevodovka'].append(point.find('span', class_='c-item__info-mobile-wide').text.replace(', ', ''))
                except:
                    parsed_data['prevodovka'].append(np.nan)
                parsed_data['vykon_motora'].append(np.nan)
                try:
                    parsed_data['objem_motora'].append(point.find('span', class_='c-item__name--suffix').text.split(',')[0])
                except:
                    parsed_data['objem_motora'].append(np.nan)
                try:
                    parsed_data['cena'].append(point.find('div', class_='notranslate c-item__price').text.replace('\xa0', '').replace(' Kč', ''))
                except:
                    parsed_data['cena'].append(np.nan)
                try:
                    parsed_data['url'].append(point.find('a', class_='sds-surface sds-surface--clickable sds-surface--00 c-item__link')['href'])
                except:
                    parsed_data['url'].append(np.nan)
                parsed_data['krajina'].append('Czech Republic')
                parsed_data['datum_pridania'].append(datetime.now().date())
                    
            return parsed_data
        else:
            return None

    def edit_list_cars_details(self, list_cars: list):
        """
        Edits the details of a list of cars by creating a new list of rows.

        Parameters:
            list_cars (list): A list of dictionaries representing car details.

        Returns:
            list: A list of dictionaries representing the edited car details.

        Raises:
            Exception: If there is an error getting the number of values from detail_dict.
            KeyError: If there is an error creating a row from detail_dict.
        """
        return super().edit_list_cars_details(list_cars)


class TipCarsScraper(Scraper):
    def __init__(self, request_call_limit: int, request_period_seconds: int, requests_made: int, number_of_attempts: int) -> None:
        """
        Initializes a new instance of the class.

        Args:
            request_call_limit (int): The maximum number of requests that can be made to the server within a certain period of time.
            request_period_seconds (int): The duration of the period in seconds.
            requests_made (int): The number of requests made to the server during the current period.
            number_of_attempts (int): The number of times the scraper will attempt to fetch a page before giving up.

        Returns:
            None
        """
        super().__init__(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
        
    def fetch_page(self, base_url: str, page_url: str, proxy: str, headers: dict):
        """
        Fetches a page from the given base URL and page URL using the specified proxy and headers.

        Args:
            base_url (str): The base URL of the website.
            page_url (str): The URL of the page to fetch.
            proxy (str): The proxy to use for the request.
            headers (dict): The headers to include in the request.

        Returns:
            The response object from the fetched page.
        """
        return super().fetch_page(base_url, page_url, proxy, headers)
    
    def parse_data(self, response: requests.models.Response, page_url: str):
        """
        Parses the data from a web page response and extracts car details.

        Args:
            response (requests.models.Response): The response object containing the web page data.
            page_url (str): The URL of the web page.

        Returns:
            dict: A dictionary containing the extracted car details. The dictionary has the following keys:
                - 'znacka' (list): The list of car brands.
                - 'model' (list): The list of car models.
                - 'rok' (list): The list of car years.
                - 'km' (list): The list of car mileages.
                - 'palivo' (list): The list of car fuel types.
                - 'prevodovka' (list): The list of car transmission types.
                - 'vykon_motora' (list): The list of car engine power values.
                - 'objem_motora' (list): The list of car engine displacement values.
                - 'cena' (list): The list of car prices.
                - 'url' (list): The list of car URLs.
                - 'krajina' (list): The list of car countries.
                - 'datum_pridania' (list): The list of dates when the car details were added.

                If the end_page element is found in the web page, the function extracts the car details from the web page
                and returns the dictionary. If the end_page element is not found, the function returns None.

                Note: If an error occurs while extracting a specific car detail, the corresponding value in the dictionary
                will be set to np.nan.

        """
        logger.info(f'Parsing page: {page_url}\n')
        
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        all_cars_list = soup.find_all('a', class_='w-100 float-l')
        
        end_page = soup.find('i', class_='icon-doprava')
        if end_page is not None:
        
            cars_list = {
                'znacka': [],
                'model': [],
                'rok': [],
                'km': [],
                'palivo': [],
                'prevodovka': [],
                'vykon_motora': [],
                'objem_motora': [],
                'cena': [],
                'url': [],
                'krajina': [],
                'datum_pridania': [],
            }
            for car in all_cars_list:
                model = car.find('h2', class_='fs-20px lh-19 fs-tucne').text
                for index, title in enumerate(model.split()):
                    if len(model.split()) == 2:
                        if index == 0:
                            try:
                                cars_list['znacka'].append(title)
                            except:
                                cars_list['znacka'].append(np.nan)
                        elif index == 1:
                            try:
                                cars_list['model'].append(' '.join(model.split()[1:]))
                            except:
                                cars_list['model'].append(np.nan)
                    elif len(model.split()) > 2:
                        if index == 0:
                            try:
                                cars_list['znacka'].append(title)
                            except:
                                cars_list['znacka'].append(np.nan)
                        elif index == 1:
                            try:
                                cars_list['model'].append(' '.join(model.split()[1:]))
                            except:
                                cars_list['model'].append(np.nan)
                try:
                    cars_list['rok'].append(car.find_all_next('div', class_='w-100 boxiky_s_udaji')[0].text.strip())
                except:
                    cars_list['rok'].append(np.nan)
                try:
                    cars_list['km'].append(car.find_all_next('div', class_='w-100 boxiky_s_udaji')[1].text.replace(' tkm', '000').replace(' km', '').strip())
                except:
                    cars_list['km'].append(np.nan)
                try:
                    cars_list['palivo'].append(car.find_all_next('div', class_='w-100 boxiky_s_udaji')[4].text.strip())
                except:
                    cars_list['palivo'].append(np.nan)
                cars_list['prevodovka'].append(np.nan)
                try:
                    cars_list['vykon_motora'].append(car.find_all_next('div', class_='w-100 boxiky_s_udaji')[2].text.replace(' kW', '').strip())
                except:
                    cars_list['vykon_motora'].append(np.nan)
                try:
                    cars_list['objem_motora'].append(car.find_all_next('div', class_='w-100 boxiky_s_udaji')[3].text.strip())
                except:
                    cars_list['objem_motora'].append(np.nan)
                try:
                    cars_list['cena'].append(car.find('div', class_='fs-22px lh-19 fs-tucne mb-5').text.replace('\xa0', '').replace('Kč', '').strip())
                except:
                    cars_list['cena'].append(np.nan)
                try:
                    cars_list['url'].append('https://www.tipcars.com' + car.get('href'))
                except:
                    cars_list['url'].append(np.nan)
                cars_list['krajina'].append('Czech Republic')
                cars_list['datum_pridania'].append(datetime.now().date())
                
            return cars_list
        else:
            return None
        
    def edit_list_cars_details(self, list_cars: list):
        """
        Edits the details of a list of cars by creating a new list of rows.

        Parameters:
            list_cars (list): A list of dictionaries representing car details.

        Returns:
            list: A list of dictionaries representing the edited car details.
        """
        return super().edit_list_cars_details(list_cars)

    