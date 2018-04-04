import os
import pandas as pd
import IP2Location
from user_agents import parse

from django.conf import settings
from django.db import transaction
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
    for chunk in pd.read_csv(file_name,
                             sep='\t',
                             names=['date', 'time', 'user_id', 'url', 'IP', 'user_agent_string'],
                             chunksize=settings.CHUNK_SIZE,
                             compression='gzip',
                             parse_dates=[[0, 1]], usecols=[0, 1, 2, 4, 5]):
        log.info('Extracted chunk: %s', chunk.axes[0])
        chunk_list.append(chunk)
        break

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
        ip = ip.strip()
        try:
            country = ip2loc.get_country_long(ip)
            city = ip2loc.get_city(ip)
            log.info('Parsed IP: %s | %s | %s', ip, city, country)
            ips_instances.append(IP(ip=ip, city=city, country=country))
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
    try:
        result = parse(ua_string)
    except Exception:
        log.exception('Unable to parse user agent: %s', ua_string)
        return None
    agent = Agent()
    if len(ua_string) >= 256:
        log.warning('ua_string > 256. Will be truncated: %s', ua_string)
    agent.agent_string = ua_string[:256]
    agent.op_sys = result.os.family
    agent.op_sys_version = result.os.version_string
    agent.browser = result.browser.family
    agent.browser_version = result.browser.version_string
    agent.device = result.device.family
    agent.device_brand = result.device.brand
    if result.is_pc:
        agent.device_type = 'desktop'
    elif result.is_bot:
        agent.device_type = 'crawler'
    elif result.is_mobile:
        agent.device_type = 'mobile'
    elif result.is_tablet:
        agent.device_type = 'tablet'
    else:
        agent.device_type = 'unknown'
    return agent


@transaction.atomic
def parse_user(user):
    """
    It's not parsing anything, just creates a CustomUser instance
    :param user: user_id string
    :return: CustomUser instance
    """
    # check if the user is already in the database. It must be unique
    try:
        u = CustomUser.objects.get(user_id=user)
    except Exception:
        u = CustomUser(user_id=user)
        u.save()
    return u


def transform_and_load(chunk, input_file_instance):
    """
    Transforms the data and loads it into a database for further use/processing
    :return:
    """
    # initialize IP parsers
    ip_info = ['IP',
               'COUNTRY',
               'REGION',
               'CITY',
               ]
    ip2loc = IP2Location.IP2Location()
    ip2loc.open('IP2LOCATION-LITE-DB3.BIN/IP2LOCATION-LITE-DB3.BIN')

    range_index = chunk.axes[0]
    ip_instances = []
    user_agent_instances = []
    user_instances = []
    request_instances = []
    for i in range_index.values:
        ips = parse_countries_cities_ips(chunk.IP[i], ip2loc)
        user_agent = parse_user_agent(chunk.user_agent_string[i])
        user = parse_user(chunk.user_id[i])
        # if one of the components failed to parse, skip the row
        if not ips or not user_agent or not user:
            log.warning('Skipping row %s', i)
            continue

        ip_instances.extend(ips)
        user_agent_instances.append(user_agent)
        user_instances.append(user)
        date_time = chunk.date_time[i].to_pydatetime()
        for ip in ips:
            request_instances.append({
                'timestamp': date_time,
                'ip': ip,
                'agent': user_agent,
                'user': user,
                'file': input_file_instance
            })
    # use bulk_create to avoid calling the save() method for each instance.
    # with bulk_create you can insert all the instance in one query
    # save the requests last because we need the references at the database level
    IP.objects.bulk_create(ip_instances)
    log.info('Created ips: %s', len(ip_instances))
    Agent.objects.bulk_create(user_agent_instances)
    log.info('Created agents: %s', len(user_agent_instances))
    log.info('Created user_ids: %s', len(user_instances))
    Request.objects.bulk_create([Request(**request) for request in request_instances])
    log.info('Created requests: %s', len(request_instances))
    log.info('Database loaded with bach: %s', range_index)
