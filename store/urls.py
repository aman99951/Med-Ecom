# store/urls.py
from django.urls import path, include
from store import views
from .views import *
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cartss', CartViewSet)


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('add-to-cart/<int:variant_id>/',
         views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('profile/', views.profile_view, name='profile'),
    path('delete-account/', views.delete_account, name='delete_account'),


    path('guest/', views.guest_checkout, name='guest_checkout'),
    path('checkout/', views.checkout, name='checkout'),


    path('order-success/', views.order_success, name='order_success'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_confirmation, name='order_detail'),

    path('cancel_order/<int:order_id>/',
         views.cancel_order, name='cancel_order'),
    path('reorder/<int:order_id>/', views.reorder, name='reorder'),

    path('search-suggestions/', views.search_suggestions,
         name='search_suggestions'),
    path('sales-report/', views.sales_report, name='sales_report'),

    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('list/', views.ticket_list, name='ticket_list'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),


    path('chat-request/', views.user_chat_request_view, name='user_chat_request'),
    path('agent-requests/', views.agent_chat_requests_view,
         name='agent_chat_requests'),
    path('chat-session/<int:chat_request_id>/',
         views.user_chat_session_view, name='user_chat_session'),
    path('agent-chat-session/<int:chat_request_id>/',
         views.agent_chat_session_view, name='agent_chat_session'),
    path('toggle-status/', views.agent_toggle_status, name='agent_toggle_status'),

    path('submit-problem/', views.user_chat_request_view,
         name='submit_problem_description'),

    path('ticket/<int:ticket_id>/chat/',
         views.TicketChatView.as_view(), name='ticket-chat'),

    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('order/<int:order_id>/create_invoice/',
         views.create_invoice, name='create_invoice'),
    path('invoice/<int:invoice_id>/mark_paid/',
         views.mark_invoice_as_paid, name='mark_invoice_as_paid'),
    path('invoice/<int:invoice_id>/cancel/',
         views.cancel_invoice, name='cancel_invoice'),
    path('agent/login/', views.agent_login_view, name='agent_login'),
    path('agent/logout/', views.agent_logout_view, name='agent_logout'),

    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('faq/', views.faq, name='faq'),

    path("order-labels/", views.order_label_list_view, name="order_label_list"),
    path("order/<int:order_id>/labels/",
         views.order_label_view, name="order_labels"),
    path('api/', include(router.urls)),
    path('api/register/', RegisterAPIView.as_view(), name='register'),

    path('api/signin', SignInView.as_view(), name='signin'),
    path('api/signout', views.signout, name='signout'),
    path('api/check-login/', CheckLoginView.as_view(), name='check-login'),

    path('api/profile/', profile_api, name='profile-api'),
    path('api/profile/update/', update_profile_api, name='update-profile-api'),

    path("api/add-to-cart/", AddToCartView.as_view(), name="add-to-cart"),
    path("api/cart/", views.api_cart_view, name="api_cart_view"),
    path("api/cart/<int:item_id>/", views.api_cart_vieww, name="delete-cart-item"),
    path('api/apply-discount/', views.apply_discount_code,
         name='apply_discount_code'),
    path('api/remove-discount/', views.remove_discount_code,
         name='remove_discount_code'),
    path("api/checkout/", views.checkout_api, name="checkout_api"),
    path('api/order/<int:order_id>/', order_detail_api, name='order_detail_api'),
    path('api/order/<int:order_id>/review/',
         submit_review_api, name='submit_review_api'),
    path('api/orders/', order_list_api, name='order_list_api'),

    path('api/invoices/', invoice_list_api, name='invoice-list-api'),
    path('api/invoices/<int:invoice_id>/',
         invoice_detail_api, name='invoice-detail-api'),
    path('api/tickets/create/', create_ticket_api, name='create_ticket_api'),
    path('api/tickets/', ticket_list_api, name='ticket_list_api'),
    path('api/tickets/<int:pk>/', ticket_detail_api, name='ticket_detail_api'),

    path('api/chat/request/', user_chat_request_api,
         name='user_chat_request_api'),
    path('api/chat/session/<int:chat_request_id>/',
         user_chat_session_api, name='user_chat_session_api'),
    path('api/search-suggestions/', views.search_suggestions_api,
         name='api_search_suggestions'),
    path('about/', views.about_us, name='about_us'),
    path('faq/', views.faq_page, name='faq_page'),
    path('terms/', views.term, name='terms'),
    path('api/about-us/', about_us_api, name='about_us_api'),
    path('api/terms/', term_api, name='term_api'),

]
