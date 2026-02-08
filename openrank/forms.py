from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import EngineFamily, Engine, RatingList, RatingListStage

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [ 'username', 'email' ]

class EngineFamilyForm(forms.ModelForm):
    class Meta:
        model = EngineFamily
        fields = [ 'name', 'author', 'website' ]

class EngineForm(forms.ModelForm):
    class Meta:
        model = Engine
        fields = [ 'family', 'version', 'release_date', 'disabled', 'latest', 'nps' ]
        widgets = { 'release_date': forms.DateInput(attrs={ 'type' : 'date'}) }

class RatingListForm(forms.ModelForm):
    class Meta:
        model = RatingList
        fields = ['name', 'thread_count', 'hashsize', 'base_time', 'increment', 'book']

class RatingListStageForm(forms.ModelForm):
    class Meta:
        model = RatingListStage
        fields = ['top_n_engines', 'games']
