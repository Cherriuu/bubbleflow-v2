# Custom permissions for the operations app.
from rest_framework.permissions import IsAuthenticated


# Only allow logged-in users who own a shop.
# Users without a shop (such as an admin superuser) are rejected instead of crashing on request.user.shop.
class IsShopUser(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and hasattr(request.user, "shop")
        )
