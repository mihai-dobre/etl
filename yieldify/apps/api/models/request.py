from django.db import models
from .agent import Agent
from .custom_user import CustomUser
from .ip import IP
from .url import Url
from .input_file import InputFile


class Request(models.Model):
    timestamp = models.DateTimeField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ip = models.ForeignKey(IP, on_delete=models.CASCADE)
    # url = models.ForeignKey(Url)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    file = models.ForeignKey(InputFile, on_delete=models.CASCADE)

    def __str__(self):
        return '{} | {}'.format(self.timestamp, self.file.name)

    def __unicode__(self):
        return '{} | {}'.format(self.timestamp, self.file.name)
