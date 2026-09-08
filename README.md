# django-ai-benchmarking

A reusable Django app that integrates the [ai-benchmarking](https://github.com/samesameinc/ai-benchmarking) package. It provides database models, a polished Django Admin interface, and task-runner-agnostic background execution for running AI evaluation and benchmarking tasks.

## Features
- **Admin Integration:** Clean Django Admin UI for uploading dataset and knowledge base (KB) files, tracking job status, and viewing JSON results.
- **Task Runner Agnostic:** Seamlessly works with Celery, RQ, Django Signals, or Cloud Run Jobs.
- **Async Evaluation:** Native asyncio bridge for high-performance concurrent benchmarking using the underlying library.
- **Configurable Providers:** Supports Gemini, OpenAI, and Anthropic through Django settings.
- **Email Notifications:** Optionally emails the JSON results to the user upon completion.

## Installation

1. Install via pip:
```bash
pip install django-ai-benchmarking
```

2. Add to your `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    "django_ai_benchmarking",
]
```

3. Run migrations:
```bash
python manage.py migrate
```

## Configuration

Add the following configuration block to your `settings.py`:

```python
# API Keys for the underlying benchmarking models
GEMINI_API_KEY = "your-gemini-key"
OPENAI_API_KEY = "your-openai-key"        # Optional
ANTHROPIC_API_KEY = "your-anthropic-key"  # Optional

# Benchmarking Defaults
AI_BENCHMARKING_CONFIG = {
    "PROVIDER": "gemini",
    "MODEL": "gemini-2.5-flash",
    "JUDGE_MODEL": None,
}

# Optional: Email Notifications
AI_BENCHMARKING_SEND_EMAILS = True
DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"
```

## Background Task Execution

`django-ai-benchmarking` does not force a specific background task runner. You can execute pending benchmark jobs in several ways:

### Option 1: Ephemeral Workers (Cloud Run / Cron)
If you use serverless containers like Google Cloud Run Jobs or a standard cron job, use the built-in management command:
```bash
python manage.py run_benchmarks_once --limit 10
```
*This processes all `PENDING` jobs synchronously and automatically shuts down when the queue is empty, saving idle compute costs.*

### Option 2: Signal Triggers (Event-Driven)
You can trigger cloud infrastructure or internal logic immediately upon job creation by connecting to the custom signal:
```python
# your_app/apps.py
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = "your_app"

    def ready(self):
        from django_ai_benchmarking.signals import benchmark_job_created

        def trigger_worker(sender, instance, **kwargs):
            # Example: Ping GCP Cloud Run API to wake up the worker container
            pass

        benchmark_job_created.connect(trigger_worker)
```

### Option 3: Celery / RQ
If your host project already runs Celery, wrap the runner in a standard shared task:
```python
# your_app/tasks.py
from celery import shared_task
from django_ai_benchmarking.tasks import run_benchmark_job

@shared_task
def process_benchmark(job_id):
    run_benchmark_job(job_id)
```

## Local Development

To contribute or run the package locally using the development sandbox:

```bash
git clone https://github.com/your-org/django-ai-benchmarking.git
cd django-ai-benchmarking

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .

# Run sandbox migrations and server
cd sandbox
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## License

MIT License.