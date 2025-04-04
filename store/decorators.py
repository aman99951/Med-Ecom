# invoices/decorators.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import Agent
from django.shortcuts import redirect
from functools import wraps


def my_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def agent_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        # Ensure the user is authenticated
        if request.user.is_authenticated:
            try:
                # Try to get the associated agent
                agent = get_object_or_404(
                    Agent, username=request.user.username)
                # If an agent is found, proceed to the view
                return view_func(request, *args, **kwargs)
            except Agent.DoesNotExist:
                # If no agent is found, return a forbidden response
                return HttpResponseForbidden("You do not have access to this page.")
        else:
            # Redirect to login if the user is not authenticated
            # Replace 'login' with your actual login URL
            return redirect('agent_login')
    return _wrapped_view
