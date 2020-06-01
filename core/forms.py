from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal'),
)


class CheckOutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "1234 Main St"}))
    appartment_adress = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Apartment or suite"}))
    country = CountryField(
        blank_label='(select country)').formfield(widget=CountrySelectWidget(
            attrs={"class": "custom-select d-block w-100"}))
    zip = forms.CharField(widget=forms.TextInput(
        attrs={"class": "form-control"}))
    same_billing_address = forms.BooleanField(required=False,
                                              widget=forms.CheckboxInput())
    save_info = forms.BooleanField(required=False,
                                   widget=forms.CheckboxInput())
    payment_options = forms.ChoiceField(widget=forms.RadioSelect,
                                        choices=PAYMENT_CHOICES)


class CuponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'promo code',
            'aria-label': "Recipient's username",
            'aria-describedby': "basic-addon2"
        }))


class RefundForm(forms.Form):
    ref_code = forms.CharField(max_length=20)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    email = forms.EmailField()
