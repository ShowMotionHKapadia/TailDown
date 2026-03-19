from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import User, JobDetails

class UserModelAdmin(UserAdmin):
    model = User
    #The field to be used for displaying users model.
    #These override the definitions on the base UserModelAdmin
    #that reference specific fields on auth.User.
    list_display = ['id','email', 'first_name', 'last_name','company_name','phone','is_staff','is_superuser','is_active', 'is_customer','is_deleted' ,'created_at', 'updated_at']
    list_filter = ['company_name','is_staff', 'is_active', 'is_customer']
    fieldsets = [
                 ("User Cradentials", {'fields': ['email', 'password']}),
                 ("Personal Info", {'fields': ['first_name', 'last_name','company_name','phone']}),
                 ("Permissions", {'fields': ['is_active', 'is_staff', 'is_customer']}),
                 ("Groups & Permissions", {'fields': ['groups', 'user_permissions'],'classes': ['collapse'],'description': 'Assign Django groups or direct permissions to this user.'}),
                ]
    
    # add_fieldsets is not a standard ModelAdmin attribute. UserModelAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    #add_fieldsets is a list of touples. each touple represents a section in the Add User form.
    add_fieldsets = [(None, { 'classes': ['wide'], 'fields': ['email', 'password1', 'password2']})] 
    
    search_fields = ['email', 'first_name', 'last_name','company_name']
    ordering = ['id']
    filter_horizontal = ['groups', 'user_permissions']
 
admin.site.register(User, UserModelAdmin)   

@admin.register(JobDetails)
class JobDetailsAdmin(admin.ModelAdmin):
    list_display = ('jobId','jobNo' ,'showName', 'customer', 'createdOn','is_deleted')
    autocomplete_fields = ['customer'] # This now works because of your search_fields!