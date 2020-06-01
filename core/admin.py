from django.contrib import admin
from .models import Item, OrderItem, Order, Payment, Cupon, Refund, Address


# Register your models here.
def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update order to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ordered',
        'being_delivered',
        'received',
        'refund_requested',
        'refund_granted',
        'shipping_address',
        'billing_address',
        'payment',
        'cupon',
    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payment',
        'cupon',
    ]
    list_filter = [
        'ordered',
        'being_delivered',
        'received',
        'refund_requested',
        'refund_granted',
    ]
    search_fields = ['user__username', 'refer_code']
    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'appartment_adress',
        'country',
        'zip',
        'address_type',
        'default',
    ]
    list_filter = ['default', 'country', 'address_type']

    search_fields = [
        'user',
        'street_address',
        'appartment_adress',
        'country',
        'zip',
    ]


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Cupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
