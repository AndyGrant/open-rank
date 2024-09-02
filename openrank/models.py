from django.db.models import *

import os

def engine_docker_name(instance, filename):
    name = '%s.Dockerfile' % (instance.name)
    return os.path.join('engines', instance.family.name, name)

def engine_binary_name(instance, filename):
    name = '%s.elf' % (instance.name)
    return os.path.join('engines', instance.family.name, name)

def engine_extra_name(instance, filename):
    name = '%s.extra' % (instance.name)
    return os.path.join('engines', instance.family.name, name)

def check_unique_fields(model, instance, *field_names):

    checks = { f : getattr(instance, f) for f in field_names }
    others = model.objects.filter(**checks)
    others = others if instance._state.adding else others.exclude(pk=instance.pk)

    if others.exists():
        raise ValueError


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
    latest  = ForeignKey('Engine', on_delete=SET_NULL, null=True, blank=True)

    def __str__(self):
        return '%s by %s' % (self.name, self.author)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            check_unique_fields(EngineFamily, self, 'name')
            super().save(*args, **kwargs)

class Engine(Model):

    name           = CharField(max_length=128)
    family         = ForeignKey(EngineFamily, on_delete=CASCADE)
    release_date   = DateField()
    hardware       = CharField(max_length=32, choices=EngineHardwareType.choices)
    classification = CharField(max_length=32, choices=EngineClassification.choices)

    docker_file    = FileField(upload_to=engine_docker_name, blank=True, null=True)
    binary_file    = FileField(upload_to=engine_binary_name, blank=True, null=True)
    extra_file     = FileField(upload_to=engine_extra_name,  blank=True, null=True)

    def __str__(self):
        return '%s' % (self.name)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            check_unique_fields(Engine, self, 'name')
            super().save(*args, **kwargs)