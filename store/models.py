from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from decimal import Decimal


# Model for site settings like title and logo

class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('price', 'Fixed Price'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)

    def is_valid(self):
        now = timezone.now()
        if now < self.valid_from or (self.valid_until and now > self.valid_until):
            return False
        if self.usage_limit and self.usage_limit <= 0:  # No usage limit
            return False
        return True

    def apply_discount(self, total_amount):
        if not self.is_valid():
            raise ValidationError("Discount code is not valid.")
        if self.discount_type == 'percentage':
            return total_amount * (1 - self.discount_percentage / 100)
        elif self.discount_type == 'price':
            return max(total_amount - self.discount_price, Decimal('0.00'))
        else:
            raise ValidationError("Invalid discount type.")

    def __str__(self):
        if self.discount_type == 'percentage':
            return f"{self.code} - {self.discount_percentage}%"
        elif self.discount_type == 'price':
            return f"{self.code} - ${self.discount_price}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username


class SiteSetting(models.Model):
    site_title = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_title


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.id)])

    def __str__(self):
        return self.name

# Model for units (e.g., tablet, capsule, etc.)


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# Model for the main product information


class Product(models.Model):
    TYPE_CHOICES = [
        ('RX', 'RX'),
        ('OTC', 'OTC'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    sub_description = models.TextField(blank=True, null=True)
    how_to_use = models.TextField(blank=True, null=True)
    side_effects = models.TextField(blank=True, null=True)
    drug_interactions = models.TextField(blank=True, null=True)
    precautions = models.TextField(blank=True, null=True)
    featured = models.BooleanField(default=False)
    sale = models.BooleanField(default=False)
    top_selling = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def lowest_potency(self):
        lowest_variant = self.variants.order_by('potency').first()
        return lowest_variant.potency if lowest_variant else None

    def highest_potency(self):
        highest_variant = self.variants.order_by('-potency').first()
        return highest_variant.potency if highest_variant else None

    def get_lowest_potency_price(self):
        lowest_variant = self.variants.order_by('potency').first()
        return lowest_variant.price_usd if lowest_variant else None

    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])

    def __str__(self):
        return self.name

# Model for product images


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')

    def __str__(self):
        return f"Image for {self.product.name}"

# Model for product labels (additional product attributes)


class ProductLabel(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='labels')
    label = models.CharField(max_length=255)
    value = models.TextField()

    def __str__(self):
        return f"{self.label}: {self.value}"

# Model for product variants, representing different potencies and prices


class CountryOfOrigin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    flag = models.ImageField(upload_to='flags/', blank=True, null=True)
    rx_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.flag.url if self.flag else 'No Flag'}"


