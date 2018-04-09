from django.core.management.base import BaseCommand
from yieldify.apps.api.models import InputFile, IP, Request, CustomUser, Agent


class Command(BaseCommand):
    help = 'Read files from the input directory, load data to the database, print aggregated results'

    def handle(self, *args, **options):
        """
        Clean db.
        :param args:
        :param options: is a dictionary containing the command line arguments.
        :return:
        """
        InputFile.objects.all().delete()
        Agent.objects.all().delete()
        CustomUser.objects.all().delete()
        IP.objects.all().delete()
        Request.objects.all().delete()
