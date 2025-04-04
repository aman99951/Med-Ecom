
from .models import *
from django.utils.timezone import localtime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import AnonymousUser
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import *
from rest_framework import viewsets
from django.core.paginator import Paginator
from itertools import groupby
from operator import attrgetter
from django.db import IntegrityError, transaction
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils import timezone
from .models import Invoice, Order
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ticket, TicketReply, ShippingMethod, HealthInformation
from django.views import View
from django.contrib.auth.decorators import user_passes_test
import json
from .models import ChatMessage, ProblemRequest
from .models import Agent, ChatRequest
from .models import Ticket
from .forms import TicketForm
from .models import Order, Review
from .forms import ReviewForm, TicketReplyForm

from pytz import timezone as pytz_timezone
from django.utils.dateparse import parse_datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F, Q
from .models import Order, OrderItem, Reorder, OrderAttachment
from decimal import Decimal
from django.contrib.auth import update_session_auth_hash
import logging
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .models import Address
from .forms import AddressForm,  GuestRegisterForm, CustomPasswordChangeForm, ShippingForm
from django.contrib.auth import authenticate, login as auth_login
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from .models import Cart, CartItem, Variant, Inventory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import SiteSetting, Shipping
from .decorators import my_login_required, agent_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Variant, Cart, CartItem, Profile, DiscountCode, Order
from django.contrib import messages
from django.contrib.auth import login


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
        # Add classes to form fields
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['email'].widget.attrs.update({'class': 'form-control'})
        form.fields['mobile'].widget.attrs.update({'class': 'form-control'})
        form.fields['password1'].widget.attrs.update({'class': 'form-control'})
        form.fields['password2'].widget.attrs.update({'class': 'form-control'})

    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Merge session cart with user's cart before logging in
            merge_carts(request, user)

            # Log the user in
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
        form.fields['username'].label = "Email"  # Rename the label
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({'class': 'form-control'})

    return render(request, 'store/login.html', {'form': form})


def merge_carts(request, user):
    session_key = request.session.session_key
    if not session_key:
        return  # No session cart to merge

    # Fetch the cart associated with the session key
    session_cart = Cart.objects.filter(
        session_key=session_key, user=None).first()
    if session_cart:
        # Fetch or create the user's cart
        user_cart, created = Cart.objects.get_or_create(user=user)

        # Move items from session cart to user cart
        for item in session_cart.items.all():
            user_cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart, variant=item.variant)
            if not created:
                user_cart_item.quantity += item.quantity
            user_cart_item.total_price = user_cart_item.quantity * \
                user_cart_item.variant.price_usd
            user_cart_item.save()

        # Delete the session cart after merging
        session_cart.delete()


@my_login_required
def logout(request):
    auth_logout(request)
    return redirect('login')


def home(request):
    today = timezone.now().date()

    # Fetch featured products
    featured_products = Product.objects.filter(is_active=True, featured=True)

    # Fetch sale products with active discounts
    sale_products = Product.objects.filter(is_active=True, sale=True)

    top_selling_products = Product.objects.filter(
        is_active=True, top_selling=True)

    # Apply discounts and revert prices where necessary
    for variant in Variant.objects.all():
        if variant.discounts.filter(start_date__lte=today, end_date__gte=today).exists():
            variant.apply_discount()
        elif variant.discounts.filter(end_date__lt=today).exists():
            variant.revert_price()

    # Optionally, prefetch related images and labels for efficiency
    featured_products = featured_products.prefetch_related('images', 'labels')
    sale_products = sale_products.prefetch_related('images', 'labels')
    top_selling_products = top_selling_products.prefetch_related(
        'images', 'labels')

    context = {
        'featured_products': featured_products,
        'sale_products': sale_products,
        'top_selling_products': top_selling_products,
    }
    return render(request, 'store/home.html', context)


def basehome(request):
    # Ensure there is at least one SiteSetting object
    site_settings, created = SiteSetting.objects.get_or_create(
        defaults={'site_title': 'Medicine E-commerce Website'}
    )
    return render(request, 'base.html', {'site_settings': site_settings})


def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)

    # Group variants by country_of_origin and manufacturer
    grouped_variants = {}
    for country, country_group in groupby(
        sorted(product.variants.all(), key=lambda v: (
            v.country_of_origin.name, v.manufacturer)),
        key=attrgetter('country_of_origin')
    ):
        grouped_variants[country] = {}
        for manufacturer, manufacturer_group in groupby(country_group, key=attrgetter('manufacturer')):
            grouped_variants[country][manufacturer] = list(manufacturer_group)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'grouped_variants': grouped_variants,
    })


logger = logging.getLogger(__name__)


def cart_view(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        logger.debug(f"Authenticated user cart: {cart.id}")

        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(
                session_key=session_key, user=None).first()
            if session_cart:
                for item in session_cart.items.all():
                    existing_item = CartItem.objects.filter(
                        cart=cart, variant=item.variant).first()
                    if existing_item:
                        existing_item.quantity += item.quantity
                        existing_item.total_price = existing_item.quantity * existing_item.variant.price_usd
                        existing_item.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(
            session_key=session_key, user=None)
        logger.debug(f"Anonymous user cart: {cart.id}")

    cart_items = cart.items.all()
    total_price = sum(item.total_price for item in cart_items)

    # Round the total price
    total_price = round(total_price, 2)
    error_message = None
    discount_message = None
    inventory_error_message = None

    if request.method == 'POST':
        if 'remove_item' in request.POST:
            item_id = request.POST.get('remove_item')
            CartItem.objects.filter(id=item_id).delete()
            return redirect('cart')

        if 'apply_discount' in request.POST:
            discount_code = request.POST.get('discount_code')
            try:
                discount = DiscountCode.objects.get(code=discount_code)
                if discount.is_valid():
                    discounted_total = discount.apply_discount(total_price)
                    cart.discount_code = discount
                    cart.save()
                    total_price = discounted_total
                    discount_message = f"Discount Applied: {discount.discount_percentage}%"
                else:
                    error_message = "Invalid or expired discount code."
            except DiscountCode.DoesNotExist:
                error_message = "Discount code does not exist."

        if 'remove_discount' in request.POST:
            cart.discount_code = None
            cart.save()
            discount_message = "Discount removed."
            # Revert to original price
            total_price = sum(item.total_price for item in cart_items)

        for item in cart_items:
            quantity = request.POST.get(f'quantity_{item.id}')
            if quantity:
                quantity = int(quantity)
                inventory = Inventory.objects.filter(
                    variant=item.variant).first()

                if inventory and quantity > inventory.stock:
                    inventory_error_message = (
                        f"Quantity exceeds available stock for the product {item.variant.product.name} "
                        f"with tablets {item.variant.number_of_tablets} and potency {item.variant.potency} "
                        f"{item.variant.unit.name}. Only {inventory.stock} units are available."
                    )
                    break

                item.quantity = quantity
                item.total_price = quantity * item.variant.price_usd
                try:
                    item.save()
                except ValidationError as e:
                    error_message = str(e)
                    break

        if error_message or inventory_error_message:
            return render(request, 'store/cart.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'error_message': error_message,
                'inventory_error_message': inventory_error_message,
                'discount_message': discount_message
            })

        return redirect('cart')

    # Apply discount if available
    discounted_total = total_price
    if cart.discount_code:
        try:
            discounted_total = cart.discount_code.apply_discount(total_price)
        except ValidationError as e:
            error_message = str(e)

    discounted_total = round(discounted_total, 2)  # Round the discounted total

    return render(request, 'store/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': discounted_total,
        'error_message': error_message,
        'inventory_error_message': inventory_error_message,
        'discount_message': discount_message
    })


