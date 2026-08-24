from django import forms
from django.utils.translation import get_language
from localflavor.us.forms import USZipCodeField
from localflavor.in_.forms import INZipCodeField
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'first_name',
            'last_name',
            'email',
            'address',
            'postal_code',
            'city',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_language = get_language()
        if current_language == 'ta':  # Tamil / India
            self.fields['postal_code'] = INZipCodeField()
        else:  # Default / English -> US
            self.fields['postal_code'] = USZipCodeField()
