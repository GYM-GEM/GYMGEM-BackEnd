from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username','first_name', 'last_name','password', 'email', 'created_at', 'updated_at', 'last_seen', 'default_profile', 'status']