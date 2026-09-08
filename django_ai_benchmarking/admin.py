from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import BenchmarkJob
from .signals import benchmark_job_created


@admin.register(BenchmarkJob)
class BenchmarkJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status_badge",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email", "error_message")
    ordering = ("-created_at",)

    fieldsets = (
        (
            _("Input Files"),
            {
                "fields": ("user", "data_file", "kb_file"),
            },
        ),
        (
            _("Execution Details"),
            {
                "fields": (
                    "status",
                    "progress_log",
                    "error_message",
                    "results",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = (
        "status",
        "progress_log",
        "error_message",
        "results",
        "created_at",
        "updated_at",
        "completed_at",
    )

    def get_readonly_fields(self, request, obj=None):
        # Prevent editing files or user after the job is created
        if obj:
            return self.readonly_fields + ("user", "data_file", "kb_file")
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.user:
            obj.user = request.user

        super().save_model(request, obj, form, change)

        # Dispatch an open-source signal on creation
        if not change:
            benchmark_job_created.send(
                sender=self.__class__, instance=obj, request=request
            )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        """Renders colored status pills in the admin list view."""
        colors = {
            BenchmarkJob.StatusChoices.PENDING: "#6c757d",  # Gray
            BenchmarkJob.StatusChoices.RUNNING: "#0d6efd",  # Blue
            BenchmarkJob.StatusChoices.COMPLETED: "#198754",  # Green
            BenchmarkJob.StatusChoices.FAILED: "#dc3545",  # Red
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; '
            'border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )