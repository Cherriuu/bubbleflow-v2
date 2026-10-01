# Handles HTTP requests and responses and API endpoints for the operations app.
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    PreparedItem,
    StorageLocation,
    Batch,
    MenuItem,
    Order,
)

from .serializers import (
    PreparedItemSerializer,
    StorageLocationSerializer,
    BatchSerializer,
    MenuItemSerializer,
    OrderSerializer,
    CreateBatchSerializer,
    MarkBatchReadySerializer,
    WasteSerializer,
    CorrectionSerializer,
    CreateOrderSerializer,
)

from .services.inventory import (
    create_batch,
    get_item_inventory,
    get_estimated_servings,
    get_inventory_status,
    record_waste,
    record_correction,
    mark_batch_ready,
    update_batch_status,
)

from .services.orders import (
    create_order,
    complete_order,
    #cancel_order,
)

from .services.forecasting import recommend_production


# Check that the API is running
@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})


# Get all prepared items
@api_view(["GET"])
def prepared_items(request):
    items = PreparedItem.objects.all()

    serializer = PreparedItemSerializer(
        items,
        many=True
    )

    return Response(serializer.data)


# Get all storage locations
@api_view(["GET"])
def storage_locations(request):
    locations = StorageLocation.objects.all()

    serializer = StorageLocationSerializer(
        locations,
        many=True
    )

    return Response(serializer.data)


# Get all batches
@api_view(["GET"])
def batches(request):
    batches = Batch.objects.all()

    serializer = BatchSerializer(
        batches,
        many=True
    )

    for batch in batches:
        if batch.prepared_item.requires_cooling:
            update_batch_status(batch)

    return Response(serializer.data)


# Get all menu items
@api_view(["GET"])
def menu_items(request):
    items = MenuItem.objects.all()

    serializer = MenuItemSerializer(
        items,
        many=True
    )

    return Response(serializer.data)


# Get all orders
@api_view(["GET"])
def orders(request):
    orders = Order.objects.all()

    serializer = OrderSerializer(
        orders,
        many=True
    )

    return Response(serializer.data)


# Create a new inventory batch
@api_view(["POST"])
def create_batch_view(request):
    # Validate the input data
    input_serializer = CreateBatchSerializer(
        # Data is the data sent in the request body which is parsed into Python data types by Django REST Framework
        data=request.data
    )

    # Returns a 400 Bad Request response if the input data is invalid
    input_serializer.is_valid(
        raise_exception=True
    )

    # Now that the input data is valid, we can access the validated data
    data = input_serializer.validated_data

    # Django ORM takes the validated data and tries to save it to the database using the defined models in models.py
    try:
        batch = create_batch(
            prepared_item=data["prepared_item"],
            storage_location=data["storage_location"],
            batch_fraction=data["batch_fraction"],
            started_at=data["started_at"]
        )

    # Returns a 400 Bad Request response if the input data is invalid
    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Serialize the batch object to simple Python data types that can be rendered into JSON
    serializer = BatchSerializer(batch)

    # Django Rest Framework takes the serialized data and renders it into JSON to be sent back in the HTTP response
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


# Mark a preparing batch as ready
@api_view(["POST"])
def mark_batch_ready_view(request, batch_id):
    batch = get_object_or_404(
        Batch,
        id=batch_id
    )

    input_serializer = MarkBatchReadySerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    try:
        batch = mark_batch_ready(batch)

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = BatchSerializer(batch)

    return Response(serializer.data)


# Record wasted inventory
@api_view(["POST"])
def record_waste_view(request, batch_id):
    batch = get_object_or_404(
        Batch,
        id=batch_id
    )

    input_serializer = WasteSerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    data = input_serializer.validated_data

    try:
        record_waste(
            batch=batch,
            quantity=data["quantity"],
            reason=data["reason"]
        )

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = BatchSerializer(batch)

    return Response(serializer.data)


# Correct inventory manually
@api_view(["POST"])
def record_correction_view(request, batch_id):
    batch = get_object_or_404(
        Batch,
        id=batch_id
    )

    input_serializer = CorrectionSerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    data = input_serializer.validated_data

    try:
        record_correction(
            batch=batch,
            quantity=data["quantity"],
            reason=data["reason"]
        )

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = BatchSerializer(batch)

    return Response(serializer.data)


# Create a customized order
@api_view(["POST"])
def create_order_view(request):
    input_serializer = CreateOrderSerializer(
        data=request.data
    )

    input_serializer.is_valid(
        raise_exception=True
    )

    data = input_serializer.validated_data

    try:
        order, warnings = create_order(
            shop=data["shop"],
            items=data["items"]
        )

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = OrderSerializer(order)

    return Response(
        {
            "order": serializer.data,
            "warnings": warnings
        },
        status=status.HTTP_201_CREATED
    )


# Complete an order and consume inventory
@api_view(["POST"])
def complete_order_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id
    )

    try:
        order = complete_order(order)

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = OrderSerializer(order)

    return Response(serializer.data)


# Cancel an order and restore inventory has been removed for right now, as it is not needed for the MVP. It might be added back later.


# Get current inventory totals
@api_view(["GET"])
def inventory_summary_view(request):
    items = PreparedItem.objects.filter(
        is_active=True
    )

    inventory = []

    for item in items:
        balance = get_item_inventory(item)
        estimated_servings = get_estimated_servings(item)
        inventory_status = get_inventory_status(item)

        inventory.append({
            "id": item.id,
            "name": item.name,
            "base_unit": item.base_unit,
            "inventory": balance,
            "estimated_servings": estimated_servings,
            "status": inventory_status
        })

    return Response(inventory)


# Get production recommendations
@api_view(["GET"])
def recommendations_view(request):
    items = PreparedItem.objects.filter(
        is_active=True
    )

    recommendations = []

    for item in items:
        recommendation = recommend_production(item)

        recommendations.append({
            "id": item.id,
            "name": item.name,
            "base_unit": item.base_unit,
            "recommended_quantity": recommendation
        })

    return Response(recommendations)