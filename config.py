import json
from dotenv import load_dotenv
import os


# A function for loading a JSON file with application settings
def load_settings():
    """Load settings from a JSON file.

    This function loads settings from a JSON file specified in the environment
    variable SETTINGS_APK, which should be a path to a file on the local file
    system. If the environment variable is not set or if the file does not
    exist, the function raises a FileNotFoundError. If the file cannot be
    decoded as a UTF-8 file, the function raises a UnicodeDecodeError.

    Returns:
        A dictionary with the settings.

    Raises:
        FileNotFoundError: If the settings file does not exist.
        UnicodeDecodeError: If the settings file cannot be decoded as a UTF-8
            file.
    """
    load_dotenv()
    try:
        SETTINGS_APK = os.environ['SETTINGS_APK']
    except KeyError:
        raise FileNotFoundError('Environment variable SETTINGS_APK not set')
    try:
        with open(SETTINGS_APK, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f'Settings file {SETTINGS_APK} not found')
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f'Settings file {SETTINGS_APK} is not UTF-8')
    return config_data



