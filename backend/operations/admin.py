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
admin.site.register(InventoryEvent)
admin.site.register(MenuItem)
admin.site.register(RecipeComponent)
admin.site.register(Order)
admin.site.register(OrderItem)