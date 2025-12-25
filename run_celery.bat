@echo off
REM Запуск Celery worker
celery -A config worker --loglevel=info --pool=solo

REM Запуск Celery beat (в другом окне)
REM celery -A config beat --loglevel=info