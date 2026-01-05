# 🎓 Postman - Образовательная платформа

## 🚀 Запуск проекта одной командой

### Быстрый старт:

# 1. Клонируйте проект
```
git clone <репозиторий>
cd Postman
```

# 2. Настройте переменные окружения
```
cp .env.example .env
```
#### Отредактируйте .env файл (укажите свои значения)

# 3. Запустите все сервисы одной командой
```
docker-compose up -d --build
```
# 4. Создайте суперпользователя
```
docker-compose exec backend python manage.py createsuperuser
``` 
# 🔗 Доступ к сервисам:
- Django API: http://localhost:8000
- Swagger документация: http://localhost:8000/swagger/
- Админ панель: http://localhost:8000/admin
- Health check: http://localhost:8000/api/health/

# 📊 Проверка работоспособности сервисов
1. Проверьте статус всех контейнеров:
```
docker-compose ps
```
# 2. Проверьте каждый сервис:
### Бэкенд (Django):
```
curl http://localhost:8000/api/health/
# Ожидаемый ответ: {"status": "healthy", ...}
```
### База данных (PostgreSQL):
```
docker-compose exec postgres pg_isready -U postgres_user
# Ожидаемый ответ: postgres:5432 - accepting connections
```
### Redis:
```
docker-compose exec redis redis-cli ping
# Ожидаемый ответ: PONG
```
### Celery Worker:
```
docker-compose logs celery_worker --tail=10
```
### Celery Beat:
```
docker-compose logs celery_beat --tail=10
```
# 🛠️ Полезные команды
### Управление Docker:
```
# Запуск: docker-compose up -d
# Остановка: docker-compose down
# Пересборка: docker-compose up -d --build
# Логи: docker-compose logs -f
# Логи конкретного сервиса: docker-compose logs -f backend
```
### Управление Django:
```
# Миграции: docker-compose exec backend python manage.py migrate
# Суперпользователь: docker-compose exec backend python manage.py createsuperuser
# Shell: docker-compose exec backend python manage.py shell
# Тесты: docker-compose exec backend python manage.py test
```
# ⚙️ Настройка .env файла
### Обязательные переменные для настройки:

- SECRET_KEY - сгенерируйте новый ключ
- POSTGRES_PASSWORD - пароль для PostgreSQL
- STRIPE_SECRET_KEY - ключ Stripe для платежей
- EMAIL_HOST_PASSWORD - пароль для email

# 🐛 Устранение проблем
### Если сервисы не запускаются:
1. Проверьте логи:
```
docker-compose logs
```
2. Проверьте порты:
Убедитесь, что порты 8000, 5432, 6379 свободны.
3. Очистите и перезапустите:
```
docker-compose down -v
docker-compose up -d --build
```
# 📞 Поддержка
### При возникновении проблем проверьте:

1. Все ли контейнеры запущены: docker-compose ps
2. Доступен ли health check: curl http://localhost:8000/api/health/
3. Проверьте логи проблемного сервиса

