# Handles HTTP requests and responses and API endpoints for the operations app.
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
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
    WasteSerializer,
    CorrectionSerializer,
    CreateOrderSerializer,
    InventoryEventSerializer,
)

from .services.inventory import (
    create_batch,
    get_item_inventory,
    get_estimated_servings,
    get_inventory_status,
    record_waste,
    record_correction,
    get_batch_balance,
    mark_batch_ready,
    update_batch_status,
)

from .services.orders import (
    create_order,
    complete_order,
    #cancel_order,
)

from .services.forecasting import recommend_production, get_start_by


# Check that the API is running
@api_view(["GET"])
@permission_classes([AllowAny]) # The only data endpoint that doesn't need a logged-in shop
def health_check(request):
    return Response({"status": "ok"})


# Check whether a list request asked for hidden items too, with ?include_inactive=true
def include_inactive(request):
    return request.query_params.get("include_inactive") == "true"


# Get all prepared items
@api_view(["GET"]) # Only accept GET requests for this endpoint
def prepared_items(request): # Request is the HTTP request object that contains all the information about the incoming request
    # Get the logged-in shop's prepared items from the database using Django ORM
    items = PreparedItem.objects.filter(
        shop=request.user.shop
    )

    # Hidden items stay out of dropdowns; pages that show names for old batches ask for them too
    if not include_inactive(request):
        items = items.filter(is_active=True)

    # Serialize the items queryset to simple Python data types that can be rendered into JSON
    serializer = PreparedItemSerializer(
        items,
        many=True
    )

    # Django Rest Framework takes the serialized data and render it into JSON to be sent back in the HTTP response
    return Response(serializer.data)


# Get the active ingredients that can be added to drinks as toppings
@api_view(["GET"])
def toppings(request):
    items = PreparedItem.objects.filter(
        shop=request.user.shop,
        is_active=True,
        is_topping=True
    ).order_by("name")

    serializer = PreparedItemSerializer(
        items,
        many=True
    )

    return Response(serializer.data)


# Get all storage locations
@api_view(["GET"])
def storage_locations(request):
    locations = StorageLocation.objects.filter(
        shop=request.user.shop
    )

    serializer = StorageLocationSerializer(
        locations,
        many=True
    )

    return Response(serializer.data)


@api_view(["GET"])
def batches(request):
    batches = Batch.objects.filter(
        prepared_item__shop=request.user.shop
    )

    for batch in batches:
        update_batch_status(batch)

    serializer = BatchSerializer(
        batches,
        many=True
    )

    return Response(serializer.data)


# Get all menu items
@api_view(["GET"])
def menu_items(request):
    items = MenuItem.objects.filter(
        shop=request.user.shop
    )

    if not include_inactive(request):
        items = items.filter(is_active=True)

    serializer = MenuItemSerializer(
        items,
        many=True
    )

    return Response(serializer.data)


# Get all orders
@api_view(["GET"])
def orders(request):
    orders = Order.objects.filter(
        shop=request.user.shop
    )

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
            shop=request.user.shop,
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
    # Returns a 404 Not Found response if the batch belongs to another shop
    batch = get_object_or_404(
        Batch,
        id=batch_id,
        prepared_item__shop=request.user.shop
    )

    # Returns a 400 Bad Request response if the batch is not preparing or cooling
    try:
        batch = mark_batch_ready(batch)

    except ValueError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        BatchSerializer(batch).data,
        status=status.HTTP_200_OK
    )

# Record wasted inventory
@api_view(["POST"])
def record_waste_view(request, batch_id):
    # Returns a 404 Not Found response if the batch belongs to another shop
    batch = get_object_or_404(
        Batch,
        id=batch_id,
        prepared_item__shop=request.user.shop
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

    # Waste can use up the batch, so reload it to get the new status
    batch.refresh_from_db()

    serializer = BatchSerializer(batch)

    return Response(serializer.data)


# Correct inventory manually
@api_view(["POST"])
def record_correction_view(request, batch_id):
    # Returns a 404 Not Found response if the batch belongs to another shop
    batch = get_object_or_404(
        Batch,
        id=batch_id,
        prepared_item__shop=request.user.shop
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

    # A correction can change the batch's status (depleted or ready again), so reload it
    batch.refresh_from_db()

    serializer = BatchSerializer(batch)

    return Response(serializer.data)


# Get a batch's inventory history, newest first, with its current balance and status
@api_view(["GET"])
def batch_events_view(request, batch_id):
    # Returns a 404 Not Found response if the batch belongs to another shop
    batch = get_object_or_404(
        Batch,
        id=batch_id,
        prepared_item__shop=request.user.shop
    )

    events = batch.inventory_events.select_related(
        "order_item"
    ).order_by(
        "-created_at",
        "-id"
    )

    return Response({
        "balance": get_batch_balance(batch),
        "status": batch.status,
        "events": InventoryEventSerializer(events, many=True).data
    })


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
        # Always the logged-in shop, never a shop sent in the request body
        order, warnings = create_order(
            shop=request.user.shop,
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
    # Returns a 404 Not Found response if the order belongs to another shop
    order = get_object_or_404(
        Order,
        id=order_id,
        shop=request.user.shop
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
        shop=request.user.shop,
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


# Get production recommendations and when to start each batch
@api_view(["GET"])
def recommendations_view(request):
    items = PreparedItem.objects.filter(
        shop=request.user.shop,
        is_active=True
    )

    recommendations = []

    for item in items:
        recommendation = recommend_production(item)

        recommendations.append({
            "id": item.id,
            "name": item.name,
            "base_unit": item.base_unit,
            "recommended_quantity": recommendation,
            "start_by": get_start_by(item)
        })

    return Response(recommendations)
