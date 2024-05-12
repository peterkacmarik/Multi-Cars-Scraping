from consolemenu import *
from consolemenu.items import *
from rich import print



class MainMenu:
    def __init__(self):
        pass
    
    def start_page_menu(self):
        """
        Displays a menu with options for the user to select a site to scrape.
        
        Returns:
            str: The user's selected site ID.
        """
        options = ('AaaAuto.cz', 'SAuto.cz', 'TipCars.com', 'Settings', 'Exit')
        print('\n\t *** Select site to scrape: ***')
        for idx, site in enumerate(options, 1):
            print(f'\t{idx}. {site}')

        site_id: str = input('Enter number: ')
        return site_id
    
    def settings_menu(self):
        """
        Displays a menu with options for the user to select settings.
        
        Returns:
            str: The user's selected settings option.
        """
        options = ('Scraping Settings', 'Proxy Settings', 'Logging Settings', 'Back')
        print('\n\t*** Settings ***')
        for index, option in enumerate(options, 1):
            print(f'\t{index}. {option}')
            
        settings_id: str = input('Enter option: ')
        return settings_id
        
        
class CarsMenu:
    def __init__(self):
        pass
    
    def menu_cars(self):
        """
        Displays a menu with options for the user to select from when working with cars.
        
        Returns:
            str: The user's selected option from the menu.
        """
        options = ('Scrape Pages', 'Display All Data from DB', 'Delete All Data from Table', 'Back to Main Menu')
        for index, option in enumerate(options, 1):
            print(f'\t{index}. {option}')
        
        choice: str = input('Enter option: ')
        return choice

    def sub_menu_cars(self):
        """
        A function that displays a sub-menu with options for working with cars.
        
        Returns:
            str: The user's selected option from the sub-menu.
        """
        options = ('Show as DataFrame', 'Add to DB', 'Export to csv', 'Export to xlsx', 'Back')
        print('\n\t*** Options ***')
        for idx, option in enumerate(options, 1):
            print(f'\t{idx}. {option}')

        choice: str = input('Enter option: ')
        return choice
