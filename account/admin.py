from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import User, JobDetails
from axes.models import AccessFailureLog, AccessAttempt

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

# Remove the default Axes admin pages and replace with custom one
admin.site.unregister(AccessFailureLog)
admin.site.unregister(AccessAttempt)

@admin.register(AccessAttempt)
class AccessAttemptAdmin(admin.ModelAdmin):
    list_display = ('attempt_time', 'ip_address', 'username', 'user_agent', 'path_info', 'failures_since_start', 'is_locked')
    list_filter = ('attempt_time', 'path_info')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('attempt_time', 'ip_address', 'username', 'user_agent', 'path_info', 'http_accept', 'failures_since_start', 'get_data', 'post_data')
    actions = ['unlock_users']

    @admin.display(boolean=True, description="Locked Out")
    def is_locked(self, obj):
        from django.conf import settings
        return obj.failures_since_start >= settings.AXES_FAILURE_LIMIT

    @admin.action(description="Unlock selected users")
    def unlock_users(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Successfully unlocked {count} user(s).")