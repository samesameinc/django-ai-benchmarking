import asyncio
import json
import os
import tempfile

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from ai_benchmarking.eval import run_benchmark_async
from .models import BenchmarkJob


def run_benchmark_job(job_id: int) -> None:
    """
    Executes an AI benchmark job synchronously.

    This runner function is task-framework agnostic. It can be called directly,
    or wrapped inside Celery, RQ, Django Tasks, or background threads.
    """
    try:
        job = BenchmarkJob.objects.get(pk=job_id)
    except BenchmarkJob.DoesNotExist:
        return

    job.status = BenchmarkJob.StatusChoices.RUNNING
    job.save(update_fields=["status", "updated_at"])

    temp_data_path = None
    temp_kb_path = None

    try:
        # 1. Read input files into temporary disk files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_data:
            temp_data.write(job.data_file.read())
            temp_data_path = temp_data.name

        if job.kb_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_kb:
                temp_kb.write(job.kb_file.read())
                temp_kb_path = temp_kb.name

        # 2. Safely populate environment variables from settings
        api_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        for key in api_keys:
            if hasattr(settings, key):
                os.environ[key] = getattr(settings, key)

        # 3. Read configurable model/provider defaults
        config = getattr(settings, "AI_BENCHMARKING_CONFIG", {})
        provider = config.get("PROVIDER", "gemini")
        model = config.get("MODEL", "gemini-2.5-flash")
        judge_model = config.get("JUDGE_MODEL", None)

        # 4. Execute asynchronous benchmark logic
        results_dict = asyncio.run(
            run_benchmark_async(
                data_path=temp_data_path,
                kb_path=temp_kb_path,
                output_path=None,
                provider=provider,
                model=model,
                judge_model=judge_model,
            )
        )

        # 5. Persist output metrics to model
        job.results = results_dict
        job.status = BenchmarkJob.StatusChoices.COMPLETED
        job.completed_at = timezone.now()
        job.save(
            update_fields=["results", "status", "completed_at", "updated_at"]
        )

        # 6. Send optional completion notification
        _send_completion_email(job, results_dict)

    except Exception as exc:
        job.status = BenchmarkJob.StatusChoices.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        raise exc

    finally:
        # Guaranteed cleanup of temporary files regardless of success or failure
        for path in (temp_data_path, temp_kb_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _send_completion_email(job: BenchmarkJob, results: dict) -> None:
    """Sends completed benchmark results to the requesting user."""
    should_send = getattr(settings, "AI_BENCHMARKING_SEND_EMAILS", True)
    if not should_send or not job.user or not job.user.email:
        return

    from_email = getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        getattr(settings, "EMAIL_HOST_USER", None),
    )

    email = EmailMessage(
        subject=f"AI Benchmark Job #{job.pk} Completed",
        body=(
            f"Your AI benchmark execution #{job.pk} has completed successfully.\n"
            "The JSON output metrics are attached to this message."
        ),
        from_email=from_email,
        to=[job.user.email],
    )

    email.attach(
        f"benchmark_{job.pk}_results.json",
        json.dumps(results, indent=2),
        "application/json",
    )
    email.send(fail_silently=True)