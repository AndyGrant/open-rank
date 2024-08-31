from django.db.models import *

import os
import time

def engine_file_name(instance, filename):
    bin_name = '%s.%d' % (instance.name, int(time.time()))
    return os.path.join('binaries', instance.family.name, bin_name)


class EngineHardwareType(TextChoices):
    CPU = 'CPU', 'CPU'

class EngineClassification(TextChoices):
    OPENSOURCE = 'OPENSOURCE' , 'Open Source'
    FREE       = 'FREE'       , 'Free'
    PRIVATE    = 'PRIVATE'    , 'Private'
    COMMERCIAL = 'COMMERCIAL' , 'Commercial'


class EngineFamily(Model):

    name    = CharField(max_length=128)
    author  = CharField(max_length=128)
    website = URLField(max_length=256)

    def __str__(self):
        return '%s by %s' % (self.name, self.author)

class Engine(Model):

    name           = CharField(max_length=128)
    family         = ForeignKey(EngineFamily, on_delete=CASCADE)
    release_date   = DateField()
    hardware       = CharField(max_length=32, choices=EngineHardwareType.choices)
    classification = CharField(max_length=32, choices=EngineClassification.choices)
    binary         = FileField(upload_to=engine_file_name, blank=True, null=True)

    def __str(self):
        return '%s' % (self.name)