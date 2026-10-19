from django.urls import path
from . import menu_views, views

urlpatterns = [
    # Health check endpoint
    path("health/", views.health_check),

    # Basic data
    path("prepared-items/", views.prepared_items),
    path("storage-locations/", views.storage_locations),
    path("batches/", views.batches),
    path("menu-items/", views.menu_items),
    path("orders/", views.orders),
    path("toppings/", views.toppings),

    # Batch actions
    path("batches/create/", views.create_batch_view),
    path("batches/<int:batch_id>/ready/", views.mark_batch_ready_view),
    path("batches/<int:batch_id>/waste/", views.record_waste_view),
    path("batches/<int:batch_id>/correction/", views.record_correction_view),
    path("batches/<int:batch_id>/events/", views.batch_events_view),

    # Order actions
    path("orders/create/", views.create_order_view),
    path("orders/<int:order_id>/complete/", views.complete_order_view),
    # Removed cancel order endpoint for now, might be added back later.
    #path("orders/<int:order_id>/cancel/", views.cancel_order_view),

    # Menu setup
    path("menu/ingredients/", menu_views.ingredients_view),
    path("menu/ingredients/<int:ingredient_id>/", menu_views.ingredient_detail_view),
    path("menu/drinks/", menu_views.drinks_view),
    path("menu/drinks/<int:drink_id>/", menu_views.drink_detail_view),

    # Dashboard
    path("inventory/", views.inventory_summary_view),
    path("recommendations/", views.recommendations_view),
]