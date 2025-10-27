# accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims here
        profile = user.profiles.first()  # get first profile if user has multiple
        token['username'] = user.username
        token['email'] = user.email
        token['profile_types'] = list(user.profiles.values_list('type', flat=True))

        return token
