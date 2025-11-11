import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assignment2.settings")

app = Celery("assignment2")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Debug task: {self.request!r}")