def add_to_cart(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id)

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(
                session_key=session_key, user=None).first()
            if session_cart:
                for item in session_cart.items.all():
                    existing_item = CartItem.objects.filter(
                        cart=cart, variant=item.variant).first()
                    if existing_item:
                        existing_item.quantity += item.quantity
                        existing_item.total_price = existing_item.quantity * existing_item.variant.price_usd
                        existing_item.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(
            session_key=session_key, user=None)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, variant=variant)
    if not created:
        cart_item.quantity += 1
    cart_item.total_price = cart_item.quantity * variant.price_usd
    cart_item.save()

    return redirect('cart')


@my_login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        # Initialize instances
        address_instance = Address.objects.filter(user=user).first()
        shipping_instance = Shipping.objects.filter(user=user).first()

        # Initialize forms
        address_form = AddressForm(
            request.POST if 'save_address' in request.POST else None, instance=address_instance)
        shipping_form = ShippingForm(
            request.POST if 'save_shipping' in request.POST else None, instance=shipping_instance)
        password_form = CustomPasswordChangeForm(
            user=user, data=request.POST if 'change_password' in request.POST else None)

        # Check which form is submitted
        if 'save_address' in request.POST and address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = user
            address.save()
            messages.success(
                request, 'Your billing address has been successfully updated.')
            return redirect('profile')

        if 'save_shipping' in request.POST and shipping_form.is_valid():
            shipping = shipping_form.save(commit=False)
            shipping.user = user
            shipping.save()
            messages.success(
                request, 'Your shipping address has been successfully updated.')
            return redirect('profile')

        if 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Your password has been successfully changed.')
            return redirect('profile')

    else:
        # Initialize forms with current instances
        address_instance = Address.objects.filter(user=user).first()
        shipping_instance = Shipping.objects.filter(user=user).first()
        address_form = AddressForm(instance=address_instance)
        shipping_form = ShippingForm(instance=shipping_instance)
        password_form = CustomPasswordChangeForm(user=user)

    return render(request, 'store/profile.html', {
        'address_form': address_form,
        'shipping_form': shipping_form,
        'password_form': password_form,
    })


@my_login_required
def delete_account(request):
    user = request.user
    user.delete()
    messages.success(request, "Your account has been successfully deleted.")
    return redirect('home')  # Redirect to home or login page after deletion


def guest_checkout(request):
    if request.method == 'POST':
        register_form = GuestRegisterForm(request.POST)
        address_form = AddressForm(request.POST)
        shipping_form = ShippingForm(request.POST)  # Add this line

        if register_form.is_valid() and address_form.is_valid() and shipping_form.is_valid():  # Add shipping_form validation
            email = register_form.cleaned_data['email']

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                error_message = "An account with this email already exists."
                return render(request, 'store/guest_checkout.html', {
                    'register_form': register_form,
                    'address_form': address_form,
                    'shipping_form': shipping_form,  # Pass the shipping form to the template
                    'error_message': error_message,
                })

            # Create the user
            user = register_form.save(commit=False)
            password = get_random_string(length=12)
            user.set_password(password)
            user.username = email
            user.save()

            # Create Profile, Address, and Shipping
            Profile.objects.create(
                user=user, mobile=register_form.cleaned_data['mobile'])
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            shipping = shipping_form.save(commit=False)  # Handle shipping data
            shipping.user = user
            shipping.save()

            # Automatically log in the user
            login(request, user)

            # Send email
            try:
                send_mail(
                    'Your Account Details',
                    f'Your account has been created.\n\nUsername: {email}\nPassword: {password}',
                    'your_email@example.com',
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"An error occurred while sending the email: {e}")

            return redirect('home')
        else:
            # Print errors for debugging
            print("Form validation failed.")
            print("Register form errors:", register_form.errors)
            print("Address form errors:", address_form.errors)
            print("Shipping form errors:", shipping_form.errors)  # Add this line
    else:
        register_form = GuestRegisterForm()
        address_form = AddressForm()
        shipping_form = ShippingForm()  # Add this line

    context = {
        'register_form': register_form,
        'address_form': address_form,
        'shipping_form': shipping_form,  # Add this line
    }

    return render(request, 'store/guest_checkout.html', context)


@my_login_required
def order_success(request):
    return render(request, 'store/order_success.html')


@my_login_required
def order_confirmation(request, order_id):
    # Fetch the order tied to the current user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    attachments = OrderAttachment.objects.filter(order=order)

    # Fetch health information for the user if it exists
    health_info = HealthInformation.objects.filter(user=request.user).first()

    # Fetch shipping method for the order if it exists
    shipping_method = ShippingMethod.objects.filter(
        id=order.shipping_method_id).first()

    # Handle review submission
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Update or create a review associated with the order and user
            review, created = Review.objects.update_or_create(
                order=order,
                user=request.user,  # Link to the user
                defaults={'comment': form.cleaned_data['comment']}
            )
            # Provide feedback and redirect to avoid form re-submission
            messages.success(request, 'Your review has been submitted.')
            return redirect('order_detail', order_id=order_id)
        else:
            messages.error(request, 'There was an error with your review.')
    else:
        # Check if the user already has a review for this order
        existing_review = Review.objects.filter(
            order=order, user=request.user).first()
        form = ReviewForm(instance=existing_review)

    # Fetch all reviews for this order
    reviews = Review.objects.filter(order=order)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items,
        'form': form,
        'reviews': reviews,
        'attachments': attachments,
        'health_info': health_info,
        'shipping_method': shipping_method,
    }

    return render(request, 'store/order_confirmation.html', context)


@my_login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in ['canceled', 'returned']:
        order.cancel_order()
        messages.success(request, "Order canceled and inventory updated.")
    else:
        messages.warning(
            request, "This order has already been canceled or returned.")

    return redirect('order_list')


@my_login_required
def order_list(request):
    user = request.user
    # Fetch orders for the logged-in user, ordered by creation date or ID in descending order
    orders = Order.objects.filter(user=user).order_by('-created_at')

    # Prefetch related product and variant information for efficiency
    orders = orders.prefetch_related('order_items__variant__product')

    # Convert 'created_at' to IST
    ist_timezone = pytz_timezone('Asia/Kolkata')
    for order in orders:
        if order.created_at:
            order.created_at_ist = order.created_at.astimezone(ist_timezone)
        else:
            order.created_at_ist = None

    return render(request, 'store/order_list.html', {'orders': orders})


