import pandas as pd
import logging
from dotenv import load_dotenv
import os
from logs import logger
from rich import print
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, Date, Enum, Float, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base


# Load environment variables
load_dotenv()

# Load logger settings from .env file
LOG_DIR_DATABASE = os.getenv('LOG_DIR_DATABASE')

# Create logger object
logger = logger.get_logger(log_file=LOG_DIR_DATABASE, log_level=logging.INFO)

# Database tables definition (declarative base)
Base = declarative_base()

class CarData(Base):
    __tablename__ = 'car_data_from_multiple_sources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    znacka = Column(Text)
    model = Column(Text)
    rok = Column(Text)
    km = Column(Text)
    palivo = Column(Text)
    prevodovka = Column(String)
    vykon_motora = Column(Text)
    objem_motora = Column(Text)
    cena = Column(Text)
    url = Column(Text)
    krajina = Column(Text)
    datum_pridania = Column(DateTime)

class ScrapingSettings(Base):
    __tablename__ = 'scraping_settings'
    id = Column(Integer, primary_key=True)
    request_call_limit = Column(Integer)
    request_period_seconds = Column(Integer)
    requests_made = Column(Integer)
    number_of_attempts = Column(Integer)

class ProxySettings(Base):
    __tablename__ = 'proxy_settings'
    id = Column(Integer, primary_key=True)
    number_of_proxies = Column(Integer)
    

class LoggingSettings(Base):
    __tablename__ = 'logging_settings'
    id = Column(Integer, primary_key=True)
    log_level = Column(String)


class DatabaseManagerSettings:
    def __init__(self):
        """
        Initializes the DatabaseManagerSettings class.
        This method loads environment variables using the `load_dotenv` function from the `dotenv` module. 
        It retrieves the database URL from the `DATABASE_URL` environment variable using the `os.getenv` function. 
        It creates an engine using the `create_engine` function from the `sqlalchemy` module, passing the database URL as an argument. 
        It creates a session using the `sessionmaker` function from the `sqlalchemy.orm` module, binding it to the engine. 
        Finally, it creates a session using the `Session` class and assigns it to the `session` attribute of the class.
        """
        load_dotenv()  # Load environment variables
        db_url = os.getenv('DATABASE_URL')  # Retrieve the database URL
        self.engine = create_engine(db_url)  # Create an engine
        self.Session = sessionmaker(bind=self.engine)  # Create a session
        self.session = self.Session()  # Assign the session to the class

    def create_table(self, table: Table):
        """
        Creates a table in the database using the provided Table object.
        
        Args:
            table (Table): The Table object representing the table to be created.
        """
        table.create(self.engine)


    # def insert_data(self, obj):
    #     """Vloží objekt (riadok) do tabuľky."""
    #     self.session.add(obj)
    #     self.session.commit()

    
    def insert_data(self, df: pd.DataFrame, Model: declarative_base):
        """
        Inserts data from a pandas DataFrame into a database table using the provided Model.
        
        Parameters:
            df (pd.DataFrame): The DataFrame containing the data to be inserted.
            Model (declarative_base): The SQLAlchemy model representing the table schema.
        """
        for _, row in df.iterrows():
            obj = Model(**row.to_dict())
            self.session.add(obj)
        self.session.commit()

    def read_data(self, model, conditions=None):
        """
        Reads data from the specified model in the database based on optional conditions.

        Parameters:
            model (DeclarativeMeta): The model class to query.
            conditions (Optional[BinaryExpression]): The optional conditions to filter the query results.

        Returns:
            pandas.DataFrame: The queried data as a DataFrame.
        """
        query = self.session.query(model)
        if conditions:
            query = query.filter(conditions)
        data = pd.read_sql(query.statement, self.session.bind)
        return data

    def update_data(self, model, updates):
        """
        Updates data in the database table based on the provided model and updates.

        Parameters:
            model (DeclarativeMeta): The SQLAlchemy model representing the table schema.
            updates (dict): A dictionary containing the column names and their corresponding new values.
        """
        self.session.query(model).update(updates, synchronize_session=False)
        self.session.commit()
        
    # def update_data(self, model, conditions, updates):
    #     """Aktualizuje dáta v tabuľke podľa podmienok."""
    #     self.session.query(model).filter(conditions).update(updates)
    #     self.session.commit()

    # def delete_data(self, model, conditions):
    #     """Vymaže dáta z tabuľky podľa podmienok."""
    #     self.session.query(model).filter(conditions).delete()
    #     self.session.commit()
        
    def delete_all_data(self, model):
        """
        Deletes all data from the specified model in the database.
        
        Parameters:
            model: The SQLAlchemy model representing the table schema.
        """
        self.session.query(model).delete()
        self.session.commit()

    def close_connection(self):
        """
        Closes the connection to the database.
        This method closes the session object, which releases any resources held by the session and closes the database connection.

        Parameters:
            self (DatabaseManagerSettings): The instance of the DatabaseManagerSettings class.
        """
        self.session.close()


# Príklad použitia
# db_manager_settings = DatabaseManagerSettings()

# Vypis stlpcov tabulky
# print(db_manager_settings.read_data(model=CarData).columns)

# Vytvorenie tabuliek
# db_manager_settings.create_table(CarData.__table__)
# db_manager_settings.create_table(ScrapingSettings.__table__)
# db_manager_settings.create_table(ProxySettings.__table__)
# db_manager_settings.create_table(LoggingSettings.__table__)


# Vloženie dát
# scraping_setting = ScrapingSettings(request_call_limit='1', request_period_seconds='1', requests_made='0')
# db_manager_settings.insert_data(scraping_setting)

# proxy_settings = ProxySettings(number_of_proxies='5')
# db_manager_settings.insert_data(proxy_settings)


# Čítanie dát
# scraping_settings: pd.DataFrame = db_manager_settings.read_data(CarData, conditions=[CarData.krajina == 'Czech Republic'])
# print(scraping_settings['request_period_seconds'][0])
# print(scraping_settings['request_call_limit'][0])

# proxy_settings: pd.DataFrame = db_manager_settings.read_data(ProxySettings)
# print(proxy_settings['number_of_proxies'][0])


# Aktualizácia dát
# x = 11
# c = 14
# db_manager_settings.update_data(ScrapingSettings, {'request_call_limit': x})
# db_manager_settings.update_data(ScrapingSettings, {'request_period_seconds': c})


# Vymazanie dát
# db_manager_settings.delete_all_data(ScrapingSettings)


# Zatvorenie spojenia
# db_manager_settings.close_connection()
