from django import forms
from .models import TailDownCart
from account.models import JobDetails
from customer.models import TailDownOrder
from datetime import date

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
    chainLength = forms.CharField(required=False)

    class Meta:
        model = TailDownCart
        #Ensure these names match your Model's field names exactly
        fields = [
            'orderName','quantity', 'deliverBy',
            'showName', 'cableFinishes', 'cableSize',
            'cableLengthFt', 'cableLengthIn', 
            'topType', 'endType', 'turnbuckle', 
            'chain', 'tcOrder', 'turnbuckleSize','chainLength',
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
        deliver_by = cleaned_data.get("deliverBy")
        ft = cleaned_data.get('cableLengthFt')
        inches = cleaned_data.get('cableLengthIn')
        turnbuckle = cleaned_data.get('turnbuckle')
        chain = cleaned_data.get('chain')
        order = cleaned_data.get('tcOrder')
        tb_size = cleaned_data.get('turnbuckleSize')
        chain_length = cleaned_data.get('chainLength')

        #Ensure order name is not blank or whitespace-only
        if not name or name.strip() == "":
            self.add_error('orderName', 'Name cannot be empty.')

        #Validate quantity range (only if a value was provided)
        if quantity is not None:
            if quantity < 1 or quantity > 25:
                self.add_error('quantity', 'Please enter a quantity between 1 and 25.')

        # Delivery date validation
        if deliver_by:
            if deliver_by < date.today():
                self.add_error('deliverBy', 'Delivery date cannot be in the past.')
        else:
            self.add_error('deliverBy', 'Please select a delivery date.')

        # Cable length validation
        if ft is None and inches is None:
            self.add_error('cableLengthFt', 'Please enter a cable length.')
        else:
            if ft is not None and ft < 0:
                self.add_error('cableLengthFt', 'Feet cannot be negative.')
            if ft is not None and ft > 70:
                self.add_error('cableLengthFt', 'Feet cannot exceed 70.')
            if inches is not None:
                if inches < 0 or inches >= 12:
                    self.add_error('cableLengthIn', 'Inches must be between 0 and 11.')
            if (ft == 0 or ft is None) and (inches == 0 or inches is None):
                self.add_error('cableLengthFt', 'Cable length cannot be zero.')

            # # Warning for long cables (70+ ft)
            total_inches = (ft or 0) * 12 + (inches or 0)
            if total_inches >= 840:
                self.cable_length_warning = "Cable length is 70 ft or more. Please double-check the measurement."

        #If the turnbuckle checkbox is selected, a size must also be chosen
        if turnbuckle and not tb_size:
            self.add_error('turnbuckleSize', 'Turnbuckle is selected, so size is required.')

        #Hardware selected but no order method specified — user must choose how to order
        if (turnbuckle or chain) and (order == 'none' or not order):
            self.add_error('tcOrder', 'Please specify the order for the hardware selected.')
        
        #No hardware selected but an order method was specified — inconsistent state
        if not turnbuckle and not chain and (order and order != 'none'):
             self.add_error('tcOrder', 'If no hardware is selected, Order must be "None".')

        if chain and not chain_length:
            self.add_error('chainLength', 'Chain is selected, so chain length is required.')

        # # Chain length should be empty when chain is not selected
        if not chain and chain_length:
            self.add_error('chainLength', 'Chain length should be empty when chain is not selected.')

        return cleaned_data
    
class TailDownOrderEditForm(forms.ModelForm):
    showName = forms.ModelChoiceField(
        queryset=JobDetails.objects.all(),
        to_field_name='jobId',
        empty_label="Select a Show",
        error_messages={'required': 'Please select a valid Show Name.'}
    )
    turnbuckleSize = forms.CharField(required=False)
    chainLength = forms.CharField(required=False)

    class Meta:
        model = TailDownOrder
        fields = [
            'orderName', 'quantity','deliverBy',
            'showName', 'cableSize', 'cableFinishes',
            'cableLengthFt', 'cableLengthIn', 
            'topType', 'endType', 'turnbuckle',
            'chain', 'tcOrder', 'turnbuckleSize', 'chainLength','status'
        ]

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("orderName")
        quantity = cleaned_data.get("quantity")
        deliver_by = cleaned_data.get("deliverBy")
        ft = cleaned_data.get('cableLengthFt')
        inches = cleaned_data.get('cableLengthIn')
        turnbuckle = cleaned_data.get('turnbuckle')
        chain = cleaned_data.get('chain')
        order = cleaned_data.get('tcOrder')
        tb_size = cleaned_data.get('turnbuckleSize')
        chain_length = cleaned_data.get('chainLength')

        if not name or name.strip() == "":
            self.add_error('orderName', 'Name cannot be empty.')

        if quantity is not None:
            if quantity < 1 or quantity > 25:
                self.add_error('quantity', 'Please enter a quantity between 1 and 25.')

        # Delivery date validation
        # On edit: only reject a past date if the user actually changed it.
        # This allows editing old orders (e.g. fixing a typo, updating status)
        # without the already-passed delivery date blocking the save.
        if deliver_by:
            if deliver_by < date.today() and deliver_by != self.instance.deliverBy:
                self.add_error('deliverBy', 'Delivery date cannot be in the past.')
        else:
            self.add_error('deliverBy', 'Please select a delivery date.')

        # Cable length validation
        if ft is None and inches is None:
            self.add_error('cableLengthFt', 'Please enter a cable length.')
        else:
            if ft is not None and ft < 0:
                self.add_error('cableLengthFt', 'Feet cannot be negative.')
            if ft is not None and ft > 70:
                self.add_error('cableLengthFt', 'Feet cannot exceed 70.')
            if inches is not None:
                if inches < 0 or inches >= 12:
                    self.add_error('cableLengthIn', 'Inches must be between 0 and 11.')
            if (ft == 0 or ft is None) and (inches == 0 or inches is None):
                self.add_error('cableLengthFt', 'Cable length cannot be zero.')

            # Warning for long cables (70+ ft)
            total_inches = (ft or 0) * 12 + (inches or 0)
            if total_inches >= 840:
                self.cable_length_warning = "Cable length is 70 ft or more. Please double-check the measurement."

        if turnbuckle and not tb_size:
            self.add_error('turnbuckleSize', 'Turnbuckle is selected, so size is required.')

        if (turnbuckle or chain) and (order == 'none' or not order):
            self.add_error('tcOrder', 'Please specify the order for the hardware selected.')

        if not turnbuckle and not chain and (order and order != 'none'):
            self.add_error('tcOrder', 'If no hardware is selected, Order must be "None".')

        if chain and not chain_length:
            self.add_error('chainLength', 'Chain is selected, so chain length is required.')

        if not chain and chain_length:
            self.add_error('chainLength', 'Chain length should be empty when chain is not selected.')

        return cleaned_data