@my_login_required
def reorder(request, order_id):
    original_order = get_object_or_404(Order, id=order_id, user=request.user)

    new_order = Order.objects.create(
        user=original_order.user,
        shipping_address=original_order.shipping_address,
        total_cost=original_order.total_cost,
        payment_method=original_order.payment_method,
        status='pending',
    )

    for item in original_order.orderitem_set.all():
        OrderItem.objects.create(
            user=request.user,
            order=new_order,
            variant=item.variant,
            quantity=item.quantity,
            price=item.price,
        )

    Reorder.objects.create(
        user=request.user, original_order=original_order, new_order=new_order)

    return redirect('order_detail', order_id=new_order.id)


def search_suggestions(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # Search for active products matching the query in name or brand_name
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand_name__icontains=query), is_active=True
        )

        # Fetch variants for each matching product
        for product in products:
            seen_potencies = set()  # Set to keep track of unique potencies per product
            variants = product.variants.all()  # Get all variants related to the product

            for variant in variants:
                # Convert potency to a float and check if it's a whole number
                potency_value = float(variant.potency)
                formatted_potency = int(
                    potency_value) if potency_value.is_integer() else potency_value
                potency_key = f"{formatted_potency} {variant.unit.name}"

                # Only add the variant if this potency has not been seen before for this product
                if potency_key not in seen_potencies:
                    seen_potencies.add(potency_key)
                    # Display brand name only if it exists
                    brand_display = f" ({product.brand_name})" if product.brand_name else ''
                    results.append({
                        'name': f"{product.name}{brand_display} {formatted_potency} {variant.unit.name}",
                        'url': variant.get_absolute_url()
                    })

    return JsonResponse(results, safe=False)


@staff_member_required
def sales_report(request):
    products = Product.objects.all()

    # Get search query parameters
    search_query = request.GET.get('q', '')
    category_query = request.GET.get('category', '')
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    # Validate and parse dates
    date_from = parse_datetime(date_from_str) if date_from_str else None
    date_to = parse_datetime(date_to_str) if date_to_str else None

    print(f"Date From: {date_from}, Date To: {date_to}")

    # Filter products based on search query
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category_query:
        products = products.filter(category__name=category_query)

    # Filter order items based on date range
    if date_from and date_to:
        order_items = OrderItem.objects.filter(
            order__created_at__range=[date_from, date_to]
        )
    else:
        order_items = OrderItem.objects.all()

    print(order_items)  # Check if order_items are fetched correctly

    # Aggregate report data
    report_data = []
    for product in products:
        variants = Variant.objects.filter(product=product)
        for variant in variants:
            total_sales = order_items.filter(variant=variant).aggregate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('price'))
            )

            report_data.append({
                'product': product.name,
                'variant': variant,
                'total_quantity': total_sales['total_quantity'] or 0,
                'total_revenue': total_sales['total_revenue'] or 0.00,
            })

    context = {
        'report_data': report_data,
        'search_query': search_query,
        'category_query': category_query,
        'date_from': date_from_str,
        'date_to': date_to_str,
    }
    return render(request, 'admin/sales_report.html', context)


def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user  # Set user only if authenticated
            ticket.save()
            return redirect('ticket_list')
    else:
        form = TicketForm()
    return render(request, 'helpdesk/create_ticket.html', {'form': form})


@my_login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(
        user=request.user).prefetch_related('replies')
    return render(request, 'helpdesk/ticket_list.html', {'tickets': tickets})


@my_login_required
def ticket_detail(request, pk):
    # Ensure that the user can only access their own tickets
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)

    # Fetch only the latest reply
    latest_reply = ticket.replies.order_by('-created_at').first()

    if request.method == 'POST':
        if ticket.status != 'Closed':  # Check if the ticket is not closed
            form = TicketReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.ticket = ticket
                reply.user = request.user  # Associate the reply with the current user
                reply.save()
                return redirect('ticket_detail', pk=ticket.pk)
        else:
            # Handle the case where the ticket is closed
            form = TicketReplyForm()  # Recreate the form to prevent POST submission
            context = {
                'ticket': ticket,
                'latest_reply': latest_reply,
                'form': form,
                'error': 'This ticket is closed and cannot accept new messages.',
            }
            return render(request, 'helpdesk/ticket_detail.html', context)
    else:
        form = TicketReplyForm()

    context = {
        'ticket': ticket,
        'latest_reply': latest_reply,  # Pass only the latest reply
        'form': form,
    }
    return render(request, 'helpdesk/ticket_detail.html', context)


def user_chat_request_view(request):
    online_agents = Agent.objects.filter(is_online=True)

    if request.method == 'POST':
        if online_agents.exists():
            agent = online_agents.first()
            user = request.user if request.user.is_authenticated else None

            # Get guest information if the user is not authenticated
            guest_name = request.POST.get('name') if not user else None
            guest_email = request.POST.get('email') if not user else None
            guest_phone = request.POST.get('phone') if not user else None

            if agent:
                try:
                    with transaction.atomic():
                        # Create a chat request
                        chat_request = ChatRequest.objects.create(
                            user=user,
                            guest_name=guest_name,
                            guest_email=guest_email,
                            guest_phone=guest_phone,
                            agent=agent
                        )
                    return redirect('user_chat_session', chat_request_id=chat_request.id)
                except IntegrityError as e:
                    print(f"Error creating chat request: {e}")
                    messages.error(
                        request, "There was an error creating your chat request. Please try again later.")
                    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})
            else:
                messages.error(
                    request, "No available agent to handle your request.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

        else:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            problem_description = request.POST.get('problem_description')

            try:
                ProblemRequest.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    name=name,
                    email=email,
                    phone=phone,
                    problem_description=problem_description
                )
                return render(request, 'chat/thank_you.html')
            except IntegrityError as e:
                print(f"Error creating problem request: {e}")
                messages.error(
                    request, "There was an error submitting your problem. Please try again later.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})


def user_chat_session_view(request, chat_request_id):
    # Fetch the chat request object, no longer filter by user
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)

    # Process message sending if the form is submitted
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Set sender to the authenticated user or None if not authenticated
            sender = request.user if request.user.is_authenticated else None

            # Create the chat message with the sender as None if user is not authenticated
            ChatMessage.objects.create(
                session=chat_request,
                sender=sender,
                message=message_text
            )
            return redirect('user_chat_session', chat_request_id=chat_request.id)

    # Get all messages in this chat session
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')

    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        'agent': chat_request.agent.username,  # Use agent's username directly
        'user': chat_request.user  # Pass the user to the template if needed
    })


