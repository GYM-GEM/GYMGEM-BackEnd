from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken

def google_callback(request):
    user = request.user

    if not user.is_authenticated:
        return redirect("http://localhost:3000/google-error")

    # generate JWT
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    # redirect to React frontend with tokens
    url = (
        "http://localhost:3000/google-success"
        f"?access={access}"
        f"&refresh={refresh}"
        f"&email={user.email}"
        f"&username={user.username}"
    )

    return redirect(url)
