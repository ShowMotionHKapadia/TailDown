import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class TailDownOrder(models.Model):
    #Allowed values for the cableFinishes field — stored as short codes, displayed as full labels
    CABLE_FINISH_CHOICES = [('GAL', 'Galvanized'), ('BLK', 'Blackened')]

    #Links the order to a user; deleting the user also deletes all their orders
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    #Auto-generated UUID used as the primary key instead of an auto-increment integer,
    #making order IDs harder to guess or enumerate
    orderId = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)

    #Human-readable name for the order, pre-filled with a sensible default
    orderName = models.CharField(max_length=255, default="TailDown No 1")

    #Finish applied to the cable; restricted to the two choices defined above
    cableFinishes = models.CharField(max_length=10, choices=CABLE_FINISH_CHOICES, verbose_name=("Cable Finishes"))

    #Diameter/size of the cable (e.g. '1/4"', '3/8"')
    cableSize = models.CharField(max_length=10, verbose_name=("Cable Size"))

    #The show/job this order belongs to; deleting the job cascades and removes related orders
    showName = models.ForeignKey("account.JobDetails", verbose_name=("ShowName"), on_delete=models.CASCADE)

    #Fitting type for the top end of the cable assembly (Big / Small / None)
    topType = models.CharField(max_length=10, verbose_name=("Top Type"))

    #Fitting type for the bottom end of the cable assembly (Big / Small / None)
    endType = models.CharField(max_length=10, verbose_name=("End Type"))

    #Whether a turnbuckle is included in the order
    turnbuckle = models.BooleanField(default=False, verbose_name=("Turnbuckle"))

    #Whether a chain is included in the order
    chain = models.BooleanField(default=False, verbose_name=("Chain"))

    #Assembly order of the hardware, e.g. 'OT' (Only Turnbuckle), 'TC' (Turnbuckle then Chain)
    tcOrder = models.CharField(max_length=10, verbose_name=("Turnbuckle & Chain Order"))

    #Physical size of the turnbuckle (e.g. '1/2"X6"'); only relevant when turnbuckle=True
    turnbuckleSize = models.CharField(max_length=10, verbose_name=("Turnbuckle &Size"))

    #Number of units ordered; enforced between 1 and 25 at the database and form level
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1),MaxValueValidator(25)]) 

    #Tracks where the order is in the workflow; defaults to 'Draft' on creation
    status = models.CharField(max_length=20, default="Draft", verbose_name=("Order Status"))

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        #Identifies the order by the customer's username in admin and shell output
        return f"{self.customer.username}"
    
    #Permission to view all customer data
    class Meta:
        permissions = [
            ('view_all_taildownorders', 'Can view all customer orders'),
        ]


class TailDownCart(models.Model):
    #Allowed values for the cableFinishes field — stored as short codes, displayed as full labels
    CABLE_FINISH_CHOICES = [('GAL', 'Galvanized'), ('BLK', 'Blackened')]

    #Links the order to a user; deleting the user also deletes all their orders
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    #Auto-generated UUID used as the primary key instead of an auto-increment integer,
    #making order IDs harder to guess or enumerate
    orderId = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)

    #Human-readable name for the order, pre-filled with a sensible default
    orderName = models.CharField(max_length=255, default="TailDown No 1")

    #Finish applied to the cable; restricted to the two choices defined above
    cableFinishes = models.CharField(max_length=10, choices=CABLE_FINISH_CHOICES, verbose_name=("Cable Finishes"))

    #Diameter/size of the cable (e.g. '1/4"', '3/8"')
    cableSize = models.CharField(max_length=10, verbose_name=("Cable Size"))

    #The show/job this order belongs to; deleting the job cascades and removes related orders
    showName = models.ForeignKey("account.JobDetails", verbose_name=("ShowName"), on_delete=models.CASCADE)

    #Fitting type for the top end of the cable assembly (Big / Small / None)
    topType = models.CharField(max_length=10, verbose_name=("Top Type"))

    #Fitting type for the bottom end of the cable assembly (Big / Small / None)
    endType = models.CharField(max_length=10, verbose_name=("End Type"))

    #Whether a turnbuckle is included in the order
    turnbuckle = models.BooleanField(default=False, verbose_name=("Turnbuckle"))

    #Whether a chain is included in the order
    chain = models.BooleanField(default=False, verbose_name=("Chain"))

    #Assembly order of the hardware, e.g. 'OT' (Only Turnbuckle), 'TC' (Turnbuckle then Chain)
    tcOrder = models.CharField(max_length=10, verbose_name=("Turnbuckle & Chain Order"))

    #Physical size of the turnbuckle (e.g. '1/2"X6"'); only relevant when turnbuckle=True
    turnbuckleSize = models.CharField(max_length=10, verbose_name=("Turnbuckle &Size"))

    #Number of units ordered; enforced between 1 and 25 at the database and form level
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1),MaxValueValidator(25)]) 

    isOrdered = models.BooleanField(default=False, verbose_name=("Cart Order"))

    def __str__(self):
        #Identifies the order by the customer's username in admin and shell output
        return f"{self.customer.username}"
