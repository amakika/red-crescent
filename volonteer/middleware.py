# middleware.py
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin

class MobileCsrfExemptMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check for a custom header identifying mobile requests
        if 'X-Mobile-App' in request.headers:  # You can use any header that the mobile app sends
            setattr(request, '_dont_enforce_csrf_checks', True)
        # No need to call super().process_request(request)