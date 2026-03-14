#!/usr/bin/env python3

import csv
import django
import hashlib
import os

from pathlib import Path
from django.utils.dateparse import parse_date

# --- 0. Setup Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opensite.settings')
django.setup()

from openrank.models import *

FAMILIES_CSV = 'families.csv'
ENGINES_CSV = 'engines.csv'

# --- 0. Create Rating List ---

if not RatingList.objects.filter(name='Bullet').first():

    rl = RatingList.objects.create(
        name         ='Bullet',
        thread_count = 1,
        hashsize     = 64,
        base_time    = 60,
        increment    = 1,
        book         = 'UHO_Lichess_4852_v1.epd',
    )

    print ('Created new Rating List: %s' % (str(rl)))

    stages = [(1, 10000, 100), (2, 50, 100), (3, 25, 100), (4, 10, 100)]

    for stage_num, top_n, games in stages:
        rls = RatingListStage.objects.create(
            rating_list   = rl,
            stage_number  = stage_num,
            top_n_engines = top_n,
            games         = games,
        )
        print ('Created new Rating List Stage: %s' % (str(rls)))

# --- 1. Import families ---
with open(FAMILIES_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        EngineFamily.objects.get_or_create(
            name=row['name'],
            defaults={
                'author'  : row['author'],
                'website' : row['website'],
            },
        )

# --- 2. Import engines ---
with open(ENGINES_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            family = EngineFamily.objects.get(name=row['family'])
        except EngineFamily.DoesNotExist:
            print('Skipping engine %s — family \'%s\' not found' % (row['version'], row['family']))
            continue

        Engine.objects.get_or_create(
            family=family,
            version=row['version'],
            defaults={
                'release_date': parse_date(row['release_date']),
                'nps': int(row['nps']),
                'latest': False,
            },
        )

# --- 3. Mark latest engine per family ---
Engine.objects.update(latest=False)

for family in EngineFamily.objects.all():
    latest_engine = (
        Engine.objects
        .filter(family=family, release_date__isnull=False)
        .order_by('-release_date')
        .first()
    )
    if latest_engine:
        latest_engine.latest = True
        latest_engine.save(update_fields=['latest'])
        print('Marked latest engine %s for family %s' % (latest_engine.version, family.name))

# --- 4. Add all Engines to all rating lists ---
for rating_list in RatingList.objects.all():
    rating_list.engines.add(*Engine.objects.all())

# --- 5. Set SHAs for Books/Engines ---

archive_path = Path(__file__).resolve().parent / 'books' / 'artifacts'

for rating_list in RatingList.objects.all():

    if not (path := archive_path / rating_list.book_artifact()).exists():
        raise Exception('Missing a .zst archive for %s' % (rating_list.book))

    sha256 = hashlib.sha256()
    with path.open('rb') as fin:
        for chunk in iter(lambda: fin.read(8192), b''):
            sha256.update(chunk)

    rating_list.book_sha = sha256.hexdigest()
    rating_list.save(update_fields=['book_sha'])

    print ('Set %s\'s book_sha to %s' % (rating_list.name, rating_list.book_sha))

archive_path = Path(__file__).resolve().parent / 'engines' / 'tarballs'

for engine in Engine.objects.all():

    if not (path := archive_path / engine.tarball_name()).exists():
        raise Exception('Missing a .zst archive for %s' % (engine.image_name()))

    sha256 = hashlib.sha256()
    with path.open('rb') as fin:
        for chunk in iter(lambda: fin.read(8192), b''):
            sha256.update(chunk)

    engine.tarball_sha = sha256.hexdigest()
    engine.save(update_fields=['tarball_sha'])

    print ('Set %s\'s tarball_sha to %s' % (engine.name(), engine.tarball_sha))

# --- 6. Create Admin User from ENV vars ---

username = os.environ.get('OPENRANK_USERNAME')
password = os.environ.get('OPENRANK_PASSWORD')

if username and password and not User.objects.filter(username=username).exists():
    user = User.objects.create_user(
        username=username,
        password=password,
        enabled=True,
        admin=True,
    )
    print('Created user: %s (enabled=True, admin=True)' % username)
