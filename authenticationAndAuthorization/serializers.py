# accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims here
        token['username'] = user.username
        token['email'] = user.email
        token['profile_types'] = list(user.profiles.values_list('profile_type', flat=True))

        return token
