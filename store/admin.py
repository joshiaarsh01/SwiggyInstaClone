from django.contrib import admin
from .models import (
    Admin, Brand, Customer, Delivery, Deliverypartner, Payment, Product, Reviews, ProductVariant, Order, OrderLineItem,
    Godown, ProductStock, VariantStock, StockTransfer
)

admin.site.register(Admin)
admin.site.register(Brand)
admin.site.register(Customer)
admin.site.register(Delivery)
admin.site.register(Deliverypartner)
admin.site.register(Payment)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ('stock',)
        return ()
admin.site.register(Reviews)
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ('stock',)
        return ()
admin.site.register(Order)
admin.site.register(OrderLineItem)
admin.site.register(Godown)


def get_manager_godown(request):
    if request.user.is_superuser:
        return None
    return Godown.objects.filter(manager=request.user).first()


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'godown', 'product', 'quantity')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        godown = get_manager_godown(request)
        if godown:
            return qs.filter(godown=godown)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "godown" and not request.user.is_superuser:
            godown = get_manager_godown(request)
            if godown:
                kwargs["queryset"] = Godown.objects.filter(pk=godown.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            godown = get_manager_godown(request)
            if godown:
                obj.godown = godown
        super().save_model(request, obj, form, change)


@admin.register(VariantStock)
class VariantStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'godown', 'variant', 'quantity')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        godown = get_manager_godown(request)
        if godown:
            return qs.filter(godown=godown)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "godown" and not request.user.is_superuser:
            godown = get_manager_godown(request)
            if godown:
                kwargs["queryset"] = Godown.objects.filter(pk=godown.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            godown = get_manager_godown(request)
            if godown:
                obj.godown = godown
        super().save_model(request, obj, form, change)


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_godown', 'to_godown', 'product', 'variant', 'quantity', 'transferred_at')

    def save_model(self, request, obj, form, change):
        if change:
            self.message_user(request, "Editing existing transfers is not allowed. Create a new transfer instead.", level='error')
            return

        if obj.quantity <= 0:
            self.message_user(request, "Quantity must be greater than 0.", level='error')
            return

        if obj.product:
            source_stock, _ = ProductStock.objects.get_or_create(
                godown=obj.from_godown, product=obj.product, defaults={'quantity': 0}
            )
            dest_stock, _ = ProductStock.objects.get_or_create(
                godown=obj.to_godown, product=obj.product, defaults={'quantity': 0}
            )
        elif obj.variant:
            source_stock, _ = VariantStock.objects.get_or_create(
                godown=obj.from_godown, variant=obj.variant, defaults={'quantity': 0}
            )
            dest_stock, _ = VariantStock.objects.get_or_create(
                godown=obj.to_godown, variant=obj.variant, defaults={'quantity': 0}
            )
        else:
            self.message_user(request, "You must select either a Product or a Variant.", level='error')
            return

        if source_stock.quantity < obj.quantity:
            self.message_user(
                request,
                f"Not enough stock in {obj.from_godown}. Available: {source_stock.quantity}, requested: {obj.quantity}",
                level='error'
            )
            return

        source_stock.quantity -= obj.quantity
        dest_stock.quantity += obj.quantity
        source_stock.save()
        dest_stock.save()

        super().save_model(request, obj, form, change)