def agent_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate against the User model
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user is an agent
            try:
                agent = Agent.objects.get(username=username)
                # Log the agent in
                # Use the login function to set the user session
                login(request, user)
                request.session['agent_username'] = agent.username
                agent.set_online()  # Set the agent online
                # Redirect to agent chat requests
                return redirect('agent_chat_requests')
            except Agent.DoesNotExist:
                messages.error(request, "You are not authorized to log in.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin/agent_login.html')


@agent_required
def agent_logout_view(request):
    # Get the current agent from the request
    agent = Agent.objects.filter(username=request.user.username).first()

    # Check if the agent exists
    if agent:
        agent.set_offline()

    # Log out the agent
    logout(request)
    return redirect('agent_login')


@agent_required
def agent_chat_requests_view(request):
    # Get the agent associated with the logged-in session
    agent_username = request.session.get('agent_username')
    agent = get_object_or_404(Agent, username=agent_username)

    # Fetch chat requests for this agent that have not been accepted, ordered by timestamp (most recent first)
    chat_requests = ChatRequest.objects.filter(
        agent=agent, accepted=False).order_by('-timestamp')

    # Handle the acceptance of a chat request
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        chat_request = get_object_or_404(
            ChatRequest, id=request_id, agent=agent)
        chat_request.accepted = True
        chat_request.save()
        return redirect('agent_chat_session', chat_request_id=chat_request.id)

    return render(request, 'chat/agent_chat_requests.html', {'chat_requests': chat_requests})


@agent_required
def agent_chat_session_view(request, chat_request_id):
    # Fetch the chat request, ensuring it belongs to the logged-in agent
    chat_request = get_object_or_404(
        ChatRequest, id=chat_request_id, agent__username=request.user.username)

    # Ensure the chat request is accepted
    if not chat_request.accepted:
        return redirect('agent_chat_requests')

    # Handle message sending
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Create a new chat message
            ChatMessage.objects.create(
                session=chat_request,
                sender=request.user,  # Assuming the agent is using the same User model
                message=message_text
            )
            return redirect('agent_chat_session', chat_request_id=chat_request.id)

    # Retrieve all messages for the chat session
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')

    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        # Pass the agent's username for display
        'agent_username': request.user.username
    })


@agent_required
def agent_toggle_status(request):
    agent = get_object_or_404(Agent, username=request.user.username)
    agent.is_online = not agent.is_online
    agent.save()
    return redirect('agent_chat_requests')


@method_decorator(login_required, name='dispatch')
class TicketChatView(View):
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        replies = TicketReply.objects.filter(
            ticket=ticket).order_by('created_at')
        form = TicketReplyForm()

        context = {
            'ticket': ticket,
            'replies': replies,
            'form': form,
        }
        return render(request, 'admin/ticket_chat.html', context)

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            new_reply = form.save(commit=False)
            new_reply.ticket = ticket
            new_reply.user = request.user  # Ensure user is assigned
            new_reply.save()
            return redirect('ticket-chat', ticket_id=ticket.id)
        else:
            replies = TicketReply.objects.filter(
                ticket=ticket).order_by('created_at')
            context = {
                'ticket': ticket,
                'replies': replies,
                'form': form,
            }
            return render(request, 'admin/ticket_chat.html', context)


@my_login_required
def checkout(request):
    user = request.user
    cart = Cart.objects.filter(user=user).first()

    if not cart or not cart.items.exists():
        return redirect('cart')  # Redirect to cart page if the cart is empty

    # Calculate the total cost before discount
    total_cost = sum(item.total_price for item in cart.items.all())

    # Initialize discount details
    discount_message = None
    total_cost_with_discount = total_cost

    discount_code = cart.discount_code
    if discount_code:
        discount_decimal = Decimal(
            discount_code.discount_percentage) / Decimal(100)
        discount_amount = total_cost * discount_decimal
        total_cost_with_discount = total_cost - discount_amount
        discount_message = f"Discount Applied: {discount_code.discount_percentage}% (-${discount_amount:.2f})"

        if discount_code.discount_type == 'price':
            discount_amount = Decimal(discount_code.discount_price)
            total_cost_with_discount = total_cost - discount_amount
            discount_message = f"Discount Applied: ${discount_code.discount_price}"

    # Apply the special discount if the total cost exceeds $5000
    if total_cost_with_discount > Decimal('5000.00'):
        special_discount = Decimal('40') / Decimal('100')
        special_discount_amount = total_cost_with_discount * special_discount
        total_cost_with_discount -= special_discount_amount
        if not discount_message:
            discount_message = f"Special Discount Applied: 40% (-${special_discount_amount:.2f})"
        else:
            discount_message += f" | Special Discount Applied: 40% (-${special_discount_amount:.2f})"

    # Round the total cost to two decimal places
    total_cost_with_discount = round(total_cost_with_discount, 2)

    if request.method == 'POST':
        if 'update_shipping' in request.POST:
            shipping_method_id = request.POST.get('shipping_method')
            if not shipping_method_id:
                return render(request, 'store/checkout.html', {
                    'error_message': 'Shipping method not selected.',
                    'cart': cart,
                    'shipping_addresses': Shipping.objects.filter(user=user),
                    'billing_addresses': Address.objects.filter(user=user),
                    'shipping_methods': ShippingMethod.objects.all(),
                    'total_cost': total_cost,
                    'total_cost_with_discount': total_cost_with_discount,
                    'discount_message': discount_message,
                    'discount_code': discount_code,
                    'shipping_cost': Decimal('0.00'),
                    'total_cost_with_shipping': total_cost_with_discount,
                })

            try:
                shipping_method = ShippingMethod.objects.get(
                    id=shipping_method_id)
            except ShippingMethod.DoesNotExist:
                return render(request, 'store/checkout.html', {
                    'error_message': f"Shipping method with ID {shipping_method_id} not found.",
                    'cart': cart,
                    'shipping_addresses': Shipping.objects.filter(user=user),
                    'billing_addresses': Address.objects.filter(user=user),
                    'shipping_methods': ShippingMethod.objects.all(),
                    'total_cost': total_cost,
                    'total_cost_with_discount': total_cost_with_discount,
                    'discount_message': discount_message,
                    'discount_code': discount_code,
                    'shipping_cost': Decimal('0.00'),
                    'total_cost_with_shipping': total_cost_with_discount,
                })

            shipping_cost = shipping_method.cost
            total_cost_with_shipping = total_cost_with_discount + shipping_cost

            return render(request, 'store/checkout.html', {
                'cart': cart,
                'shipping_addresses': Shipping.objects.filter(user=user),
                'billing_addresses': Address.objects.filter(user=user),
                'shipping_methods': ShippingMethod.objects.all(),
                'total_cost': total_cost,
                'total_cost_with_discount': total_cost_with_discount,
                'discount_message': discount_message,
                'discount_code': discount_code,
                'shipping_cost': shipping_cost,
                'total_cost_with_shipping': total_cost_with_shipping,
                'selected_shipping_method_id': shipping_method_id,
            })

        else:
            # Handle order placement
            shipping_address_id = request.POST.get('shipping_address')
            billing_address_id = request.POST.get('billing_address')
            shipping_method_id = request.POST.get('shipping_method')

            if not shipping_address_id or not billing_address_id or not shipping_method_id:
                return render(request, 'store/checkout.html', {
                    'error_message': 'All fields are required to place an order.',
                    'cart': cart,
                    'shipping_addresses': Shipping.objects.filter(user=user),
                    'billing_addresses': Address.objects.filter(user=user),
                    'shipping_methods': ShippingMethod.objects.all(),
                    'total_cost': total_cost,
                    'total_cost_with_discount': total_cost_with_discount,
                    'discount_message': discount_message,
                    'discount_code': discount_code,
                    'shipping_cost': Decimal('0.00'),
                    'total_cost_with_shipping': total_cost_with_discount,
                })

            try:
                shipping_address = Shipping.objects.get(
                    id=shipping_address_id, user=user)
                billing_address = Address.objects.get(
                    id=billing_address_id, user=user)
                shipping_method = ShippingMethod.objects.get(
                    id=shipping_method_id)
            except (Shipping.DoesNotExist, Address.DoesNotExist, ShippingMethod.DoesNotExist):
                return render(request, 'store/checkout.html', {
                    'error_message': 'Invalid address or shipping method selected.',
                    'cart': cart,
                    'shipping_addresses': Shipping.objects.filter(user=user),
                    'billing_addresses': Address.objects.filter(user=user),
                    'shipping_methods': ShippingMethod.objects.all(),
                    'total_cost': total_cost,
                    'total_cost_with_discount': total_cost_with_discount,
                    'discount_message': discount_message,
                    'discount_code': discount_code,
                    'shipping_cost': Decimal('0.00'),
                    'total_cost_with_shipping': total_cost_with_discount,
                })

            # Calculate the total cost with shipping
            shipping_cost = shipping_method.cost
            total_cost_with_shipping = total_cost_with_discount + shipping_cost

            # Create order
            order = Order.objects.create(
                user=user,
                total_cost=total_cost_with_shipping,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_method='Cash on Delivery',
                status='Pending',
                shipping_method=shipping_method,

            )

            # Create order items for each cart item
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    user=user,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price_usd,

                )

            # Handle file attachments
            for file in request.FILES.getlist('attachments'):
                OrderAttachment.objects.create(order=order, file=file)

            # Clear the cart after successful checkout
            cart.items.all().delete()
            cart.discount_code = None
            cart.save()

            # Redirect to a success page
            return redirect('order_success')

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'shipping_addresses': Shipping.objects.filter(user=user),
        'billing_addresses': Address.objects.filter(user=user),
        'shipping_methods': ShippingMethod.objects.all(),
        'total_cost': total_cost,
        'total_cost_with_discount': total_cost_with_discount,
        'discount_message': discount_message,
        'discount_code': discount_code,
        'shipping_cost': Decimal('0.00'),
        'total_cost_with_shipping': total_cost_with_discount,
    })


