from django.core.management.base import BaseCommand
from django_ai_benchmarking.models import BenchmarkJob
from django_ai_benchmarking.tasks import run_benchmark_job


class Command(BaseCommand):
    help = "Runs pending benchmark jobs synchronously and exits (for Cloud Run or Cron workers)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of pending jobs to process in a single batch.",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        pending_jobs = BenchmarkJob.objects.filter(
            status=BenchmarkJob.StatusChoices.PENDING
        )

        if limit:
            pending_jobs = pending_jobs[:limit]

        job_ids = list(pending_jobs.values_list("pk", flat=True))

        if not job_ids:
            self.stdout.write("No pending jobs found. Exiting gracefully.")
            return

        self.stdout.write(f"Found {len(job_ids)} pending job(s) to process.")

        for job_id in job_ids:
            self.stdout.write(f"Processing BenchmarkJob #{job_id}...")
            try:
                run_benchmark_job(job_id)
                self.stdout.write(
                    self.style.SUCCESS(f"Finished BenchmarkJob #{job_id}.")
                )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Failed BenchmarkJob #{job_id}: {exc}")
                )

        self.stdout.write("All batch jobs complete. Shutting down container.")