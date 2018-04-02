from django.db import models


class IP(models.Model):
    ip = models.CharField(max_length=32, blank=True, null=True)
    city = models.CharField(max_length=64, blank=True, null=True)
    country = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return '{} : {} from {}'.format(self.ip, self.city, self.country)

    def __unicode__(self):
        return '{} : {} from {}'.format(self.ip, self.city, self.country)