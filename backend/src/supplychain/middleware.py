"""
Middleware to track the current user for automated event generation.

This middleware stores the current user in thread-local storage so that
Django signals can access the user who triggered the model changes.
"""

import threading
from django.utils.deprecation import MiddlewareMixin

# Thread-local storage for the current user
_user = threading.local()


class CurrentUserMiddleware(MiddlewareMixin):
    """Middleware to store the current user in thread-local storage."""
    
    def process_request(self, request):
        """Store the current user when processing a request."""
        _user.value = getattr(request, 'user', None)
    
    def process_response(self, request, response):
        """Clean up the thread-local storage after processing response."""
        if hasattr(_user, 'value'):
            del _user.value
        return response
    
    def process_exception(self, request, exception):
        """Clean up the thread-local storage if an exception occurs."""
        if hasattr(_user, 'value'):
            del _user.value


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_user, 'value', None)
