from django import forms
from django.db import IntegrityError, transaction

from openrank.models import *

class EngineFamilyForm(forms.ModelForm):

    class Meta:
        model  = EngineFamily
        fields = '__all__'

    def __init__(self, *args, **kwargs):

        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['latest'].queryset = Engine.objects.filter(family=instance)

        else:
            self.fields.pop('latest', None)

class EngineForm(forms.ModelForm):

    class Meta:
        model   = Engine
        fields  = '__all__'
        widgets = { 'release_date' : forms.DateInput(attrs={'type': 'date'}) }

    def __init__(self, *args, **kwargs):

        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if not instance:
            self.fields['hardware'].initial = EngineHardwareType.CPU
            self.fields['classification'].initial = EngineClassification.OPENSOURCE