from django.contrib import admin
from .models import Client
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['code','nom','type_client','telephone','email','actif']
    list_filter   = ['type_client','actif']
    search_fields = ['nom','code','telephone','email']
