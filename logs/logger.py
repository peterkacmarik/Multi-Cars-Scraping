import logging
from rich import print


def get_logger(log_file, log_level):
    # Vytvorenie loggera
    logger = logging.getLogger(log_file)
    logger.setLevel(log_level)

    # Nastavenie formátu logovania
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Nastavenie logovania do súboru
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Nastavenie logovania na konzolu
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger