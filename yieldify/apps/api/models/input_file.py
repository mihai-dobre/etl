from django.db import models


class InputFile(models.Model):
    name = models.CharField(max_length=32, blank=True, null=True)
    md5 = models.CharField(max_length=64, blank=True, null=True)
    path = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return '{}/{}'.format(self.path, self.name)

    def __unicode__(self):
        return '{}/{}'.format(self.path, self.name)