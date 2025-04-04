from django.db import models
from .models import Invoice, Discount
from django.urls import reverse
from .forms import TicketReplyForm
from .models import Ticket, TicketReply, HealthInformation, ShippingMethod
from django.utils.html import format_html
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path
from .models import Agent, ChatRequest, ChatMessage, TicketReply
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# Define a custom resource class for Product


class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name')  # Show Category name
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'category', 'type', 'sub_description',
            'how_to_use', 'side_effects', 'drug_interactions',
            'precautions', 'featured', 'sale', 'top_selling',
        )

# Define a custom resource class for Variant


class VariantResource(resources.ModelResource):
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'name')  # Show Product name
    )
    unit = fields.Field(
        column_name='unit',
        attribute='unit',
        widget=ForeignKeyWidget(Unit, 'name')  # Show Unit name
    )
    country_of_origin = fields.Field(
        column_name='country_of_origin',
        attribute='country_of_origin',
        # Show Country of Origin name
        widget=ForeignKeyWidget(CountryOfOrigin, 'name')
    )

    class Meta:
        model = Variant
        fields = (
            'id', 'product', 'unit', 'potency', 'number_of_tablets',
            'price_inr', 'price_usd', 'country_of_origin', 'manufacturer', 'shipping_note',
        )

# Inline class to manage ProductLabel entries within Product admin


class ProductLabelInline(admin.TabularInline):
    model = ProductLabel
    extra = 1  # Number of empty forms to display by default
    fields = ['label', 'value']

# Inline class to manage Variant entries within Product admin


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ['number_of_tablets', 'unit', 'potency', 'price_inr',
              'price_usd', 'country_of_origin', 'manufacturer', 'shipping_note']

# Inline class to manage Inventory entries within Product admin


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty forms to display by default
    fields = ['image']


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource  # Use the custom resource class
    list_display = ('name', 'category', 'type',
                    'featured', 'sale', 'top_selling')
    inlines = [ProductImageInline, ProductLabelInline, VariantInline,
               ]  # Include Inventory inline

# Register Variant model with custom admin options


@admin.register(Variant)
class VariantAdmin(ImportExportModelAdmin):
    resource_class = VariantResource  # Use the custom resource class
    list_display = ('product', 'unit', 'potency', 'price_inr',
                    'price_usd', 'country_of_origin')
    list_filter = ('product', 'unit', 'country_of_origin')
    search_fields = ('product__name', 'unit__name', 'country_of_origin')

    actions = ['delete_selected_variants']

    def delete_selected_variants(self, request, queryset):
        queryset.delete()
        self.message_user(
            request, "Selected variants have been deleted successfully.")

    delete_selected_variants.short_description = "Delete selected variants"

# Register Inventory model with custom admin options


@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin):
    list_display = ('product', 'variant_number_of_tablets', 'stock')
    list_filter = ('product', 'variant')
    search_fields = ('product__name', 'variant__name')

    # Method to display the number_of_tablets in the admin list view
    def variant_number_of_tablets(self, obj):
        return obj.variant.number_of_tablets

    variant_number_of_tablets.short_description = 'Number of Tablets'


@admin.register(Unit)
class UnitAdmin(ImportExportModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    pass


@admin.register(ProductImage)
class ProductImageAdmin(ImportExportModelAdmin):
    pass


@admin.register(ProductLabel)
class ProductLabelAdmin(ImportExportModelAdmin):
    pass


@admin.register(SiteSetting)
class SiteSettingAdmin(ImportExportModelAdmin):
    pass


@admin.register(CountryOfOrigin)
class CountryOfOriginAdmin(ImportExportModelAdmin):
    pass


@admin.register(Cart)
class CartAdmin(ImportExportModelAdmin):
    pass


@admin.register(CartItem)
class CartItemAdmin(ImportExportModelAdmin):
    pass


admin.site.register(Address)
admin.site.register(Shipping)
admin.site.register(Profile)
admin.site.register(DiscountCode)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Reorder)

admin.site.register(Review)
admin.site.register(OrderAttachment)


admin.site.register(ChatRequest)
admin.site.register(ChatMessage)
admin.site.register(ProblemRequest)


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    form = TicketReplyForm
    extra = 1
    readonly_fields = ('created_at',)
    can_delete = False


class TicketAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status',
                    'created_at', 'view_chat_link')
    inlines = [TicketReplyInline]

    def view_chat_link(self, obj):
        url = reverse('ticket-chat', args=[obj.id])
        return format_html('<a href="{}">View Chat</a>', url)

    view_chat_link.short_description = 'Chat'


admin.site.register(Ticket, TicketAdmin)
admin.site.register(HealthInformation)
admin.site.register(ShippingMethod)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order',
                    'amount_due', 'status', 'issued_date']
    list_filter = ['status', 'issued_date']
    search_fields = ['invoice_number', 'order__id']


@admin.register(Discount)
class ProductLabelAdmin(ImportExportModelAdmin):
    pass


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('variant', 'discount_type',
                    'discount_value', 'start_date', 'end_date')


class AgentAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_online')
    fields = ('username', 'password', 'is_online')

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


class AgentAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('username', 'name', 'phone', 'is_online')
    # Enable searching by these fields
    search_fields = ('username', 'name', 'phone')
    list_filter = ('is_online',)  # Enable filtering by 'is_online' status


admin.site.register(Agent, AgentAdmin)


class OrderLabelLink(models.Model):
    class Meta:
        verbose_name = "Order Labels"
        verbose_name_plural = "Order Labels"


class OrderLabelAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        """Redirect to the order labels list view."""
        from django.shortcuts import redirect
        return redirect(reverse("order_label_list"))

    def get_model_perms(self, request):
        """Hide from the model list but show in sidebar."""
        return {"view": True}  # Only enable the "view" permission


# Register the dummy model
admin.site.register(OrderLabelLink, OrderLabelAdmin)
