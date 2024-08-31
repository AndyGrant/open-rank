from django import forms
from django.db import IntegrityError, transaction

from openrank.models import *

class EngineFamilyForm(forms.ModelForm):

    class Meta:
        model  = EngineFamily
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

    def clean(self):

        with transaction.atomic():

            data     = super().clean()
            name     = data.get('name')
            families = EngineFamily.objects.filter(name=name)

            if self.instance:
                families = families.exclude(pk=self.instance.pk)

            if families.exists():
                self.add_error('name', 'The Engine Family name must be unique')

            return data

class EngineForm(forms.ModelForm):

    class Meta:
        model   = Engine
        fields  = '__all__'
        widgets = {
            'release_date' : forms.DateInput(attrs={'type': 'date'}),
            'binary'       : forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):

        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if not instance:
            self.fields['hardware'].initial = EngineHardwareType.CPU
            self.fields['classification'].initial = EngineClassification.OPENSOURCE

    def clean(self):

        with transaction.atomic():

            # Ensure that we always have a binary file associated with an engine
            data = super().clean()
            if not data.get('binary'):
                raise forms.ValidationError('A static linux-avx2-popcnt binary must be provided')

            # Ensure only one engine in a family is marked as being most-recent
            Engine.objects.filter(family=data.get('family')).update(most_recent=False)
            self.instance.most_recent = True

            return data
