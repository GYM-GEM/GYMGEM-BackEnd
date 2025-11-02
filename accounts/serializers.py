from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username','first_name', 'last_name','password', 'email', 'created_at', 'updated_at', 'last_seen', 'default_profile', 'status']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        account = Account(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('firstName', ''),
            last_name=validated_data.get('lastName', ''),
            status=validated_data.get('status', ''),
        )
        account.set_password(validated_data['password'])
        account.save()
        return account

