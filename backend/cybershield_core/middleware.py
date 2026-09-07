"""
Audit Log Middleware
Automatically records every state-changing API request to the audit trail.
"""

import json
import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("cybershield.audit")

AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
EXCLUDED_PATHS = {"/api/auth/refresh/", "/api/schema/", "/api/docs/"}


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware that logs all write operations (POST/PUT/PATCH/DELETE)
    for compliance and forensic accountability. Logs include:
    - Authenticated user + tenant
    - HTTP method and path
    - Response status code
    - Client IP address
    - Timestamp (UTC)
    """

    def process_response(self, request, response):
        if request.method not in AUDIT_METHODS:
            return response
        if request.path in EXCLUDED_PATHS:
            return response

        user = getattr(request, "user", None)
        user_display = str(user) if user and user.is_authenticated else "anonymous"

        logger.info(
            json.dumps({
                "timestamp": timezone.now().isoformat(),
                "user": user_display,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "ip": self._get_client_ip(request),
            })
        )

        # Track failed logins per client IP using Django cache backend
        if request.path == "/api/auth/login/" and request.method == "POST":
            from django.core.cache import cache
            ip = self._get_client_ip(request)
            cache_key = f"failed_login_attempts_{ip}"
            
            if response.status_code == 401:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, timeout=300) # 5-minute sliding window
                
                if attempts >= 5:
                    logger.critical(
                        json.dumps({
                            "event": "BRUTE_FORCE_DETECTED",
                            "timestamp": timezone.now().isoformat(),
                            "ip": ip,
                            "attempts": attempts,
                            "action": "IP_BLOCKED_AUTO",
                        })
                    )
                    from detection.models import IPBlocklist, Tenant
                    tenant = Tenant.objects.first()
                    if tenant:
                        IPBlocklist.objects.get_or_create(
                            ip_address=ip,
                            tenant=tenant,
                            defaults={
                                "reason": f"Auto-contained: 5 failed login attempts in 5 minutes.",
                                "is_active": True,
                            }
                        )
            elif response.status_code == 200:
                cache.delete(cache_key)

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
