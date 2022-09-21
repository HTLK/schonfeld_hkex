from django import forms

class HKEXForm(forms.Form):
    stock_code = forms.CharField()
    start_date = forms.CharField()
    end_date = forms.CharField()
    change_threshold = forms.CharField()