class Variant(models.Model):
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='variants')
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE)
    potency = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_tablets = models.IntegerField(default=1)
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    original_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)  # New field to store original price
    country_of_origin = models.ForeignKey(
        'CountryOfOrigin', on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=255)
    shipping_note = models.CharField(max_length=255, null=True, blank=True)

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    def __str__(self):
        return f"{self.product.name} - {self.potency}{self.unit} - {self.country_of_origin}"

    def apply_discount(self):
        """Apply discount and save discounted price to database if not already applied."""
        today = timezone.now().date()
        discount = self.discounts.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()

        # Only apply discount if there's an active discount and original price is not set
        if discount and not self.original_price_usd:
            self.original_price_usd = self.price_usd  # Store the original price
            if discount.discount_type == 'percentage':
                discount_amount = self.price_usd * \
                    (discount.discount_value / 100)
            elif discount.discount_type == 'fixed':
                discount_amount = discount.discount_value

            self.price_usd = max(self.price_usd - discount_amount, 0)
            self.save(update_fields=['price_usd', 'original_price_usd'])

    def revert_price(self):
        """Revert to the original price if the discount has ended."""
        today = timezone.now().date()
        discount = self.discounts.filter(
            start_date__lte=today,
            end_date__lte=today
        ).first()

        if discount and self.original_price_usd:
            self.price_usd = self.original_price_usd
            self.original_price_usd = None  # Clear the original price
            self.save(update_fields=['price_usd', 'original_price_usd'])


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    variant = models.ForeignKey(
        Variant, on_delete=models.CASCADE, related_name='discounts')
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def is_active(self):
        """Check if the discount is active based on the current date."""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def delete(self, *args, **kwargs):
        # Perform additional cleanup if needed
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.variant} - {self.discount_type} - {self.discount_value}"


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='inventory')
    variant = models.ForeignKey(
        Variant, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.variant if self.variant else 'Default'}: {self.stock} units"


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(
        max_length=40, null=True, blank=True)
    discount_code = models.ForeignKey(
        DiscountCode, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def apply_discount(self):
        total_price = sum(item.total_price for item in self.items.all())
        if self.discount_code and self.discount_code.is_valid():
            total_price = self.discount_code.apply_discount(total_price)
        return self.discount_code.apply_special_discount(total_price)

    def __str__(self):
        return f"Cart ({self.user or self.session_key})"


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(
        max_digits=100, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        inventory = Inventory.objects.filter(variant=self.variant).first()
        if inventory and self.quantity > inventory.stock:
            raise ValidationError("Quantity exceeds available stock.")
        self.total_price = self.quantity * self.variant.price_usd
        super().save(*args, **kwargs)


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_1}, {self.city}"


class Shipping(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_1}, {self.city}"


class HealthInformation(models.Model):
    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    weight = models.IntegerField(null=True, blank=True, default=00)
    sex = models.CharField(
        max_length=10, choices=SEX_CHOICES, null=True, blank=True)
    breastfeeding = models.BooleanField(null=True, blank=True)
    smoker = models.BooleanField(null=True, blank=True)
    drug_allergies = models.BooleanField(null=True, blank=True)
    allergies_description = models.TextField(null=True, blank=True)
    supplements = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Health Information for {self.user.username}'


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100,
                            default='none'
                            )
    cost = models.DecimalField(max_digits=7, decimal_places=2)
    delivery_time = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name} (${self.cost})'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('returned', 'Returned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(
        Shipping, on_delete=models.CASCADE, default=1)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    billing_address = models.ForeignKey(
        Address, on_delete=models.CASCADE, related_name='billing_orders', default=1)
    is_canceled = models.BooleanField(default=False)
    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.SET_NULL, null=True, blank=True)
    health_info = models.ForeignKey(
        HealthInformation, on_delete=models.SET_NULL, null=True, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'Order {self.id} by {self.user.username}'

    def save(self, *args, **kwargs):
        """
        Override save to handle order status changes, especially cancellation and reversion.
        """
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                if self.status == 'canceled':
                    self.cancel_order_items()
                elif old_order.status == 'canceled':
                    self.revert_order_items()

        super().save(*args, **kwargs)

    def cancel_order(self):
        """
        Cancels the order and updates inventory and associated invoices.
        """
        if not self.is_canceled:
            self.status = 'canceled'
            self.is_canceled = True
            self.save()

    def cancel_order_items(self):
        """
        Cancel all related order items and restore inventory.
        """
        for item in self.orderitem_set.all():
            item.update_inventory_on_cancel()
            item.cancel_invoice()

    def revert_order_items(self):
        """
        Revert inventory when an order status is changed from canceled.
        """
        for item in self.orderitem_set.all():
            item.update_inventory_on_revert()

    def get_tracking_url(self):
        """Returns tracking URL for DHL based on tracking number."""
        if not self.tracking_number:
            return None  # If no tracking number or carrier is not DHL, return None

        # Construct the DHL tracking URL
        return f"https://www.dhl.com/en/express/tracking.html?AWB={self.tracking_number}"


class OrderItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, default=1)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Item {self.variant.product.name} ({self.quantity}) in Order {self.order.id}'

    def save(self, *args, **kwargs):
        """
        Override save to update inventory and create an invoice when an order item is added.
        """
        if self.pk is None:  # New OrderItem
            inventory = Inventory.objects.filter(variant=self.variant).first()
            if inventory:
                if self.quantity > inventory.stock:
                    raise ValidationError("Quantity exceeds available stock.")
                inventory.stock -= self.quantity
                inventory.save()

            super().save(*args, **kwargs)
            self.create_invoice()
        else:
            super().save(*args, **kwargs)

    def update_inventory_on_cancel(self):
        """
        Update inventory when an order item is canceled.
        """
        inventory = Inventory.objects.filter(variant=self.variant).first()
        if inventory:
            inventory.stock += self.quantity
            inventory.save()

    def update_inventory_on_revert(self):
        """
        Update inventory when an order status is reverted from canceled.
        """
        inventory = Inventory.objects.filter(variant=self.variant).first()
        if inventory:
            inventory.stock -= self.quantity
            inventory.save()

    def create_invoice(self):
        """
        Creates an invoice for the order item if one doesn't already exist.
        """
        if not Invoice.objects.filter(order=self.order).exists():
            invoice_number = f"INV-{self.order.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            Invoice.objects.create(
                order=self.order,
                user=self.user,
                invoice_number=invoice_number,
                amount_due=self.price * self.quantity
            )

    def cancel_invoice(self):
        """
        Cancels all invoices associated with this order item.
        """
        invoices = Invoice.objects.filter(order=self.order)
        for invoice in invoices:
            invoice.cancel_invoice()