@my_login_required
def invoice_list(request):
    user = request.user
    invoices = Invoice.objects.filter(user=user)
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})


@my_login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@my_login_required
def create_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not Invoice.objects.filter(order=order).exists():
        order.create_invoice()
    return redirect('invoice_detail', invoice_id=order.invoice_set.first().id)


@my_login_required
def mark_invoice_as_paid(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    invoice.mark_as_paid()
    return redirect('invoice_detail', invoice_id=invoice.id)


@my_login_required
def cancel_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    invoice.cancel_invoice()
    return redirect('invoice_detail', invoice_id=invoice.id)


def about_us(request):
    return render(request, 'store/about_us.html')


def contact_us(request):
    return render(request, 'store/contact_us.html')


def faq(request):
    return render(request, 'store/faq.html')


@staff_member_required
def order_label_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    invoice = Invoice.objects.filter(order=order, status='paid').first()

    if not invoice:
        return render(request, "store/order_label.html", {"error": "Invoice is not paid yet."})

    order_items = order.order_items.all()

    # Pagination: Show 2 items per page
    paginator = Paginator(order_items, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "store/order_label.html", {"order": order, "page_obj": page_obj})


@staff_member_required
def order_label_list_view(request):
    """
    Displays a list of all orders with paid invoices.
    """
    paid_orders = Order.objects.filter(invoice__status='paid').distinct()

    return render(request, "store/order_label_list.html", {"orders": paid_orders})


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartCreateView(generics.CreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartDetailView(generics.RetrieveAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class AddCartItemView(APIView):
    def post(self, request, cart_id):
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            # Ensure item is linked to the correct cart
            serializer.save(cart=cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'User registered successfully!', 'user_id': user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    def post(self, request):
        username = request.data.get('username')  # Email
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'message': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)  # ✅ Login sets session
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid username or password'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def signout(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"message": "Logged out successfully"})
    return JsonResponse({"error": "Invalid request"}, status=400)


class CheckLoginView(APIView):
    def get(self, request):
        user = request.user
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            return Response({"logged_in": True, "username": user.username}, status=status.HTTP_200_OK)
        else:
            return Response({"logged_in": False}, status=status.HTTP_200_OK)


@my_login_required
def profile_api(request):
    user = request.user

    if request.method == 'GET':
        address_instance = Address.objects.filter(user=user).first()
        shipping_instance = Shipping.objects.filter(user=user).first()

        response_data = {
            "username": user.username,
            # Handle missing profile gracefully
            "mobile": user.profile.mobile if hasattr(user, 'profile') else "",
            "address": {
                "address_1": address_instance.address_1 if address_instance else "",
                "address_2": address_instance.address_2 if address_instance else "",
                "city": address_instance.city if address_instance else "",
                "state": address_instance.state if address_instance else "",
                "postal_code": address_instance.postal_code if address_instance else "",
                "country": address_instance.country if address_instance else "",
            },
            "shipping": {
                "address_1": shipping_instance.address_1 if shipping_instance else "",
                "address_2": shipping_instance.address_2 if shipping_instance else "",
                "city": shipping_instance.city if shipping_instance else "",
                "state": shipping_instance.state if shipping_instance else "",
                "postal_code": shipping_instance.postal_code if shipping_instance else "",
                "country": shipping_instance.country if shipping_instance else "",
            },
        }

        return JsonResponse(response_data)


@my_login_required
@csrf_exempt
def update_profile_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user

            # Address update
            address_instance, _ = Address.objects.get_or_create(user=user)
            address_instance.address_1 = data.get(
                'address', {}).get('address_1', '')
            address_instance.address_2 = data.get(
                'address', {}).get('address_2', '')
            address_instance.city = data.get('address', {}).get('city', '')
            address_instance.state = data.get('address', {}).get('state', '')
            address_instance.postal_code = data.get(
                'address', {}).get('postal_code', '')
            address_instance.country = data.get(
                'address', {}).get('country', '')
            address_instance.save()

            # Shipping update
            shipping_instance, _ = Shipping.objects.get_or_create(user=user)
            shipping_instance.address_1 = data.get(
                'shipping', {}).get('address_1', '')
            shipping_instance.address_2 = data.get(
                'shipping', {}).get('address_2', '')
            shipping_instance.city = data.get('shipping', {}).get('city', '')
            shipping_instance.state = data.get('shipping', {}).get('state', '')
            shipping_instance.postal_code = data.get(
                'shipping', {}).get('postal_code', '')
            shipping_instance.country = data.get(
                'shipping', {}).get('country', '')
            shipping_instance.save()

            return JsonResponse({'message': 'Profile updated successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@method_decorator(csrf_exempt, name='dispatch')
class AddToCartView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            variant_id = data.get("variant_id")
            quantity = data.get("quantity", 1)  # Default to 1 if not provided

            if not variant_id:
                return JsonResponse({"error": "Variant ID is required"}, status=400)

            variant = get_object_or_404(Variant, id=variant_id)

            if request.user.is_authenticated:
                # Get or create a cart for the authenticated user
                cart, created = Cart.objects.get_or_create(user=request.user)

                # Merge session cart into authenticated cart if exists
                session_key = request.session.session_key
                if session_key:
                    session_cart = Cart.objects.filter(
                        session_key=session_key, user=None).first()
                    if session_cart:
                        for item in session_cart.items.all():
                            existing_item = CartItem.objects.filter(
                                cart=cart, variant=item.variant).first()
                            if existing_item:
                                existing_item.quantity += item.quantity
                                existing_item.total_price = existing_item.quantity * existing_item.variant.price_usd
                                existing_item.save()
                            else:
                                item.cart = cart
                                item.save()
                        session_cart.delete()
            else:
                # Handle guest users with session-based cart
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key

                cart, created = Cart.objects.get_or_create(
                    session_key=session_key, user=None)

            # Add or update item in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, variant=variant)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.total_price = cart_item.quantity * variant.price_usd
            cart_item.save()

            return JsonResponse({
                "message": "Item added to cart successfully",
                "cart_item": {
                    "id": cart_item.id,
                    "variant": cart_item.variant.id,
                    "quantity": cart_item.quantity,
                    "total_price": cart_item.total_price,
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)


@csrf_exempt
def api_cart_vieww(request, item_id=None):
    if request.method == "DELETE":
        try:
            cart_item = get_object_or_404(CartItem, id=item_id)
            cart_item.delete()
            return JsonResponse({"success": "Item removed from cart"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # Existing GET and POST logic here...

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def api_cart_view(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(
                session_key=session_key, user=None)

        cart_items = cart.items.all()
        total_price = sum(item.total_price for item in cart_items)
        discount_applied = None
        discount_type = None
        discount_amount = None

        # Apply discount if available
        discount_applied = None
        if cart.discount_code:
            try:
                discount_applied = cart.discount_code.code
                discount_type = cart.discount_code.discount_type
                discount_amount = (
                    cart.discount_code.discount_percentage if discount_type == "percentage"
                    else cart.discount_code.discount_price
                )
                total_price = cart.discount_code.apply_discount(total_price)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

        cart_data = {
            "cart_id": cart.id,
            "items": [
                {
                    "id": item.id,
                    "variant": item.variant.id,
                    "variantName": item.variant.product.name,
                    "number_of_tablets": item.variant.number_of_tablets,
                    "potency": item.variant.potency,
                    "unit_name": item.variant.unit.name if item.variant.unit else "",
                    "price_usd": item.variant.price_usd,
                    "quantity": item.quantity,
                    "image": f"http://192.168.1.4:8000{item.variant.product.images.first().image.url}"
                    if item.variant.product.images.exists() else "",
                }
                for item in cart_items
            ],
            "total_price": round(total_price, 2),
            "discount_applied": discount_applied,
            "discount_type": discount_type,
            "discount_amount": discount_amount,
        }

        return JsonResponse(cart_data, safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")
            quantity = data.get("quantity")

            if not item_id or quantity is None:
                return JsonResponse({"error": "Invalid data"}, status=400)

            cart_item = get_object_or_404(CartItem, id=item_id)
            inventory = Inventory.objects.filter(
                variant=cart_item.variant).first()

            if inventory and quantity > inventory.stock:
                return JsonResponse({
                    "error": f"Only {inventory.stock} units available for {cart_item.variant.product.name}."
                }, status=400)

            cart_item.quantity = quantity
            cart_item.total_price = quantity * cart_item.variant.price_usd
            cart_item.save()

            return JsonResponse({
                "success": "Cart updated",
                "cart_item": {
                    "id": cart_item.id,
                    "quantity": cart_item.quantity,
                    "total_price": cart_item.total_price
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def apply_discount_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get("code")

            if not code:
                return JsonResponse({"error": "Discount code is required"}, status=400)

            try:
                discount_code = DiscountCode.objects.get(code=code)
                if not discount_code.is_valid():
                    return JsonResponse({"error": "Discount code is not valid or expired"}, status=400)

            except DiscountCode.DoesNotExist:
                return JsonResponse({"error": "Invalid discount code"}, status=400)

            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                cart, created = Cart.objects.get_or_create(
                    session_key=session_key, user=None)

            cart.discount_code = discount_code
            cart.save()

            return JsonResponse({"success": f"Discount code {code} applied!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def remove_discount_code(request):
    if request.method == "POST":
        try:
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                cart, created = Cart.objects.get_or_create(
                    session_key=session_key, user=None)

            if not cart.discount_code:
                return JsonResponse({"error": "No discount code applied"}, status=400)

            cart.discount_code = None
            cart.save()

            return JsonResponse({"success": "Discount code removed successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def checkout_api(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'User is not authenticated'}, status=403)

    cart = Cart.objects.filter(user=user).first()
    if not cart or not cart.items.exists():
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    # Calculate the total cost before discount
    total_cost = sum(item.total_price for item in cart.items.all())

    # Initialize discount details
    discount_message = None
    total_cost_with_discount = total_cost
    discount_code = cart.discount_code
    shipping_addresses = Shipping.objects.filter(
        user=user).values('id', 'address_1')
    billing_addresses = Address.objects.filter(
        user=user).values('id', 'address_1')

    if discount_code:
        discount_decimal = Decimal(
            discount_code.discount_percentage) / Decimal(100)
        discount_amount = total_cost * discount_decimal
        total_cost_with_discount = total_cost - discount_amount
        discount_message = f"Discount Applied: {discount_code.discount_percentage}% (-${discount_amount:.2f})"

        if discount_code.discount_type == 'price':
            discount_amount = Decimal(discount_code.discount_price)
            total_cost_with_discount = total_cost - discount_amount
            discount_message = f"Discount Applied: ${discount_code.discount_price}"

    # Apply special discount if total cost exceeds $5000
    if total_cost_with_discount > Decimal('5000.00'):
        special_discount = Decimal('40') / Decimal('100')
        special_discount_amount = total_cost_with_discount * special_discount
        total_cost_with_discount -= special_discount_amount
        discount_message = (discount_message or '') + \
            f" | Special Discount Applied: 40% (-${special_discount_amount:.2f})"

    total_cost_with_discount = round(total_cost_with_discount, 2)

    if request.method == 'GET':
        # Enhance the cart_items response with additional details
        cart_items = [
            {
                "variantName": item.variant.product.name,
                "number_of_tablets": item.variant.number_of_tablets,
                "potency": item.variant.potency,
                "unit_name": item.variant.unit.name if item.variant.unit else "",
                "price_usd": item.variant.price_usd,
                "quantity": item.quantity,
                "image": f"http://192.168.1.5:8000{item.variant.product.images.first().image.url}"
            }
            for item in cart.items.all()
        ]

        return JsonResponse({
            'cart_items': cart_items,
            'total_cost': float(total_cost),
            'total_cost_with_discount': float(total_cost_with_discount),
            'discount_message': discount_message,
            'shipping_methods': list(ShippingMethod.objects.values('id', 'name', 'cost')),
            'shipping_addresses': list(shipping_addresses),
            'billing_addresses': list(billing_addresses),
        })

    elif request.method == 'POST':
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        shipping_address_id = data.get('shipping_address')
        billing_address_id = data.get('billing_address')
        shipping_method_id = data.get('shipping_method')

        if not all([shipping_address_id, billing_address_id, shipping_method_id]):
            return JsonResponse({'error': 'All fields are required to place an order.'}, status=400)

        try:
            shipping_address = Shipping.objects.get(
                id=shipping_address_id, user=user)
            billing_address = Address.objects.get(
                id=billing_address_id, user=user)
            shipping_method = ShippingMethod.objects.get(id=shipping_method_id)
        except (Shipping.DoesNotExist, Address.DoesNotExist, ShippingMethod.DoesNotExist):
            return JsonResponse({'error': 'Invalid address or shipping method selected.'}, status=400)

        # Handle health information data
        health_data = data.get('health_info', {})
        if isinstance(health_data, str):
            try:
                health_data = json.loads(health_data)
            except json.JSONDecodeError:
                health_data = {}

        health_info, created = HealthInformation.objects.update_or_create(
            user=user,
            defaults={
                'weight': health_data.get('weight'),
                'sex': health_data.get('sex'),
                'breastfeeding': health_data.get('breastfeeding'),
                'smoker': health_data.get('smoker'),
                'drug_allergies': health_data.get('drug_allergies'),
                'allergies_description': health_data.get('allergies_description', ''),
                'supplements': health_data.get('supplements', ''),
            }
        )

        shipping_cost = shipping_method.cost
        total_cost_with_shipping = total_cost_with_discount + shipping_cost

        # Create order
        order = Order.objects.create(
            user=user,
            total_cost=total_cost_with_shipping,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment_method='Cash on Delivery',
            status='Pending',
            shipping_method=shipping_method,
            health_info=health_info
        )

        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                user=user,
                variant=item.variant,
                quantity=item.quantity,
                price=item.variant.price_usd,
            )

        # Handle file attachments
        for file in request.FILES.getlist('attachments'):
            OrderAttachment.objects.create(order=order, file=file)

        # Clear the cart
        cart.items.all().delete()
        cart.discount_code = None
        cart.save()

        return JsonResponse({'success': 'Order placed successfully', 'order_id': order.id}, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@my_login_required
def order_list_api(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by(
        '-created_at').prefetch_related('order_items__variant__product')

    ist_timezone = pytz_timezone('Asia/Kolkata')

    order_list = []
    for order in orders:
        order_list.append({
            'id': order.id,
            'status': order.status,
            'total_price': order.total_cost,
            'created_at': localtime(order.created_at, ist_timezone).strftime('%Y-%m-%d %H:%M:%S') if order.created_at else None,
        })

    return JsonResponse({'orders': order_list}, safe=False)


@my_login_required
def order_detail_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Fetch all necessary details
    attachments = list(OrderAttachment.objects.filter(order=order).values())
    health_info = HealthInformation.objects.filter(
        user=request.user).values().first()
    shipping_method = ShippingMethod.objects.filter(
        id=order.shipping_method_id).values().first()
    reviews = list(Review.objects.filter(
        order=order).values('user', 'comment'))

    # Serialize the Shipping object to a dictionary
    shipping_address = {
        "address_1": order.shipping_address.address_1,
        "address_2": order.shipping_address.address_2,
        "city": order.shipping_address.city,
        "state": order.shipping_address.state,
        "postal_code": order.shipping_address.postal_code,
        "country": order.shipping_address.country,
    }

    billing_address = {
        "address_1": order.billing_address.address_1,
        "address_2": order.billing_address.address_2,
        "city": order.billing_address.city,
        "state": order.billing_address.state,
        "postal_code": order.billing_address.postal_code,
        "country": order.billing_address.country,
    }

    order_items = [
        {
            "variantName": item.variant.product.name,
            "number_of_tablets": item.variant.number_of_tablets,
            "potency": item.variant.potency,
            "unit_name": item.variant.unit.name if item.variant.unit else "",
            "price_usd": item.variant.price_usd,
            "quantity": item.quantity,
            "image": f"http://192.168.1.4:8000{item.variant.product.images.first().image.url}" if item.variant.product.images.exists() else ""
        }
        for item in OrderItem.objects.filter(order=order)
    ]

    response_data = {
        "order": {
            "id": order.id,
            "total_price": order.total_cost,
            "status": order.status,
            "payment_method": order.payment_method,
            "tracking_number": order.tracking_number,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
        },
        "order_items": order_items,
        "attachments": attachments,
        "health_info": health_info,
        "shipping_method": shipping_method,
        "reviews": reviews,
    }

    return JsonResponse(response_data)


@csrf_exempt
@my_login_required
def submit_review_api(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        comment = data.get("comment")

        if not comment:
            return JsonResponse({"error": "Comment cannot be empty"}, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        review, created = Review.objects.update_or_create(
            order=order, user=request.user,
            defaults={'comment': comment}
        )

        return JsonResponse({"success": "Review submitted successfully!"})


@my_login_required
def invoice_list_api(request):
    user = request.user
    invoices = Invoice.objects.filter(user=user).order_by('-issued_date')

    ist_timezone = pytz_timezone('Asia/Kolkata')

    invoice_list = [
        {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "order_id": invoice.order.id,
            "amount_due": str(invoice.amount_due),
            "status": invoice.status,
            "issued_date": localtime(invoice.issued_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S'),
            "due_date": localtime(invoice.due_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S') if invoice.due_date else None,
            "payment_date": localtime(invoice.payment_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S') if invoice.payment_date else None,
        }
        for invoice in invoices
    ]

    return JsonResponse({'invoices': invoice_list}, safe=False)


@my_login_required
def invoice_detail_api(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    ist_timezone = pytz_timezone('Asia/Kolkata')

    response_data = {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "amount_due": str(invoice.amount_due),
        "status": invoice.status,
        "issued_date": localtime(invoice.issued_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S'),
        "due_date": localtime(invoice.due_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S') if invoice.due_date else None,
        "payment_date": localtime(invoice.payment_date, ist_timezone).strftime('%Y-%m-%d %H:%M:%S') if invoice.payment_date else None,
        "order": {
            "id": invoice.order.id,
            "total_cost": str(invoice.order.total_cost),
            "billing_address": {
                "address_1": invoice.order.billing_address.address_1,
                "city": invoice.order.billing_address.city,
                "state": invoice.order.billing_address.state,
                "country": invoice.order.billing_address.country,
            } if invoice.order.billing_address else None,
            "shipping_address": {
                "address_1": invoice.order.shipping_address.address_1,
                "city": invoice.order.shipping_address.city,
                "state": invoice.order.shipping_address.state,
                "country": invoice.order.shipping_address.country,
            } if invoice.order.shipping_address else None,
            "shipping_method": {
                "name": invoice.order.shipping_method.name,
                "cost": str(invoice.order.shipping_method.cost),
            } if invoice.order.shipping_method else None,

            "order_items": [
                {
                    "variant": {
                        "product": {
                            "name": item.variant.product.name
                        },
                        "potency": item.variant.potency,
                        "unit": {
                            "name": item.variant.unit.name
                        },
                        "price_usd": str(item.variant.price_usd),
                    },
                    "quantity": item.quantity,
                    "price": str(item.price),
                }
                for item in invoice.order.order_items.all()
            ],
        } if invoice.order else None,
    }

    return JsonResponse(response_data)


@csrf_exempt
@my_login_required
def create_ticket_api(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
            ticket.save()
            return JsonResponse({'message': 'Ticket created successfully', 'ticket_id': ticket.id}, status=201)
        return JsonResponse({'error': 'Invalid data', 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@my_login_required
def ticket_list_api(request):
    tickets = Ticket.objects.filter(
        user=request.user).prefetch_related('replies')
    tickets_data = [
        {
            'id': ticket.id,
            'subject': ticket.subject,
            'status': ticket.status,
            'latest_reply': ticket.replies.order_by('-created_at').first().message if ticket.replies.exists() else None,
        }
        for ticket in tickets
    ]
    return JsonResponse({'tickets': tickets_data}, status=200)


@my_login_required
@csrf_exempt
def ticket_detail_api(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    latest_reply = ticket.replies.order_by('-created_at').first()

    if request.method == 'POST':
        if ticket.status != 'Closed':
            try:
                data = json.loads(request.body)
                form = TicketReplyForm(data)
                if form.is_valid():
                    reply = form.save(commit=False)
                    reply.ticket = ticket
                    reply.user = request.user
                    reply.save()
                    return JsonResponse({'message': 'Reply added successfully'}, status=201)
                return JsonResponse({'error': 'Invalid data', 'errors': form.errors}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        return JsonResponse({'error': 'This ticket is closed and cannot accept new messages.'}, status=403)

    replies = list(ticket.replies.values('message', 'created_at',
                                         ))  # Include replies

    ticket_data = {
        'id': ticket.id,
        'subject': ticket.subject,
        'status': ticket.status,
        'deparment': ticket.deparment,  # Fixed typo
        'description': ticket.description,
        'attachments': ticket.attachments.url if ticket.attachments else None,
        'replies': replies  # Add replies here
    }
    return JsonResponse(ticket_data, status=200)


@csrf_exempt
def user_chat_request_api(request):
    if request.method == 'GET':  # Handle GET request for agent status
        online_agents = Agent.objects.filter(is_online=True).count()
        return JsonResponse({'online_agents': online_agents})

    if request.method == 'POST':  # Handle chat/problem request
        data = json.loads(request.body)
        online_agents = Agent.objects.filter(is_online=True)

        if online_agents.exists():
            agent = online_agents.first()
            user = request.user if request.user.is_authenticated else None

            guest_name = data.get('name') if not user else None
            guest_email = data.get('email') if not user else None
            guest_phone = data.get('phone') if not user else None

            try:
                with transaction.atomic():
                    chat_request = ChatRequest.objects.create(
                        user=user,
                        guest_name=guest_name,
                        guest_email=guest_email,
                        guest_phone=guest_phone,
                        agent=agent
                    )
                return JsonResponse({'message': 'Chat request created successfully', 'chat_request_id': chat_request.id}, status=201)
            except IntegrityError as e:
                return JsonResponse({'error': 'Error creating chat request', 'details': str(e)}, status=500)

        else:
            try:
                problem_request = ProblemRequest.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    name=data.get('name'),
                    email=data.get('email'),
                    phone=data.get('phone'),
                    problem_description=data.get('problem_description')
                )
                return JsonResponse({'message': 'Problem request submitted successfully'}, status=201)
            except IntegrityError as e:
                return JsonResponse({'error': 'Error submitting problem request', 'details': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def user_chat_session_api(request, chat_request_id):
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)

    if request.method == 'POST':
        data = json.loads(request.body)
        message_text = data.get('message')
        if message_text:
            sender = request.user if request.user.is_authenticated else None
            ChatMessage.objects.create(
                session=chat_request,
                sender=sender,
                message=message_text
            )
            return JsonResponse({'message': 'Message sent successfully'}, status=201)
        return JsonResponse({'error': 'Message text is required'}, status=400)

    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')
    messages_data = [
        {'sender': msg.sender.username if msg.sender else 'Guest',
            'message': msg.message, 'timestamp': msg.timestamp}
        for msg in messages
    ]

    return JsonResponse({
        'chat_request_id': chat_request.id,
        'agent': chat_request.agent.name,
        'user': chat_request.user.username if chat_request.user else None,
        'messages': messages_data
    }, status=200)


@csrf_exempt
def search_suggestions_api(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # Search for active products matching the query in name or brand_name
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand_name__icontains=query), is_active=True
        )

        for product in products:
            seen_potencies = set()
            variants = product.variants.all()  # Fetch all variants

            for variant in variants:
                potency_value = float(variant.potency)
                formatted_potency = int(
                    potency_value) if potency_value.is_integer() else potency_value
                potency_key = f"{formatted_potency} {variant.unit.name}"

                if potency_key not in seen_potencies:
                    seen_potencies.add(potency_key)
                    brand_display = f" ({product.brand_name})" if product.brand_name else ''
                    results.append({
                        'name': f"{product.name}{brand_display} {formatted_potency} {variant.unit.name}",
                        'product_id': product.id  # Send product ID instead of variant URL
                    })

    return JsonResponse(results, safe=False)


def about_us(request):
    site_setting = SiteSetting.objects.first()  # Get site details
    return render(request, 'store/about_us.html', {'site_setting': site_setting})


def faq_page(request):

    return render(request, 'store/faq.html')


def term(request):
    site_setting = SiteSetting.objects.first()  # Get site details
    return render(request, 'store/terms.html', {'site_setting': site_setting})


def about_us_api(request):
    site_setting = SiteSetting.objects.first()
    if site_setting:
        data = {
            "site_setting": {
                "site_title": site_setting.site_title,
                "description": "Your trusted partner for all your medical and healthcare needs."
            }
        }
    else:
        data = {"error": "Site settings not found"}
    return JsonResponse(data)


def term_api(request):
    site_setting = SiteSetting.objects.first()
    if site_setting:
        # Assuming 'terms_conditions' field exists in SiteSetting model
        terms_content = site_setting.site_title
    else:
        terms_content = "No terms available at the moment."

    return JsonResponse({"terms": terms_content})
