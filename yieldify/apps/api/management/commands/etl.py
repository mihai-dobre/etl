import os
import json
from hashlib import md5
import numpy as np
import pandas as pd
import threading
import IP2Location
import dask
import itertools
import dask.dataframe as dds
import pytz
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Count
from django.conf import settings
from yieldify.apps.api.log import log_etl as log
from yieldify.apps.api.utils import extractor, transform_and_load
from yieldify.apps.api.models import InputFile, IP, Request, CustomUser, Agent


class Command(BaseCommand):
    help = 'Read files from the input directory, load data to the database, print aggregated results'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            '-dir',
            action='store',
            type=str,
            required=True,
            dest='dir',
            help='directory with tsv files'
        )

        parser.add_argument(
            '-dest',
            action='store',
            type=str,
            dest='dest',
            help='destination of the aggregated data: stdout or database'
        )

    def should_be_parsed(self, file):
        """
        Methid that checks if a file needs to be parsed or not
        :param file:
        :return:
        """
        computed_md5 = md5(str('{file_path} | {file_size} | {file_last_modified_time}'.format(
            file_path=file,
            file_size=os.stat(file).st_size,
            file_last_modified_time=os.stat(file).st_mtime)).encode('utf-8')).hexdigest()
        log.info('Computed md5 for file: %s is: %s', file, computed_md5)
        try:
            db_file = InputFile.objects.get(path=file)
            input_file_instance = None
            if db_file.md5 != computed_md5:
                log.info('File has been modified. Updating md5: %s', file)
                db_file.md5 = computed_md5
                db_file.save()
                input_file_instance = db_file
        except ObjectDoesNotExist:
            # file not found in the database. Should be added and parsed
            log.info('Inserting new file into database: %s', file)
            db_file = InputFile()
            db_file.name = file.split(os.sep)[-1]
            db_file.md5 = computed_md5
            db_file.path = file
            db_file.save()
            input_file_instance = db_file
        except MultipleObjectsReturned:
            log.exception('get returned multiple results. Please check the database for consistency.')
            log.warning('Skipping parsing file %s', file)
            input_file_instance = None
        except Exception:
            log.exception('Unknown error occured.')
            log.warning('Skipping parsing file: %s', file)
            input_file_instance = None

        return input_file_instance

    def compute_result(self, file):
        """
        Compute the statistics
        :return: dictionary containing the statistics
        """
        result = {}

        # get Top 5 Countries based on number of events
        countries = IP.objects.values('country').annotate(count=Count('country')).order_by('-count')[:5]
        result['countries'] = ['{}    {}'.format(x['country'], x['count']) for x in countries]
        # get Top 5 Cities based on number of events
        cities = IP.objects.values('city').annotate(count=Count('city')).order_by('-count')[:5]
        result['cities'] = ['{}    {}'.format(x['city'], x['count']) for x in cities]
        # Top 5 Browsers based on number of unique users
        requests_of_unique_users = Request.objects.distinct('user').values_list('agent')
        browsers = Agent.objects.filter(id__in=requests_of_unique_users).values('browser').annotate(
            count=Count('browser')).order_by('-count')[:5]
        # resulted query:
        # SELECT api_agent.browser, COUNT(api_agent.browser) AS count
        # FROM api_agent
        # WHERE api_agent.id IN(
        #     SELECT DISTINCT ON(request.user_id) request.agent_id AS Col1
        #     FROM api_request request)
        # GROUP BY api_agent.browser
        # ORDER BY count DESC;
        result['browsers'] = ['{}    {}'.format(x['browser'], x['count']) for x in browsers]
        # Top 5 Operating systems based on number of unique users
        oss = Agent.objects.filter(id__in=requests_of_unique_users).values('op_sys').annotate(
            count=Count('op_sys')).order_by('-count')[:5]
        # resulted query:
        # SELECT api_agent.os, COUNT(api_agent.os) AS count
        # FROM api_agent
        # WHERE api_agent.id IN(
        #     SELECT DISTINCT ON(request.user_id) request.agent_id AS Col1
        #     FROM api_request request)
        # GROUP BY api_agent.os
        # ORDER BY count DESC;
        result['os'] = ['{}    {}'.format(x['op_sys'], x['count']) for x in oss]
        return result

    def parse_requests(self, index, row, input_file):
        """
        Return a series of Request instances, ready to save in the database.
        :param index: the ip_instances series is a list of maximum 2 elements
        :param row: row from the chunk dataframe(the big one)
        :param input_file: a pointer to the file instance in the database. It is a foreign key
        :return: Request instance
        """
        # log.info('ROW: %s', row)
        return Request(timestamp=row.date_time.to_pydatetime().astimezone(tz=pytz.utc),
                       user=row.custom_users,
                       agent=row.agent_instances,
                       ip=row.ip_instances[index],
                       file=input_file) if len(row.ip_instances) > index else np.nan

    def parse_user(self, chunk):
        """
        Method used to calculate the custom_user instances and fill the database with unique ones.
        :param chunk: user_id string
        :return: CustomUser instance
        """
        # create a 2 columns dataframe: user_id and custom_user
        unique = pd.DataFrame(data=chunk.user_id, columns=['user_id'])
        unique['custom_user'] = unique.user_id.apply(lambda row: CustomUser(user_id=row))
        return unique

    def process_chunk(self, chunk, users, input_file_instance):
        """
        Method that encapsulates all the processing needed for a chunk
        :param chunk: chunk of file to be processed
        :param users: dataframe with 2 columns containing all the unique users: user_id, custom_user
        :param input_file_instance: database file pointer(used for foreignkey)
        :return:
        """
        # create a ip2loc instance for each thread. Found out that this module is not thread safe
        ddf = dds.from_pandas(chunk, npartitions=16)
        transform_and_load(ddf, users)
        res = ddf.persist()

        IP.objects.bulk_create(list(itertools.chain.from_iterable(res.ip_instances.values.compute())))
        Agent.objects.bulk_create(list(res.agent_instances.values.compute()))

        res['request0'] = res.apply(lambda row: self.parse_requests(0, row, input_file_instance), axis=1, meta=object)

        res['request1'] = res.apply(lambda row: self.parse_requests(1, row, input_file_instance), axis=1, meta=object)

        res = res.persist()

        request1 = res.request1.dropna().compute()
        requests = list(res.request0.values.compute()) + \
                   list(request1.values) \
            if request1.size > 0 else []
        threading.Thread(target=Request.objects.bulk_create, args=(requests,)).start()

        log.info('Database loaded with bach: %s', chunk.index)
        # return 'Database loaded with bach: {}'.format(chunk.index)

    def handle(self, *args, **options):
        """
        Method that iterates over the files in a directory. Parses all the tsv files, enhances the data and pushes it
        to the database. It will compute an md5sum over the filename + timestamp last_modified + size and will not
        consider the file for parsing is the existing md5sum is the same with the computed one. So if you run the
        management command multiple times on the same files, the parsing will happen only on the first run. For all
        others, the data will be returned directly from the database.
        :param args:
        :param options: is a dictionary containing the command line arguments.
        :return:
        """
        dask.set_options(get=dask.threaded.get)
        dir_path = options['dir']
        if not os.path.exists(dir_path):
            raise NotADirectoryError('Path specified for -dir argument is not valid: {}'.format(dir_path))
        files = []
        # get the list of file names to parse
        for (_, _, file_names) in os.walk(dir_path):
            # filter .gz files
            file_names = filter(lambda name: name.split('.')[-1] == 'gz', file_names)
            files.extend([os.path.join(dir_path, file_name) for file_name in file_names])
            # os.walk runs recursively over the whole directory tree. I want to stop at the first level.
            break
        log.info('Files found: %s', files)
        # check if we got any files to parse
        if not files:
            raise FileNotFoundError('No files found on the specified path: {}'.format(dir_path))

        for file in files:
            log.info('Processing file: %s', file)
            # check if the file needs to be parsed.
            input_file_instance = self.should_be_parsed(file)
            if not input_file_instance:
                continue

            start = time.time()
            chunks = extractor(file)
            # log.info('users_dict: %s', id(users))
            result = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self.parse_user, chunk) for chunk in chunks]
                for future in as_completed(futures):
                    result.append(future.result())

            users = result[0].append(result[1:], ignore_index=True)
            users.drop_duplicates(subset='user_id', inplace=True)
            log.info('Users: %s', users.user_id.size)
            users = users.set_index('user_id')

            CustomUser.objects.bulk_create(list(users.custom_user.values), batch_size=settings.CHUNK_SIZE)
            # the rest of the processing should be spread over multiple processes
            log.info('CPUs: %s', os.cpu_count())

            for chunk in chunks:
                self.process_chunk(chunk, users, input_file_instance)

            print('Total running time: ', time.time()-start)
        threads = threading.enumerate()
        for t in threads:
            try:
                t.join()
            except RuntimeError as err:
                if 'cannot join current thread' in err:
                    continue
                else:
                    raise
        print(json.dumps(self.compute_result(file), indent=2))
