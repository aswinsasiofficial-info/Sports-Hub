from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('user', 'User'),
    )
    
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'user_type', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Sports Hub Info', {'fields': ('user_type', 'phone_number', 'address')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
    
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    # Custom action to make users owners
    actions = ['make_owner', 'make_user']
    
    def make_owner(self, request, queryset):
        updated = queryset.update(user_type='owner')
        self.message_user(request, f'{updated} user(s) successfully marked as owners.')
    make_owner.short_description = "Mark selected users as Owners"
    
    def make_user(self, request, queryset):
        updated = queryset.update(user_type='user')
        self.message_user(request, f'{updated} user(s) successfully marked as regular users.')
    make_user.short_description = "Mark selected users as Regular Users"

admin.site.register(User, CustomUserAdmin)