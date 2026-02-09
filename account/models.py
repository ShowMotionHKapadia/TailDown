from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

# Custom user manager 
class UserManager(BaseUserManager):
    def create_user(self, email,password=None):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(
            email=self.normalize_email(email),  
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        #create and save superuser with given email and password.
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_customer = True
        user.save(using=self._db)
        
class User(AbstractBaseUser):
    first_name = models.CharField(max_length=255, null=False)
    last_name = models.CharField(max_length=255, null=False)
    company_name = models.CharField(max_length=255, null=False)
    phone = models.CharField(max_length=12,unique=True,null=False)
    email = models.EmailField(max_length=255, unique=True, null=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()

    def __str__(self):
        return self.email
     
    #Only superuser has all permissions to access all data
    def has_perm(self, perm, obj=None):
        return self.is_superuser  
      
    #Does the user have permissions to view the app `app_label`?
    def has_module_perms(self, app_label):
        return self.is_superuser 

# Model to store Job Details
class JobDetails(models.Model):
    jobId = models.AutoField(primary_key=True)
    jobNo = models.CharField(max_length=100, default='100')
    showName = models.CharField(max_length=255)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'is_customer': True}, # Only show customers in the list
        related_name='customer_jobs',
        null=True,
        blank=True
    )
    
    # Auto-filled fields
    createdOn = models.DateTimeField(auto_now_add=True)
    modifiedOn = models.DateTimeField(auto_now=True)
    createdBy = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        limit_choices_to={'is_superuser': True}, 
        null=True,
        related_name='admin_created_jobs'
    )
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Job Detail"         # Name for one record
        verbose_name_plural = "Job Details"  # Name for the sidebar/list

    def __str__(self):
        return f"{self.jobId} -{self.jobNo} - {self.showName}"
