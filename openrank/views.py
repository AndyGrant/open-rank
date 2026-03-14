import json
import pathlib
import secrets
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import *
from .forms import *

# HELPERS

def next_stage_number(rating_list):
    last = rating_list.stages.order_by('-stage_number').first()
    return 1 if last is None else last.stage_number + 1


def index(request):
    return render(request, 'index.html')

def signup(request):

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', { 'form': form })


def family_list(request):
    families = EngineFamily.objects.all().prefetch_related('engines')
    return render(request, 'families.html', { 'families': families })

def family_create(request):

    if request.method == 'POST':
        form = EngineFamilyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('family_list')
    else:
        form = EngineFamilyForm()

    return render(request, 'family_form.html', { 'form' : form })

def family_engines(request, family_id):
    family  = get_object_or_404(EngineFamily, id=family_id)
    engines = family.engines.order_by('-release_date')
    return render(request, 'family_engines.html', { 'family' : family, 'engines' : engines })


def engine_create(request, family_id=None):

    initial = {}
    engine = Engine()

    if family_id is not None:
        family = get_object_or_404(EngineFamily, id=family_id)
        initial['family'] = family

    if request.method == 'POST':
        form = EngineForm(request.POST)
        if form.is_valid():
            engine = form.save()
            return redirect('family_engines', family_id=engine.family.id)
    else:
        form = EngineForm(initial=initial)

    return render(request, 'engine_form.html', { 'form' : form, 'engine' : engine })

def engine_edit(request, engine_id):

    engine = get_object_or_404(Engine, id=engine_id)

    if request.method == 'POST':
        form = EngineForm(request.POST, instance=engine)
        if form.is_valid():
            form.save()
            return redirect('family_engines', family_id=engine.family.id)
    else:
        form = EngineForm(instance=engine)

    context = { 'form' : form, 'engine' : engine, 'rating_lists' : RatingList.objects.all() }
    return render(request, 'engine_form.html', context)

def engine_add_to_list(request, engine_id, list_id):

    engine      = get_object_or_404(Engine, id=engine_id)
    rating_list = get_object_or_404(RatingList, id=list_id)

    rating_list.engines.add(engine)

    return redirect('engine_edit', engine_id=engine.id)


def rating_list_list(request):
    rating_lists = RatingList.objects.all().prefetch_related('stages')
    return render(request, 'rating_lists.html', { 'rating_lists' : rating_lists })

def rating_list_create(request):

    if request.method == 'POST':
        form = RatingListForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rating_list_list')
    else:
        form = RatingListForm()

    return render(request, 'rating_list_form.html', { 'form': form })

def rating_list_stage_create(request, rating_list_id):

    rating_list = get_object_or_404(RatingList, id=rating_list_id)

    if request.method == 'POST':
        form = RatingListStageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.rating_list = rating_list
            stage.stage_number = next_stage_number(rating_list)
            stage.save()
            return redirect('rating_list_list')
    else:
        form = RatingListStageForm()

    return render(request, 'rating_list_stage_form.html', { 'form' : form, 'rating_list' : rating_list })


def pairings_for_stage(request, stage_id):
    stage    = get_object_or_404(RatingListStage, id=stage_id)
    pairings = stage.pairings.all()
    return render(request, 'stage_pairings.html', { 'stage' : stage, 'pairings' : pairings })

def pairings_generate(request, stage_id):

    stage   = get_object_or_404(RatingListStage, id=stage_id)
    engines = stage.rating_list.engines.all()
    to_add  = []

    # TODO: Respect the Stages, i.e. determine the relative ranking of engines,
    #       to determine which engines to generate pairings for.

    # Create pairings only for engines marked as the latest
    for i, engine_a in enumerate(engines):
        for engine_b in engines[i+1:]:
            if (engine_a.latest and engine_b.latest
                and not Pairing.objects.filter(stage=stage, engine_a=engine_a, engine_b=engine_b).exists()
                and not Pairing.objects.filter(stage=stage, engine_a=engine_b, engine_b=engine_a).exists()):
                to_add.append(Pairing(stage=stage, engine_a=engine_a, engine_b=engine_b))
    Pairing.objects.bulk_create(to_add)

    # TODO: Create pairings for old engines, strictly against latest ones, for historical record

    return redirect('stage_pairings', stage_id=stage.id)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                         C L I E N T                                         #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def client_auth(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # Present in all client requests, except the initial connection
        worker_id = request.POST.get('worker_id')
        secret    = request.POST.get('secret')

        if not worker_id or not secret:
            return JsonResponse({ 'error': 'Authentication information not provided.' })

        if not (worker := Worker.objects.filter(id=worker_id, secret=secret).first()):
            return JsonResponse({ 'error': 'Provided information does not match an existing Worker.' })

        return view_func(request, worker, *args, **kwargs)

    return wrapper

