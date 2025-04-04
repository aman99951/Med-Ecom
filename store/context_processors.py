from .models import Cart
from .models import SiteSetting


def site_settings(request):
    site_settings, created = SiteSetting.objects.get_or_create(
        defaults={'site_title': 'Medicine E-commerce Website'}
    )
    return {'site_settings': site_settings}


def cart_items_count(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart, _ = Cart.objects.get_or_create(
            session_key=session_key, user=None)

    return {'cart_items_count': cart.items.count()}
