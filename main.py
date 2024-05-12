from itertools import cycle
from typing import Iterator
import pandas as pd
from scraper import CheckNewItems, AaaAutoScraper, SautoScraper, TipCarsScraper
from db import DatabaseManagerSettings, CarData
from menu import MainMenu, CarsMenu
import logging
from datetime import datetime
from logs import logger
from dotenv import load_dotenv
import os
from rich import print
from db import ScrapingSettings, ProxySettings
from config import load_settings
from proxy import ProxyScraper
import requests


def main():
    main_menu: MainMenu = MainMenu()
    db_manager_settings: DatabaseManagerSettings = DatabaseManagerSettings()
    check_new_items: CheckNewItems = CheckNewItems()
    
    scraping_settings: pd.DataFrame = db_manager_settings.read_data(ScrapingSettings)
    request_call_limit: int = scraping_settings['request_call_limit'][0]
    request_period_seconds: int = scraping_settings['request_period_seconds'][0]
    requests_made: int = scraping_settings['requests_made'][0]
    number_of_attempts = scraping_settings['number_of_attempts'][0]
    db_manager_settings.close_connection()
    
    # Get base_url from settings file (ScrapingSettings)
    base_url_aaaauto: str = load_settings()['scraping_settings']['base_url_aaaauto']
    
    # Get base_url from settings file (ScrapingSettings)
    base_url_sauto: str = load_settings()['scraping_settings']['base_url_sauto']

    # Get base_url from settings file (ScrapingSettings)
    base_url_tipcars: str = load_settings()['scraping_settings']['base_url_tipcars']

    # Get list user_agents of headers for scraping from settings file (ScrapingSettings)
    headers_list: list = load_settings()['scraping_settings']['user_agents']
    headers_pool: Iterator = cycle(headers_list)
                    
    running_program: bool = True
    while running_program:
        site_id = main_menu.start_page_menu()
        # AaaAuto.cz
        if site_id == '1':
            aaaauto_scraper: AaaAutoScraper = AaaAutoScraper(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
            cars_menu: CarsMenu = CarsMenu()
            
            while True:
                print('\n\t *** AaaAuto Menu ***')
                choice: str = cars_menu.menu_cars()
                # Scrape Pages
                if choice == '1':
                    print('\n\t *** Enter start and end pages to check ***')
                    start_page: int = int(input('Enter start page: '))
                    end_page: int = int(input('Enter end page: '))
                    
                    # Get list of proxies for scraping
                    try:
                        proxy_list: list = ProxyScraper().get_proxy_list()
                    except Exception as e:
                        logger.error(f'Failed to get proxy list: {e}')
                    try:
                        available_proxies: list = ProxyScraper().check_proxies(proxies = proxy_list)
                    except Exception as e:
                        logger.error(f'Failed to check proxies: {e}')
                    proxy_pool: Iterator = cycle(available_proxies)
                    
                    list_cars: list = []
                    list_all_cars_details: list = []
                    start_time: datetime = datetime.now()
                    print('\t*** Start scraping all pages with proxies... ***')
                    for page in range(start_page, end_page + 1):
                        # Get proxy from pool
                        try:
                            proxy: str = next(proxy_pool)
                        except StopIteration:
                            logger.error('Proxy pool empty')
                            break
                        # Get headers from pool
                        headers: dict = next(headers_pool)
                        
                        try:
                            response: requests.models.Response = aaaauto_scraper.fetch_page(base_url_aaaauto, page, proxy, headers)
                        except Exception as e:
                            logger.error(f'Failed to fetch page: {e}')
                            break
                        if response is None:
                            logger.info(f'Page {page} not found. Skipping...\n')
                            break
                        try:
                            cars_details: dict = aaaauto_scraper.parse_page(response, page)
                        except Exception as e:
                            logger.error(f'Failed to parse page: {e}')
                            break
                        if cars_details is None:
                            logger.info(f'Page parse {page} not found. Skipping...\n')
                            break
                        list_cars.append(cars_details)
                    list_cars_details = aaaauto_scraper.edit_list_cars_details(list_cars)
                    end_time = datetime.now()
                    logger.info(f'Elapsed time for scraping: {end_time - start_time}')
                    logger.info(f'Total number of cars found: {len(list_cars_details)}\n')
                    
                    list_all_cars_details.extend(list_cars_details)
                    df_to_insert: pd.DataFrame = check_new_items.compare_details_with_db(list_all_cars_details)
                    logger.info('Process scraping was successfully completed')
                    logger.info('Total number of records to insert: %s', len(df_to_insert))

                    while True:
                        choice: str = cars_menu.sub_menu_cars()
                        # Show as DataFrame
                        if choice == '1':
                            print(df_to_insert)
                        # Add to DB
                        elif choice == '2':
                            db_manager_settings.insert_data(df=df_to_insert, Model=CarData)
                            db_manager_settings.close_connection()
                            logger.info(f"Data was successfully inserted. {df_to_insert.shape[0]} rows inserted.")
                        # Export to csv
                        elif choice == '3':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_csv(f'multi-cars-scraping/aaaauto_data_{unique_suffix}.csv', index=False, encoding='utf-8-sig')
                            logger.info('Data was successfully exported to csv')
                        # Export to xlsx
                        elif choice == '4':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_excel(f'multi-cars-scraping/aaaauto_data_{unique_suffix}.xlsx')
                            logger.info('Data was successfully exported to xlsx')
                        # Back
                        elif choice == '5':
                            break
                        
                # Display all data from DB
                elif choice == '2':
                    car_data: pd.DataFrame = db_manager_settings.read_data(CarData)
                    db_manager_settings.close_connection()
                    print(car_data)
                # Delete all data from DB
                elif choice == '3': 
                    db_manager_settings.delete_all_data(model=CarData)
                    db_manager_settings.close_connection()
                    logger.info('All data was successfully deleted from DB')
                # Back to Main Menu
                elif choice == '4':
                    break
        
        # SAuto.cz
        elif site_id == '2':
            sauto_scraper: SautoScraper = SautoScraper(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
            cars_menu: CarsMenu = CarsMenu()
            
            while True:
                print('\n\t *** SAuto Menu ***')
                choice: str = cars_menu.menu_cars()
                # Scrape Pages
                if choice == '1':
                    print('\n\t *** Enter start and end pages to check ***')
                    start_page: int = int(input('Enter start page: '))
                    end_page: int = int(input('Enter end page: '))
                    
                    # Get list of proxies for scraping
                    try:
                        proxy_list: list = ProxyScraper().get_proxy_list()
                    except Exception as e:
                        logger.error(f'Failed to get proxy list: {e}')
                    try:
                        available_proxies: list = ProxyScraper().check_proxies(proxies = proxy_list)
                    except Exception as e:
                        logger.error(f'Failed to check proxies: {e}')
                    proxy_pool: Iterator = cycle(available_proxies)
                    
                    list_cars: list = []
                    list_all_cars_details: list = []
                    start_time: datetime = datetime.now()
                    print('\t*** Start scraping all pages with proxies... ***')
                    for page in range(start_page, end_page + 1):
                        # Get proxy from pool
                        try:
                            proxy: str = next(proxy_pool)
                        except StopIteration:
                            logger.error('Proxy pool empty')
                            break
                        # Get headers from pool
                        headers: dict = next(headers_pool)
                        try:
                            response: requests.models.Response = sauto_scraper.fetch_page(base_url_sauto, page, proxy, headers)
                        except Exception as e:
                            logger.error(f'Failed to fetch page: {e}')
                            break
                        if response is None:
                            logger.info(f'Page {page} not found. Skipping...\n')
                            break
                        try:
                            cars_details: dict = sauto_scraper.get_parsed_data(response, page)
                        except Exception as e:
                            logger.error(f'Failed to parse page: {e}')
                            break
                        if cars_details is None:
                            logger.info(f'Page parse {page} not found. Skipping...\n')
                            break
                        list_cars.append(cars_details)
                    list_cars_details = sauto_scraper.edit_list_cars_details(list_cars)
                    end_time = datetime.now()
                    logger.info(f'Elapsed time for scraping: {end_time - start_time}')
                    logger.info(f'Total number of cars found: {len(list_cars_details)}\n')
                    
                    list_all_cars_details.extend(list_cars_details)
                    df_to_insert: pd.DataFrame = check_new_items.compare_details_with_db(list_all_cars_details)
                    logger.info('Process scraping was successfully completed')
                    logger.info('Total number of records to insert: %s', len(df_to_insert))

                    while True:
                        choice: str = cars_menu.sub_menu_cars()
                        # Show as DataFrame
                        if choice == '1':
                            print(df_to_insert)
                        # Add to DB
                        elif choice == '2':
                            db_manager_settings.insert_data(df=df_to_insert, Model=CarData)
                            db_manager_settings.close_connection()
                            logger.info(f"Data was successfully inserted. {df_to_insert.shape[0]} rows inserted.")
                        # Export to csv
                        elif choice == '3':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_csv(f'multi-cars-scraping/sauto_data_{unique_suffix}.csv', index=False, encoding='utf-8-sig')
                            logger.info('Data was successfully exported to csv')
                        # Export to xlsx
                        elif choice == '4':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_excel(f'multi-cars-scraping/sauto_data_{unique_suffix}.xlsx')
                            logger.info('Data was successfully exported to xlsx')
                        # Back
                        elif choice == '5':
                            break
                        
                # Display all data from DB
                elif choice == '2':        
                    car_data: pd.DataFrame = db_manager_settings.read_data(CarData)
                    db_manager_settings.close_connection()
                    print(car_data)
                # Delete all data from DB
                elif choice == '3': 
                    db_manager_settings.delete_all_data(model=CarData)
                    db_manager_settings.close_connection()
                    logger.info('All data was successfully deleted from DB')
                # Back to Main Menu
                elif choice == '4':
                    break
                
        # TipCars.com
        elif site_id == '3':
            tipcars_scraper: TipCarsScraper = TipCarsScraper(request_call_limit, request_period_seconds, requests_made, number_of_attempts)
            cars_menu: CarsMenu = CarsMenu()
            
            while True:
                print('\n\t *** TipCars Menu ***')
                choice: str = cars_menu.menu_cars()
                # Scrape Pages
                if choice == '1':
                    print('\n\t *** Enter start and end pages to check ***')
                    start_page: int = int(input('Enter start page: '))
                    end_page: int = int(input('Enter end page: '))
                    
                    # Get list of proxies for scraping
                    try:
                        proxy_list: list = ProxyScraper().get_proxy_list()
                    except Exception as e:
                        logger.error(f'Failed to get proxy list: {e}')
                    try:
                        available_proxies: list = ProxyScraper().check_proxies(proxies = proxy_list)
                    except Exception as e:
                        logger.error(f'Failed to check proxies: {e}')
                    proxy_pool: Iterator = cycle(available_proxies)

                    list_cars: list = []
                    list_all_cars_details: list = []
                    start_time: datetime = datetime.now()
                    print('\t*** Start scraping all pages with proxies... ***')
                    for page in range(start_page, end_page + 1):
                        # Get proxy from pool
                        try:
                            proxy: str = next(proxy_pool)
                        except StopIteration:
                            logger.error('Proxy pool empty')
                            break
                        # Get headers from pool
                        headers: dict = next(headers_pool)
                        try:
                            response: requests.models.Response = tipcars_scraper.fetch_page(base_url_tipcars, page, proxy, headers)
                        except Exception as e:
                            logger.error(f'Failed to fetch page: {e}')
                            break
                        if response is None:
                            logger.info(f'Page {page} not found. Skipping...\n')
                            break
                        try:
                            cars_details: dict = tipcars_scraper.parse_data(response, page)
                        except Exception as e:
                            logger.error(f'Failed to parse page: {e}')
                            break
                        if cars_details is None:
                            logger.info(f'Page parse {page} not found. Skipping...\n')
                            break
                        list_cars.append(cars_details)
                    list_cars_details = tipcars_scraper.edit_list_cars_details(list_cars)
                    end_time = datetime.now()
                    logger.info(f'Elapsed time for scraping: {end_time - start_time}')
                    logger.info(f'Total number of cars found: {len(list_cars_details)}\n')
                    
                    list_all_cars_details.extend(list_cars_details)
                    df_to_insert: pd.DataFrame = check_new_items.compare_details_with_db(list_all_cars_details)
                    logger.info('Process scraping was successfully completed')
                    logger.info('Total number of records to insert: %s', len(df_to_insert))
                    
                    while True:
                        choice: str = cars_menu.sub_menu_cars()
                        # Show as DataFrame
                        if choice == '1':
                            print(df_to_insert)
                        # Add to DB
                        elif choice == '2':
                            db_manager_settings.insert_data(df=df_to_insert, Model=CarData)
                            db_manager_settings.close_connection()
                            logger.info(f"Data was successfully inserted. {df_to_insert.shape[0]} rows inserted.")
                        # Export to csv
                        elif choice == '3':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_csv(f'multi-cars-scraping/tipcars_data_{unique_suffix}.csv', index=False, encoding='utf-8-sig')
                            logger.info('Data was successfully exported to csv')
                        # Export to xlsx
                        elif choice == '4':
                            unique_suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            df_to_insert.to_excel(f'multi-cars-scraping/tipcars_data_{unique_suffix}.xlsx')
                            logger.info('Data was successfully exported to xlsx')
                        # Back
                        elif choice == '5':
                            break
                        
                # Display all data from DB
                elif choice == '2':        
                    car_data: pd.DataFrame = db_manager_settings.read_data(CarData)
                    db_manager_settings.close_connection()
                    print(car_data)
                # Delete all data from DB
                elif choice == '3': 
                    db_manager_settings.delete_all_data(model=CarData)
                    db_manager_settings.close_connection()
                    logger.info('All data was successfully deleted from DB')
                # Back to Main Menu
                elif choice == '4':
                    break
        
        # Settings
        elif site_id == '4':
            while True:
                settings_id: str = main_menu.settings_menu()
                # Scraping Settings
                if settings_id == '1':
                    print('\n\t*** Scraping Settings ***')
                    # Get scraping_settings from settings file (ScrapingSettings)
                    scraping_settings: pd.DataFrame = db_manager_settings.read_data(ScrapingSettings)
                    
                    print(f'Current request call limit: {scraping_settings["request_call_limit"][0]}')
                    # Enter new number of request call limit
                    request_call_limit: int = int(input('Enter new number of request call limit: '))
                    # Update request call limit in DB
                    db_manager_settings.update_data(ScrapingSettings, {'request_call_limit': request_call_limit})
                    
                    print(f'Current request period seconds: {scraping_settings["request_period_seconds"][0]}')
                    # Enter new number of request period of seconds
                    request_period_seconds: int = int(input('Enter new number of request period of seconds: '))
                    # Update request period of seconds in DB
                    db_manager_settings.update_data(ScrapingSettings, {'request_period_seconds': request_period_seconds})
                    
                    print(f'Current requests made: {scraping_settings["requests_made"][0]}')
                    # Enter new number of requests made
                    requests_made: int = int(input('Enter new number of requests made: '))
                    # Update requests made in DB
                    db_manager_settings.update_data(ScrapingSettings, {'requests_made': requests_made})
                    
                    print(f'Current scraping number of attempts: {scraping_settings["number_of_attempts"][0]}')
                    # Enter new number of attempts
                    number_of_attempts: int = int(input('Enter new number of attempts: '))
                    # Update number of attempts in DB
                    db_manager_settings.update_data(ScrapingSettings, {'number_of_attempts': number_of_attempts})
                    
                    # Close DB connection
                    db_manager_settings.close_connection()
                    logger.info('Settings were successfully updated')
                    
                # Proxy Settings
                elif settings_id == '2':
                    print('\n\t*** Proxy Settings ***')
                    # Get proxy_settings from settings file (ProxySettings)
                    proxy_settings: pd.DataFrame = db_manager_settings.read_data(ProxySettings)
                    
                    print(f'Current number of proxies: {proxy_settings["number_of_proxies"][0]}')
                    # Enter new number of proxies
                    number_of_proxies: int = int(input('Enter number of proxies: '))
                    # Update number of proxies in DB
                    db_manager_settings.update_data(ProxySettings, {'number_of_proxies': number_of_proxies})
                    
                    # Close DB connection
                    db_manager_settings.close_connection()
                    logger.info('Settings were successfully updated')

                # Logging Settings
                elif settings_id == '3':
                    print('\n\t*** Logging Settings ***')
                # Back
                elif settings_id == '4':
                    break
                
        # Exit
        elif site_id == '5':
            running_program = False
    
    
# Start program
if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Load logger settings from .env file
    LOG_DIR_MAIN = os.getenv('LOG_DIR_MAIN')
    
    # Create logger object
    logger = logger.get_logger(log_file=LOG_DIR_MAIN, log_level=logging.INFO)
    
    # Run program
    main()