@csrf_exempt
@require_POST
def client_connect(request):

    username  = request.POST.get('username')
    password  = request.POST.get('password')
    worker_id = request.POST.get('worker_id')
    secret    = request.POST.get('secret')
    hardware  = json.loads(request.POST.get('hardware'))

    if not username or not password:
        return JsonResponse({ 'error' : 'Missing username or password.' })

    if not (user := authenticate(request, username=username, password=password)):
        return JsonResponse({ 'error' : 'Failed to authenticate user.' })

    if not user.enabled:
        return JsonResponse({ 'error' : 'Authenticated successfully, but the user is not enabled.' })

    if not hardware or 'logical_cores' not in hardware:
        return JsonResponse({ 'error' : 'Must provide at least logical_cores for hardware info.' })

    worker = None # Attempt to fetch an already saved Worker
    if worker_id and secret:
        worker = Worker.objects.filter(id=worker_id, secret=secret, user=user).first()

    if not worker: # No such Worker found, create a new one
        worker = Worker.objects.create(user=user, secret=secrets.token_hex(32))

    worker.hwinfo = hardware
    worker.save()

    return JsonResponse({
        'secret'    : worker.secret,
        'worker_id' : worker.id,
    })

@csrf_exempt
@require_POST
@client_auth # Source of the worker argument
def client_request_work(request, worker):

    # TODO: This should be filtered for private engines, to ensure the user can build it
    # TODO: This should be filtered to ensure core counts are sufficient
    # TODO: This should be filtered to ensure memory reqs. are met

    pairing = (
        Pairing.objects
        .select_related('stage__rating_list')
        .filter(finished=False)
        .order_by('book_index', 'id')
        .first()
    )

    if not pairing:
        return JsonResponse({ 'warning' : 'No pairings need to be to played right now. ' })

    workload = {
        'config' : {
            'games'          : pairing.workload_size(worker),
            'pairing_id'     : pairing.id,
            'thread_count'   : pairing.stage.rating_list.thread_count,
            'hashsize'       : pairing.stage.rating_list.hashsize,
            'base_time'      : pairing.stage.rating_list.base_time,
            'increment'      : pairing.stage.rating_list.increment,
        },
        'book' : {
            'rating_list_id' : pairing.stage.rating_list.id,
            'name'           : pairing.stage.rating_list.book,
            'sha256'         : pairing.stage.rating_list.book_sha,
        },
        'engine_a' : {
            'image'     : pairing.engine_a.image_name(),
            'nps'       : pairing.engine_a.nps,
            'engine_id' : pairing.engine_a.id,
            'sha256'    : pairing.engine_a.tarball_sha,
        },
        'engine_b' : {
            'image'     : pairing.engine_b.image_name(),
            'nps'       : pairing.engine_b.nps,
            'engine_id' : pairing.engine_b.id,
            'sha256'    : pairing.engine_b.tarball_sha,
        },
    }

    # Kick book_index as a pseudo priority mechanism
    Pairing.objects.filter(pk=pairing.pk).update(book_index=F('book_index') + workload['config']['games'])

    return JsonResponse(workload)

@csrf_exempt
@require_POST
@client_auth # Source of the worker argument
def client_pull_image(request, worker):

    engine_id = request.POST.get('engine_id')
    if not engine_id or not (engine := Engine.objects.filter(id=engine_id).first()):
        return JsonResponse({ 'error' : 'Attempting to pull non-existent engine image' })

    # TODO: We must verify that this worker is eligible for the requested image
    # TODO: We must throw a SERIOUS flag if the tarball is missing

    path = settings.ENGINE_ARTIFACT_DIR / engine.tarball_name()
    return FileResponse(open(path, 'rb'), as_attachment=True, filename=engine.tarball_name())

@csrf_exempt
@require_POST
@client_auth # Source of the worker argument
def client_pull_book(request, worker):

    rating_list_id = request.POST.get('rating_list_id')
    if not rating_list_id or not (rating_list := RatingList.objects.filter(id=rating_list_id).first()):
        return JsonResponse({ 'error' : 'Attempting to pull book from non-existent Rating List' })

    path = settings.BOOK_ARTIFACT_DIR / rating_list.book_artifact()
    return FileResponse(open(path, 'rb'), as_attachment=True, filename=rating_list.book_artifact())
