from django import forms
from .models import TailDownCart
from account.models import JobDetails

class TailDownCartForm(forms.ModelForm):

    #Custom field to select a show by its jobId, sourced from JobDetails model
    showName = forms.ModelChoiceField(
        queryset=JobDetails.objects.all(),
        to_field_name='jobId',     
        empty_label="Select a Show",
        error_messages={'required': 'Please select a valid Show Name.'}
    )

    #Plain CharField — no choice validation, clean() handles logic manually
    turnbuckleSize = forms.CharField(required=False)

    class Meta:
        model = TailDownCart
        #Ensure these names match your Model's field names exactly
        fields = [
            'orderName','quantity',
            'showName', 'cableFinishes', 'cableSize', 
            'topType', 'endType', 'turnbuckle', 
            'chain', 'tcOrder', 'turnbuckleSize'
        ]

    def clean(self):
        """
        Cross-field validation logic:
          - orderName must not be blank
          - quantity must be between 1 and 25
          - turnbuckleSize is required when turnbuckle is checked
          - tcOrder must be set when any hardware (turnbuckle/chain) is selected
          - tcOrder must be 'none' when no hardware is selected
        """
        cleaned_data = super().clean()
        name = cleaned_data.get("orderName")
        quantity = cleaned_data.get("quantity")
        turnbuckle = cleaned_data.get('turnbuckle')
        chain = cleaned_data.get('chain')
        order = cleaned_data.get('tcOrder')
        tb_size = cleaned_data.get('turnbuckleSize')

        #Ensure order name is not blank or whitespace-only
        if not name or name.strip() == "":
            self.add_error('orderName', 'Name cannot be empty.')

        #Validate quantity range (only if a value was provided)
        if quantity is not None:
            if quantity < 1 or quantity > 25:
                self.add_error('quantity', 'Please enter a quantity between 1 and 25.')

        #If the turnbuckle checkbox is selected, a size must also be chosen
        if turnbuckle and not tb_size:
            self.add_error('turnbuckleSize', 'Turnbuckle is selected, so size is required.')

        #Hardware selected but no order method specified — user must choose how to order
        if (turnbuckle or chain) and (order == 'none' or not order):
            self.add_error('tcOrder', 'Please specify the order for the hardware selected.')
        
        #No hardware selected but an order method was specified — inconsistent state
        if not turnbuckle and not chain and (order and order != 'none'):
             self.add_error('tcOrder', 'If no hardware is selected, Order must be "None".')

        return cleaned_data