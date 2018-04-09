import os
import pandas as pd
import IP2Location
from user_agents import parse
import itertools
from django.conf import settings
from ..models import IP, Agent, CustomUser, Request
from ..log import log_etl as log


def extractor(file_name):
    """
    Method that reads a file in chunks of chunk_size
    :param file_name: name of the file
    :param chunk_size: the size of the batches
    :return: a list of dataframes. A dataframe is a list of chunk_size rows containing the row index as first element.
    """
    log.info('Extractor is running for file: %s', file_name)
    chunk_list = []
    # merge date and time columns in a single date_time column(improves performance - speed and memory used)
    # url column is not needed for the task so it's not loaded from the file (improves performance)
    index = 0
    for chunk in pd.read_csv(file_name,
                             sep='\t',
                             names=['date', 'time', 'user_id', 'url', 'IP', 'user_agent_string'],
                             chunksize=settings.CHUNK_SIZE,
                             compression='gzip',
                             parse_dates=[[0, 1]], usecols=[0, 1, 2, 4, 5]):
        log.info('Extracted chunk: %s', chunk.axes[0])
        chunk_list.append(chunk)
        if index > 4:
            break
        index += 1

    return chunk_list


def parse_countries_cities_ips(ip, ip2loc):
    """
    Transform ips into countries and cities. Creates the database ip instance but
    without inserting it in the db.
    :param ip: the ip in string format
    :param ip2loc: the parser instance
    :return: list of IP model instances
    """
    # the idea is to parse as few ips as possible for maximum performance
    # there are rows with multiple IPs comma separated
    # build a dictionary with
    ips = ip.split(',')
    ips_instances = []
    for ip in ips:
        try:
            ip_all = ip2loc.get_all(ip.strip())
            ips_instances.append(IP(ip=ip, city=ip_all.city, country=ip_all.country_long))
        except Exception:
            log.exception('Unable to get city/country of ip: %s', ip)
    return ips_instances


def parse_user_agent(ua_string):
    """
    Method that parses the user agent string. It identifies the browser,
    browser version, os and os version, device manufacturer and device type:mobile,tablet,
    pc,console.
    Method is also creating the database object, without actually inserting it in the db.
    :param ua_string:
    :return: Agent instance
    """
    agent = Agent()
    try:
        result = parse(ua_string)
    except Exception:
        log.exception('Unable to parse user agent: %s', ua_string)
        return [agent]

    # if len(ua_string) >= 256:
    #     log.warning('ua_string > 256. Will be truncated: %s', ua_string)
    agent.agent_string = ua_string[:256]
    agent.op_sys = result.os.family
    agent.op_sys_version = result.os.version_string
    agent.browser = result.browser.family
    agent.browser_version = result.browser.version_string
    agent.device = result.device.family
    agent.device_brand = result.device.brand
    if result.is_pc:
        agent.device_type = 'desktop'
    elif result.is_mobile:
        agent.device_type = 'mobile'
    elif result.is_tablet:
        agent.device_type = 'tablet'
    elif result.is_bot:
        agent.device_type = 'crawler'
    else:
        agent.device_type = 'unknown'
    return [agent]


def parse_user(user_id, users):
    """
    It's not parsing anything, just creates a CustomUser instance
    :param user_id: user_id string
    :return: CustomUser instance
    """
    # check if the user is already in the database. It must be unique
    try:
        u = users[user_id]
    except Exception:
        u = CustomUser(user_id=user_id)
        users[user_id] = u
    return u


def get_city_country(ip, ip2loc):
    """
    Get from one run the city and the country in a touple
    :param ip:
    :param ip2loc:
    :return:
    """
    try:
        ip_all = ip2loc.get_all(ip)
        ip_instance = IP(ip=ip, city=ip_all.city, country=ip_all.country_long)
    except Exception as err:
        ip_instance = IP(ip=ip)
    return ip_instance


def transform_and_load(chunk, input_file_instance, users):
    """
    Transforms the data and loads it into a database for further use/processing
    :return:
    """
    # initialize IP parsers

    ip2loc = IP2Location.IP2Location()
    ip2loc.open('IP2LOCATION-LITE-DB3.BIN/IP2LOCATION-LITE-DB3.BIN')

    chunk['ip_instances'] = chunk.IP.apply(lambda row: [get_city_country(ip.strip(), ip2loc) for ip in row.split(',')])

    chunk['agent_instances'] = chunk.user_agent_string.apply(parse_user_agent)
    # log.info('agent_column: %s', type(chunk.agent_instances[10]))
    # those are not unique users. Unique users are in the users dict
    chunk['custom_users'] = chunk.user_id.apply(lambda row: parse_user(row, users))

    # log.info('type chunk[custom_users]: %s', type(chunk.custom_users[20]))
    # log.info('users dict: %s', len(users.keys()))

    # saving to database
    IP.objects.bulk_create(list(itertools.chain.from_iterable(chunk.ip_instances)))
    log.info('Created ips: %s', len(chunk.ip_instances))

    Agent.objects.bulk_create(list(itertools.chain.from_iterable(chunk.agent_instances)))
    log.info('Created agents: %s', len(chunk.agent_instances))

