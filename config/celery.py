import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("postman")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True
app.conf.event_queue_expires = 60
app.conf.worker_prefetch_multiplier = 1

if os.name == "nt":
    app.conf.worker_pool = "solo"
    app.conf.worker_concurrency = 1
    app.conf.broker_connection_retry_on_startup = True
    app.conf.worker_enable_remote_control = True
    app.conf.worker_disable_rate_limits = True

app.conf.beat_schedule = {
    "test-task-every-30-seconds": {
        "task": "users.tasks.test_task",
        "schedule": timedelta(seconds=30),
        "args": ["Периодическая тестовая задача от Beat"],
    },
    "check-payment-status-every-5-minutes": {
        "task": "users.tasks.check_payment_status",
        "schedule": timedelta(minutes=5),
    },
}

app.conf.timezone = "UTC"


@app.task(bind=True)
def debug_task(self):
    print(f"Debug task: {self.request!r}")
    return "Debug task completed"
