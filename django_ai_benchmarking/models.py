from django.conf import settings
from django.db import models


class BenchmarkJob(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="benchmark_jobs",
    )

    # Input files
    data_file = models.FileField(upload_to="benchmarks/data/")
    kb_file = models.FileField(
        upload_to="benchmarks/kb/", blank=True, null=True
    )

    # Job tracking
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
    )
    progress_log = models.TextField(
        blank=True, help_text="Live logs from the benchmark run"
    )
    error_message = models.TextField(
        blank=True, help_text="Failure reasons or stack traces"
    )

    # Outputs
    results = models.JSONField(
        default=dict, blank=True, help_text="Structured metrics from ai-benchmarking"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Benchmark Job"
        verbose_name_plural = "Benchmark Jobs"

    def __str__(self):
        return f"Benchmark #{self.pk} - {self.status}"