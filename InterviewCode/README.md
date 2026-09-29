# InterviewCode

> Платформа для проведения технических собеседований с совместным редактированием кода и проверкой решений в реальном времени.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.18-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## О проекте

InterviewCode — это аналог CoderPad / HackerRank для живых собеседований:
интервьюер создаёт комнату и задачи, кандидат подключается по ссылке,
и оба работают в одном редакторе кода, который выполняется прямо в браузере.

**Проблема:** собеседовать по shared screen неудобно — нет подсветки,
кандидат не может писать код, сложно оценивать в реальном времени.
**Решение:** одна ссылка → общая комната → совместный редактор → мгновенный запуск кода.

## Возможности

### Уже реализовано

- **Регистрация и аутентификация** — JWT-токены (SimpleJWT), регистрация по email
- **Комнаты собеседований** — создание, присоединение по ссылке, роли `INTERVIEWER` / `CANDIDATE`
- **Жизненный цикл комнаты** — конечный автомат статусов с защитой переходов:

```javascript
CREATED ──join──▶ PROCESSING ──finish──▶ COMPLETED
```

- **Swagger / OpenAPI** — автодокументация всех эндпоинтов (drf-spectacular)
- **Docker-окружение** — проект поднимается одной командой

### В разработке

- [ ] Совместный редактор кода в реальном времени (WebSocket + CRDT)
- [ ] Изолированный запуск кода кандидата (Docker-песочница с лимитами)
- [ ] Банк задач и наборы (Task / TaskCase)
- [ ] Чат и видеосвязь внутри комнаты
- [ ] Сохранение и разбор решений (Solution)
- [ ] Деплой и публичный доступ

## Технологии

| Слой | Стек |
| --- | --- |
| Backend | Python, Django 6, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| API-документация | drf-spectacular (Swagger UI) |
| База данных | PostgreSQL 15 |
| Контейнеризация | Docker, Docker Compose |
| **Планируется:** WebSockets (Django Channels), Redis, Yjs + Monaco Editor, sandbox-раннер |  |

## Быстрый старт

### Требования

- Docker + Docker Compose

### Запуск

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Stas-W1nt3R/InterviewCode.git
cd InterviewCode/InterviewCode

# 2. Создай .env (пример значений ниже)
cp .env.example .env   # или создай файл вручную

# 3. Подними проект
docker compose up --build
```

Приложение будет доступно на `http://localhost:8000`, Swagger — на `http://localhost:8000/api/schema/swagger-ui/`.

### Переменные окружения

Создай файл `.env` в папке с `docker-compose.yaml`:

```env
SECRET_KEY=your-secret-key-here
DB_NAME=interviewcode
DB_USER=interviewcode
DB_PASSWORD=interviewcode
DB_HOST=db
DB_PORT=5432
```

## API 

| Метод | Эндпоинт | Описание |
| --- | --- | --- |
| `POST` | `/api/register/` | Регистрация пользователя |
| `POST` | `/api/token/` | Получение JWT (логин) |
| `POST` | `/api/token/refresh/` | Обновление JWT |
| `GET/POST` | `/api/rooms/` | Список комнат / создание |
| `POST` | `/api/rooms/{uuid}/join/` | Кандидат присоединяется к комнате |
| `POST` | `/api/rooms/{uuid}/finish/` | Интервьюер завершает собеседование |
| `GET` | `/api/schema/swagger-ui/` | Swagger UI |

## Архитектура

```javascript
InterviewCode/
├── InterviewCode/          # настройки проекта (settings, urls)
├── mysite/                 # приложение: models, serializers, views
│   ├── models.py           # User, Room, RoomParticipant, Task, TaskCase, Solution
│   ├── serializers.py
│   └── views.py            # ViewSets + кастомные actions (join, finish)
├── Dockerfile
├── docker-compose.yaml     # web (Django) + db (PostgreSQL)
└── manage.py
```

Ключевые решения:

- **Кастомная модель User** (`AbstractUser`) — гибко расширять под будущие роли.
- **Кастомные `@action` в ViewSet** — бизнес-операции (`join`, `finish`) как отдельные эндпоинты со своими правилами доступа.
- **Конечный автомат статусов комнаты** — переходы защищены на уровне API: join невозможен в завершённой комнате, finish — только для интервьюера.
- **UUID как публичный идентификатор комнат** — непредсказуемые ссылки-приглашения без отдельной модели токенов.

## Roadmap

1. **MVP** — комнаты + совместный редактор + запуск кода
2. **Бета** — банк задач, чат, история собеседований
3. **Продакт** — деплой, регистрация для всех, мониторинг

---

### Автор

**Станислав Кондратьев** — backend-разработчик (Python / Django)

[![GitHub](https://img.shields.io/badge/GitHub-Stas--W1nt3R-181717?logo=github)](https://github.com/Stas-W1nt3R)

> Проект развивается открыто — идеи, issue и PR приветствуются 