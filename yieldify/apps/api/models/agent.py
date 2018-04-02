from django.db import models


class Agent(models.Model):
    agent_string = models.CharField(max_length=128, blank=True, null=True)
    op_sys = models.CharField(max_length=64, blank=True, null=True)
    device = models.CharField(max_length=64, blank=True, null=True)
    browser = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.agent_string)

    def __unicode__(self):
        return '{}'.format(self.path)
