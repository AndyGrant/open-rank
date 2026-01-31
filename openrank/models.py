from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F

class User(AbstractUser):

    enabled = models.BooleanField(default=False)
    admin   = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Worker(models.Model):

    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workers')
    pairing = models.ForeignKey('Pairing', on_delete=models.SET_NULL, null=True, blank=True, related_name='workers')

    updated = models.DateTimeField(auto_now=True)
    secret  = models.CharField(max_length=64, default='', blank=True)
    hwinfo  = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s by %s' % (hwinfo.get('cpu_name', 'UNKNOWN'), user.username)

class EngineFamily(models.Model):

    name        = models.CharField(max_length=255, unique=True)
    author      = models.CharField(max_length=255)
    website     = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Engine(models.Model):

    family       = models.ForeignKey(EngineFamily, on_delete=models.CASCADE, related_name='engines')
    version      = models.CharField(max_length=50)
    release_date = models.DateField(null=True, blank=True)
    tarball_sha  = models.CharField(max_length=255)

    disabled = models.BooleanField(default=False)
    latest   = models.BooleanField(default=False)
    private  = models.BooleanField(default=False)

    nps = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['family'],
                condition=Q(latest=True),
                name='unique_latest_engine_per_family'
            )
        ]

    def name(self):
        return '%s-%s' % (self.family.name.lower(), self.version.lower())

    def image_name(self):
        return 'openrank-%s' % (self.name())

    def tarball_name(self):
        return self.image_name() + '.tar.zst'

    def __str__(self):
        return '%s %s' % (self.family.name, self.version)

class RatingList(models.Model):

    name         = models.CharField(max_length=255)
    thread_count = models.IntegerField()
    hashsize     = models.IntegerField()
    base_time    = models.FloatField()
    increment    = models.FloatField()
    book         = models.CharField(max_length=255)
    book_sha     = models.CharField(max_length=255)

    engines = models.ManyToManyField('Engine', related_name='rating_lists', blank=True)

    def book_artifact(self):
        return self.book + '.zst'

    def __str__(self):
        return '%d-thread %d + %d' % (self.thread_count, self.base_time, self.increment)

class RatingListStage(models.Model):

    rating_list   = models.ForeignKey(RatingList, on_delete=models.CASCADE, related_name='stages')
    stage_number  = models.PositiveIntegerField()
    top_n_engines = models.PositiveIntegerField()
    games         = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['rating_list', 'stage_number'],
                name='unique_stage_per_rating_list'
            )
        ]
        ordering = ['stage_number']

    def __str__(self):
        return '%s - Stage %d' % (str(self.rating_list), self.stage_number)

class Pairing(models.Model):

    stage    = models.ForeignKey('RatingListStage', on_delete=models.CASCADE, related_name='pairings')
    engine_a = models.ForeignKey('Engine', on_delete=models.CASCADE, related_name='pairings_as_a')
    engine_b = models.ForeignKey('Engine', on_delete=models.CASCADE, related_name='pairings_as_b')

    LL = models.IntegerField(default=0)
    LD = models.IntegerField(default=0)
    DD = models.IntegerField(default=0)
    DW = models.IntegerField(default=0)
    WW = models.IntegerField(default=0)

    # Incremented for every individual game assigned to a worker
    book_index = models.IntegerField(default=0)

    # Should be updated if underlying RatingListStage ever changes
    finished = models.BooleanField(default=False)

    def games(self):
        return sum(self.penta())

    def penta(self):
        return (self.LL, self.LD, self.DD, self.DW, self.WW)

    def workload_size(self, worker):
        # Always over-assign work, to avoid quiet-vs-noisy neighbor dynamic
        return max(0, self.stage.games - self.games()) + 2 * worker.hwinfo['logical_cores']

    def compute_finished(self):
        self.finished = self.games() >= self.stage.games
        return self.finished

    def save(self, *args, **kwargs):
        self.compute_finished()
        super().save(*args, **kwargs)

    def __str__(self):
        return '%s vs %s, Stage %s' % (str(self.engine_a), str(self.engine_b), str(self.stage))
