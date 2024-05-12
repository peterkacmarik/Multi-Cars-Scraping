# Multi-Cars Scraping

This project is a web scraper for multiple car websites. It uses Python and several libraries such as `pandas`, `requests`, and more...

## Features

- Scrapes car data from multiple websites (AaaAuto, Sauto, TipCars).
- Uses a pool of proxies and user-agents for scraping.
- Allows the user to specify the start and end pages for scraping.
- Checks and compares scraped data with existing data in the database.
- Provides options to display, add, and delete data from the database.
- Exports scraped data to CSV and XLSX files.

## Modules

- `scraper`: Contains the `CheckNewItems`, `AaaAutoScraper`, `SautoScraper`, and `TipCarsScraper` classes for scraping car data.
- `db`: Contains the `DatabaseManagerSettings` and `CarData` classes for managing the database.
- `menu`: Contains the `MainMenu` and `CarsMenu` classes for the user interface.
- `logs`: Contains the `logger` for logging information and errors.
- `config`: Contains the `load_settings` function for loading settings from a file.
- `proxy`: Contains the `ProxyScraper` class for getting and checking proxies.

## Usage

Run the `main.py` script. The main menu will be displayed where you can choose the website to scrape. In the car menu, you can choose to scrape pages, display all data from the database, delete all data from the database, or go back to the main menu.

## Note

This project is for educational purposes only. Always respect the terms of use of the websites you are scraping.
