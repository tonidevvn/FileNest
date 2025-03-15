"""Admin interface for monitoring models."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import FileAccessLog

@admin.register(FileAccessLog)
class FileAccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'file_name', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('file_name', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path(
                'monitoring-dashboard/',
                self.admin_site.admin_view(self.monitoring_dashboard_view),
                name='monitoring-dashboard',
            ),
        ]
        return custom_urls + urls

    def monitoring_dashboard_view(self, request):
        """Admin view for monitoring dashboard."""
        from django.shortcuts import redirect
        dashboard_url = reverse('monitoring:admin_dashboard')  # URL name from monitoring/urls.py
        return redirect(dashboard_url)


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_dashboard_url'] = reverse('admin:monitoring-dashboard') # URL name from monitoring/admin.py get_urls
        return super().changelist_view(request, extra_context=extra_context)
