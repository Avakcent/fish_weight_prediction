from django import forms
from .models import FishData

VALID_SPECIES = ['Bream', 'Parkki', 'Perch', 'Pike', 'Roach', 'Smelt', 'Whitefish']

class FishDataForm(forms.ModelForm):
    species = forms.ChoiceField(choices=[(s, s) for s in VALID_SPECIES], label="Вид рыбы")
    
    class Meta:
        model = FishData
        fields = ['species', 'length1', 'length2', 'length3', 'height', 'width']
        labels = {
            'length1': 'Длина 1 (см)',
            'length2': 'Длина 2 (см)',
            'length3': 'Длина 3 (см)',
            'height': 'Высота (см)',
            'width': 'Ширина (см)'
        }

    def clean_species(self):
        species = self.cleaned_data['species']
        if species not in VALID_SPECIES:
            raise forms.ValidationError("Недопустимый вид рыбы")
        return species

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='Выберите Excel-файл',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )