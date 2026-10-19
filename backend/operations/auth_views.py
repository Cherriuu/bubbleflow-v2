# Handles shop registration, login, logout, and the current session for the operations app.
# Each shop has one login that its employees share. Django's session cookie keeps the shop logged in.
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import LocationType, Shop, StorageLocation
from .serializers import RegisterSerializer, LoginSerializer


DEMO_EMAIL = "demo@bubbleflow.app"


# DRF only checks CSRF for users who are already logged in, so the login views check it themselves.
# Raises a 403 response if the X-CSRFToken header is missing or doesn't match the csrftoken cookie.
def enforce_csrf(request):
    SessionAuthentication().enforce_csrf(request)


# The data the frontend needs about the logged-in shop
def session_data(user):
    return {
        "email": user.email,
        "shop": {
            "id": user.shop.id,
            "name": user.shop.name,
        },
    }


# Register a new shop and its login, then log in
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def register_view(request):
    enforce_csrf(request)

    input_serializer = RegisterSerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    data = input_serializer.validated_data

    # Emails are stored in lowercase so that logging in is not case sensitive
    email = data["email"].strip().lower()

    User = get_user_model()

    if User.objects.filter(username__iexact=email).exists():
        return Response(
            {"error": "An account with this email already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Checks the password against AUTH_PASSWORD_VALIDATORS in settings.py
    # The unsaved user lets the validators reject passwords that are too similar to the email
    try:
        validate_password(
            data["password"],
            user=User(username=email, email=email)
        )

    except ValidationError as error:
        return Response(
            {"error": " ".join(error.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # The user, the shop, and its first storage location are created together, or not at all
    with transaction.atomic():
        user = User.objects.create_user(
            username=email,
            email=email,
            password=data["password"]
        )

        shop = Shop.objects.create(
            owner=user,
            name=data["shop_name"].strip()
        )

        # Every shop starts with somewhere to store its batches
        StorageLocation.objects.create(
            shop=shop,
            name="Main Refrigerator",
            location_type=LocationType.REFRIGERATOR
        )

    login(request, user)

    return Response(
        session_data(user),
        status=status.HTTP_201_CREATED
    )


# Log in to an existing shop
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def login_view(request):
    enforce_csrf(request)

    input_serializer = LoginSerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    data = input_serializer.validated_data

    # Returns None if the email or password is wrong
    user = authenticate(
        request,
        username=data["email"].strip().lower(),
        password=data["password"]
    )

    # The same message for both cases, so the response doesn't reveal which emails have accounts
    if user is None or not hasattr(user, "shop"):
        return Response(
            {"error": "Invalid email or password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    login(request, user)

    return Response(session_data(user))


# Log in to the seeded demo shop without a password
@api_view(["POST"])
@permission_classes([AllowAny])
def demo_login_view(request):
    enforce_csrf(request)

    User = get_user_model()

    user = User.objects.filter(
        username=DEMO_EMAIL,
        shop__isnull=False
    ).first()

    # The demo user only exists after running the seed_demo command
    if user is None:
        return Response(
            {"error": "The demo is not available right now."},
            status=status.HTTP_404_NOT_FOUND
        )

    login(request, user)

    return Response(session_data(user))


# Log out of the current shop
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)

    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


# Get the logged-in shop
# Also sets the csrftoken cookie, which the frontend sends back as the X-CSRFToken header on POST requests
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def me_view(request):
    user = request.user

    if not user.is_authenticated or not hasattr(user, "shop"):
        return Response(
            {"error": "Not logged in."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(session_data(user))
