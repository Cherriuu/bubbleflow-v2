from django.contrib import admin

from .models import (
    Shop,
    StorageLocation,
    PreparedItem,
    Batch,
    InventoryEvent,
    MenuItem,
    RecipeComponent,
    Order,
    OrderItem,
)

admin.site.register(Shop)
admin.site.register(StorageLocation)
admin.site.register(PreparedItem)
admin.site.register(Batch)
# Inventory events are an append-only ledger, so the admin can view them but not add, change, or delete them.
# Fix mistakes by recording a correction through the app.
@admin.register(InventoryEvent)
class InventoryEventAdmin(admin.ModelAdmin):
    list_display = ["id", "batch", "event_type", "quantity_delta", "order_item", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(MenuItem)
admin.site.register(RecipeComponent)
admin.site.register(Order)
admin.site.register(OrderItem)