# Handles the Menu page, where a shop sets up its own ingredients and drinks.
# Items are never deleted; turning off is_active hides them from orders and batches.
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import MenuItem, PreparedItem
from .serializers import DrinkSerializer, IngredientSerializer


# List every ingredient in the shop, including hidden ones, or add a new one
@api_view(["GET", "POST"])
def ingredients_view(request):
    shop = request.user.shop

    if request.method == "GET":
        items = PreparedItem.objects.filter(
            shop=shop
        ).order_by("name")

        return Response(IngredientSerializer(items, many=True).data)

    serializer = IngredientSerializer(
        data=request.data,
        context={"shop": shop}
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


# Edit an ingredient. PATCH changes only the fields sent, like turning it on or off.
@api_view(["PUT", "PATCH"])
def ingredient_detail_view(request, ingredient_id):
    shop = request.user.shop

    # Returns a 404 Not Found response if the ingredient belongs to another shop
    item = get_object_or_404(
        PreparedItem,
        id=ingredient_id,
        shop=shop
    )

    serializer = IngredientSerializer(
        item,
        data=request.data,
        partial=request.method == "PATCH",
        context={"shop": shop}
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


# List every drink in the shop with its recipe, including hidden ones, or add a new one
@api_view(["GET", "POST"])
def drinks_view(request):
    shop = request.user.shop

    if request.method == "GET":
        drinks = MenuItem.objects.filter(
            shop=shop
        ).prefetch_related(
            "recipe_components"
        ).order_by("name")

        return Response(DrinkSerializer(drinks, many=True).data)

    serializer = DrinkSerializer(
        data=request.data,
        context={"shop": shop}
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


# Edit a drink. Sending a recipe replaces the whole recipe.
@api_view(["PUT", "PATCH"])
def drink_detail_view(request, drink_id):
    shop = request.user.shop

    # Returns a 404 Not Found response if the drink belongs to another shop
    drink = get_object_or_404(
        MenuItem,
        id=drink_id,
        shop=shop
    )

    serializer = DrinkSerializer(
        drink,
        data=request.data,
        partial=request.method == "PATCH",
        context={"shop": shop}
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)
