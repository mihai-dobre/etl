import sys
import argparse
import csv
import json
from django.core.management.base import BaseCommand


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
            required=True,
            dest='dest',
            help='destination of the aggregated data: stdout or database'
        )

    def handle(self, *args, **options):
        """
        Method that iterates over the files in a directory. Parses all the tsv files, enhances the data and pushes it
        to the database.
        :param args:
        :param options: is a dictionary with command line arguments.
        :return:
        """
        header = ['date', 'state', 'start_time', 'end_time', 'group_id']
        # options['tslots']:
        log.info(options)
        f = options['timeslots']
        log.info(type(f))
        csv_data = csv.reader(f, delimiter=';')
        for row in csv_data:
            # transform the data into a dict according with the header
            csv_timeslot_dict = dict(zip(header, row))
            csv_timeslot_dict['start_time'] = arrow.get('{}T{}'.format(csv_timeslot_dict['date'],
                                                                       csv_timeslot_dict['start_time']), tz='London/Europe')
            csv_timeslot_dict['end_time'] = arrow.get('{}T{}'.format(csv_timeslot_dict['date'],
                                                                       csv_timeslot_dict['end_time']), tz='London/Europe')
            csv_timeslot_dict['date'] = arrow.get(csv_timeslot_dict['date'])
            # log.info('csv_row: %s', csv_timeslot_dict)

            if arrow.utcnow().date() != csv_timeslot_dict['date'].date():
                continue
            try:
                group = DeviceGroup.objects.get(id=csv_timeslot_dict['group_id'])
            except KeyError as err:
                log.exception('Key `group_id` not found in dict. %s', err)
                sys.exit(1)
            except Exception as err:
                log.exception('Group with ID: % not found. %s', csv_timeslot_dict['group_id'], err)
                sys.exit(1)
            schedule_type = 'weekday' if csv_timeslot_dict['date'].isoweekday() <= 5 else 'weekend'
            schedule = group.schedules.get(schedule_type=schedule_type)
            time_slots = schedule.time_slots.all()
            # get the force charging timeslot
            c_time_slot = time_slots.get(state='C')
            # get the force discharging timeslot
            i_time_slot = time_slots.get(state='I')
            # get the only charging timeslot
            h_time_slot = time_slots.get(state='H')

            # 'end_time': '2017-01-02T16:00:00.000Z',
            # 'start_time': '2017-01-02T15:00:00.000Z',
            i_time_slot.start_time = csv_timeslot_dict['start_time'].time()
            i_time_slot.end_time = csv_timeslot_dict['end_time'].time()
            i_time_slot.save()
            log.info('Updated discharging slot: %s - %s', i_time_slot.start_time, i_time_slot.end_time)
            h_time_slot.end_time = csv_timeslot_dict['start_time'].time()
            h_time_slot.save()
            log.info('Updated only charging slot: %s - %s', h_time_slot.start_time, h_time_slot.end_time)
