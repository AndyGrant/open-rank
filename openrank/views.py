from django.shortcuts import render, get_object_or_404, redirect

from openrank.models import *
from openrank.forms import *

def index(request):
    return render(request, 'index.html')

def create_or_edit_family(request, pk=None):

    family = get_object_or_404(EngineFamily, pk=pk) if pk else None

    if request.method == 'POST':
        form = EngineFamilyForm(request.POST, request.FILES, instance=family)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = EngineFamilyForm(instance=family)

    return render(request, 'admin_family.html', { 'form' : form })

def create_or_edit_engine(request, pk=None):

    engine = get_object_or_404(Engine, pk=pk) if pk else None

    if request.method == 'POST':
        form = EngineForm(request.POST, request.FILES, instance=engine)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = EngineForm(instance=engine)

    return render(request, 'admin_engine.html', { 'form' : form })

def list_families(request):
    context = { 'families' : EngineFamily.objects.all() }
    return render(request, 'list_families.html', context)

def list_engines(request):
    context = { 'engines' : Engine.objects.all() }
    return render(request, 'list_engines.html', context)
