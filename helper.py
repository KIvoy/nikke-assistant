import configparser


def read_config(file_name='NIKKE_ASSISTANT.INI'):
    """
    helper function to read language settings
    TODO: move to helper function files
    """
    config = configparser.ConfigParser()
    config.read(file_name)
    return config