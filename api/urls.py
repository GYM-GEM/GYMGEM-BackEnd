from django.urls import include, path

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('auth/', include('authenticationAndAuthorization.urls')),
    path('profiles/', include('profiles.urls')),
    path('trainers/', include('trainers.urls')),
]