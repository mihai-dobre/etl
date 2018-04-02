from django.db import models
from .agent import Agent
from .custom_user import CustomUser
from .ip import IP
from .url import Url


class Request(models.Model):
    timestamp = models.DateTimeField()
    user = models.ForeignKey(CustomUser)
    ip = models.ForeignKey(IP)
    url = models.ForeignKey(Url)
    agent = models.ForeignKey(Agent)

    def __str__(self):
        return '{} | {} | {} | {}'.format(self.timestamp, self.user.username, self.ip.ip, self.agent.agent_string)

    def __unicode__(self):
        return '{} | {} | {} | {}'.format(self.timestamp, self.user.username, self.ip.ip, self.agent.agent_string)