class OrderAttachment(models.Model):
    order = models.ForeignKey(
        Order, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='order_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment {self.id} for Order {self.order.id}'

# Reorder Model


class Reorder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    original_order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='reorders')
    new_order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='reordered_from')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Reorder of Order {self.original_order.id} by {self.original_order.user.username}'


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Order {self.order.id} by {self.user.username}"


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=255)
    deparment = models.CharField(max_length=20, default='')
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='New')
    attachments = models.FileField(
        upload_to='tickets/attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject
# Model to track agent availability


class TicketAgent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_agent = models.BooleanField(default=True)  # Ensure this is an agent

    def __str__(self):
        return f"Agent: {self.user.username}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name='replies', on_delete=models.CASCADE)
    agent = models.ForeignKey(TicketAgent, null=True, blank=True,
                              on_delete=models.SET_NULL)  # Use TicketAgent for agents
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.ticket.subject}"


class Agent(models.Model):
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)  # Store hashed password
    name = models.CharField(max_length=20, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_online(self):
        self.is_online = True
        self.save()

    def set_offline(self):
        self.is_online = False
        self.save()

    def save(self, *args, **kwargs):
        # If an Agent is being created or updated, create or update the corresponding User
        if self.username and self.password:
            # Check if a User already exists for this Agent
            user, created = User.objects.get_or_create(username=self.username)

            # If the user was just created, set the password and other details
            if created:
                # Hashes the password and sets it
                user.set_password(self.password)
            else:
                # Update the password if it has changed
                if not check_password(self.password, user.password):
                    user.set_password(self.password)

            # Update other user fields
            user.first_name = self.name or ''  # Optional: set first name
            user.save()

        super().save(*args, **kwargs)  # Call the parent class save method

    def __str__(self):
        return self.username


class ChatRequest(models.Model):
    user = models.ForeignKey(
        User, related_name='chat_requests', on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(
        Agent, related_name='chat_requests', on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=20, null=True, blank=True)
    guest_phone = models.IntegerField(null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Chat request from {self.user} to agent {self.agent}"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatRequest, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.message[:50]} to {self.sender}"


class ProblemRequest(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, default=1, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    problem_description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Problem Request from {self.name} ({self.email})"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('canceled', 'Canceled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Link to Order
    invoice_number = models.CharField(
        max_length=100, unique=True)  # Unique invoice number
    amount_due = models.DecimalField(
        max_digits=10, decimal_places=2)  # Total amount of the invoice
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')  # Invoice status
    # Date when the invoice is created
    issued_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(null=True, blank=True)  # Optional due date
    payment_date = models.DateTimeField(
        null=True, blank=True)  # When the invoice is paid

    class Meta:
        ordering = ['-issued_date']  # Sort by latest issued date
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f'Invoice {self.invoice_number} for Order {self.order.id}'

    def mark_as_paid(self):
        """
        Marks the invoice as paid and sets the payment date.
        """
        self.status = 'paid'
        self.payment_date = timezone.now()
        self.save()

    def cancel_invoice(self):
        """
        Cancels the invoice.
        """
        self.status = 'canceled'
        self.save()
