class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        response['X-Frame-Options']           = 'DENY'
        response['X-Content-Type-Options']    = 'nosniff'
        response['X-XSS-Protection']          = '1; mode=block'
        response['Referrer-Policy']           = 'strict-origin-when-cross-origin'
        response['Permissions-Policy']        = 'camera=(), microphone=(), geolocation=()'
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        # Basic Content Security Policy — adjust to your asset hosts and needs.
        # This CSP allows the Bootstrap/Icons CDN used by the current templates while
        # keeping the rest of the policy fairly restrictive.
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:"
        )
        # Remove identifying headers if present
        try:
            response.headers.pop('Server', None)
            response.headers.pop('X-Powered-By', None)
        except Exception:
            # Some Django versions expose response as a dict-like; ignore if not available
            pass
        return response
