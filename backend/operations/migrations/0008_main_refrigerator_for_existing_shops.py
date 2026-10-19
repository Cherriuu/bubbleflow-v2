from django.db import migrations


# Give every shop with no storage locations a Main Refrigerator, so shops registered before setup existed can start batches
def add_main_refrigerators(apps, schema_editor):
    Shop = apps.get_model("operations", "Shop")
    StorageLocation = apps.get_model("operations", "StorageLocation")

    for shop in Shop.objects.filter(storage_locations__isnull=True):
        StorageLocation.objects.create(
            shop=shop,
            name="Main Refrigerator",
            location_type="refrigerator"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0007_prepareditem_is_topping'),
    ]

    # Nothing to undo: the locations are ordinary data once created
    operations = [
        migrations.RunPython(add_main_refrigerators, migrations.RunPython.noop),
    ]
