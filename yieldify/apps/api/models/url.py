from django.db import models


class Url(models.Model):
    domain = models.CharField(max_length=64, blank=True, null=True)
    path = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.agent_string)

    def __unicode__(self):
        return '{}'.format(self.path)
