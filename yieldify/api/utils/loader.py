import os
import argparse
import gzip
import logging
from logging import handlers
import pandas as pd
import IP2Location

filename = '/Users/mihaidobre/Downloads/input_data.gz'

LOG = None


def setup_logger():
    global LOG
    etl_logger = logging.getLogger('etl')
    formatter = logging.Formatter(fmt='%(levelname)-8s %(asctime)s %(filename)s |%(lineno)4d| %(message)s',
                                  datefmt='%a, %Y-%m-%d %H:%M:%S')
    file_path = os.path.dirname(os.path.abspath(__file__))
    file_name = os.sep.join([file_path, 'etl.log'])
    print('file_path: ', file_path)
    handler = handlers.RotatingFileHandler(file_name, maxBytes=1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    etl_logger.addHandler(handler)
    etl_logger.setLevel(logging.DEBUG)
    LOG = etl_logger


def extracter(file_name, chunk_size):
    """
    Method that reads a file in chunks of chunk_size
    :param filename: name of the file
    :param chunk_size: the size of the batches
    :return: a list of dataframes. A dataframe is a list of chunk_size rows containing the row index as first element.
    """
    LOG.info('Extracter is running for file: %s', file_name)
    chunk_list = []
    # merge date and time columns in a single date_time column(improves performance - speed and memory used)
    # url column is not needed for the task so it's not loaded from the file (improves performance)
    for chunk in pd.read_csv(file_name,
                             sep='\t',
                             names=['date', 'time', 'user_id', 'url', 'IP', 'user_agent_string'],
                             chunksize=chunk_size,
                             compression='gzip',
                             parse_dates=[[0, 1]], usecols=[0, 1, 2, 4, 5]):
            LOG.info('Extracted chunk: %s', chunk.size)
            chunk_list.append(chunk)
    return chunk_list


def parse_countries_cities_ips(chunk, ip2loc_inst):
    """
    Transform ips into countries.
    :param chunk:
    :return:
    """
    # the idea is to parse as few ips as possible for maximum performance
    # there are rows with multiple IPs comma separated
    # build a dictionary with
    country = ip2loc_inst.get_country_long("19.5.10.1")
    city = ip2loc_inst.get_city()
    print rec.country_long

    print rec.city


def transformer(chunk_list):
    """
    Method that receives a chunk and processes it.
    Parses the ips -> cities and countries(number of events).
    Parses the user agent -> Browser and OS(unique users).
    :param chunk: a set of data records
    :return: a list of transformed records / result to print to stdout
    """
    parsed_data = []
    ip2loc_inst = IP2Location.IP2Location()
    bin_config = 'data/IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-USAGETYPE-SAMPLE.BIN'
    ip2loc_inst.open(bin_config)
    for chunk in chunk_list:
        (countries, cities) = parse_countries_cities_ips(chunk, ip2loc_inst)
        browser = parse_browsers_user_agent(chunk)
        os = parse_os_user_agent(chunk)


def loader():
    """
    Loads the data resulted from parsing into a database for further use/processing
    :return:
    """
    pass


def etl(file_name, chunk_size, destination=None):
    """
    Main method that does all the calculations in case output to stdout or fills the database in case of api.
    :param filename: name of the file to be parsed
    :param chunk_size: how many rows to read from file at once
    :param destination: None for stdout, database pointer if API
    :return:
    """
    setup_logger()
    result = {'countries': [], 'cities': [], 'browsers': [], 'os': []}
    LOG.info('Processing file: %s', file_name)
    chunk_list = extracter(file_name, chunk_size)
    result = transformer(chunk_list, destination)
    if destination:
        loader(destination)
    else:
        print(result)

if __name__ == '__main__':
    etl(filename, 1024)
