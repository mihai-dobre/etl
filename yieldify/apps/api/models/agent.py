from django.db import models


class Agent(models.Model):
    DEVICE_TYPE = (
        ('mobile', 'mobile'),
        ('laptop', 'laptop'),
        ('tablet', 'tablet'),
        ('desktop', 'desktop'),
        ('bot', 'bot'),
        ('unknown', 'unknown'),
    )
    agent_string = models.CharField(max_length=256, blank=True, null=True)
    op_sys = models.CharField(max_length=64, blank=True, null=True)
    op_sys_version = models.CharField(max_length=16, blank=True, null=True)
    device = models.CharField(max_length=64, blank=True, null=True)
    device_brand = models.CharField(max_length=64, blank=True, null=True)
    device_type = models.CharField(max_length=32, blank=True, null=True, choices=DEVICE_TYPE)
    browser = models.CharField(max_length=64, blank=True, null=True)
    browser_version = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return '{} {} | {} {} | {}'.format(self.op_sys,
                                           self.op_sys_version,
                                           self.browser,
                                           self.browser_version,
                                           self.device)

    def __unicode__(self):
        return '{} {} | {} {} | {}'.format(self.op_sys,
                                           self.op_sys_version,
                                           self.browser,
                                           self.browser_version,
                                           self.device)
