from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from itertools import combinations

from openrank.forms import *
from openrank.models import *

def index(request):
    return render(request, 'index.html')


def create_or_edit_instance(request, obj, form, template):

    if request.method == 'POST':
        form = form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = form(instance=obj)

    return render(request, template, { 'form' : form })

def create_or_edit_family(request, pk=None):
    obj = get_object_or_404(EngineFamily, pk=pk) if pk else None
    return create_or_edit_instance(request, obj, EngineFamilyForm, 'admin_family.html')

def create_or_edit_engine(request, pk=None):
    obj = get_object_or_404(Engine, pk=pk) if pk else None
    return create_or_edit_instance(request, obj, EngineForm, 'admin_engine.html')

def create_or_edit_rating_list(request, pk=None):
    obj = get_object_or_404(RatingList, pk=pk) if pk else None
    return create_or_edit_instance(request, obj, RatingListForm, 'admin_rating_list.html')

def create_or_edit_pairing(request, pk1, pk2=None):
    obj   = get_object_or_404(Pairing, rating_list_id=pk1, pk=pk2)
    return create_or_edit_instance(request, obj, PairingForm, 'admin_pairing.html')


def list_families(request):
    context = { 'families' : EngineFamily.objects.all() }
    return render(request, 'list_families.html', context)

def list_engines(request):
    context = { 'engines' : Engine.objects.all() }
    return render(request, 'list_engines.html', context)

def list_rating_lists(request):
    context = { 'lists' : RatingList.objects.all() }
    return render(request, 'list_rating_lists.html', context)

def list_pairings(request, pk):
    context = { 'pairings' : Pairing.objects.filter(rating_list=pk) }
    return render(request, 'list_pairings.html', context)


def generate_pairings(request, pk):

    rating_list = RatingList.objects.get(pk=pk)
    pairings    = Pairing.objects.filter(rating_list=rating_list)

    # Ensure pairings exist between all latest Engines
    primary_pks = list(EngineFamily.objects.values_list('latest', flat=True))
    for first, second in combinations(primary_pks, 2):
        Pairing.objects.get_or_create(rating_list=rating_list, engine1_id=first, engine2_id=second)

    # For any non-primary engine without any Pairings, generate them against all primary engines
    secondary = Engine.objects.exclude(pk__in=Subquery(EngineFamily.objects.values('latest')))
    for engine in secondary:
        if not Pairing.objects.filter(Q(engine1=engine) | Q(engine2=engine)).exists():
            for pk in primary_pks:
                Pairing.objects.create(rating_list=rating_list, engine1=engine, engine2_id=pk)

    return redirect('index')