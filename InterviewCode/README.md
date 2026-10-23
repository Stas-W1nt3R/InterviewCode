# InterviewCode

> Платформа для проведения технических собеседований с совместным редактированием кода и запуском решений в изолированной песочнице в реальном времени.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.18-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

<!-- Добавь скриншот или гифку работы комнаты: положи файл в docs/demo.gif -->
![Демо](docs/demo.gif)

---

## О проекте

InterviewCode — это аналог CoderPad / HackerRank для живых собеседований:
интервьюер создаёт комнату, кандидат подключается по ссылке,
и оба работают в одном редакторе кода. Код запускается кнопкой **Run**,
а вывод программы виден всем участникам комнаты сразу, по мере выполнения.

**Проблема:** собеседовать по shared screen неудобно — нет подсветки,
кандидат не может писать код, сложно оценивать в реальном времени.
**Решение:** одна ссылка → общая комната → совместный редактор → мгновенный запуск кода.

## Возможности

### Уже реализовано

- **Регистрация и аутентификация** — JWT-токены (SimpleJWT), регистрация по email
- **Комнаты собеседований** — создание, присоединение по ссылке, роли `INTERVIEWER` / `CANDIDATE`
- **Жизненный цикл комнаты** — конечный автомат статусов с защитой переходов:

```text
WAITING ──join──▶ PROCESSING ──finish──▶ COMPLETED
```

- **Совместный редактор кода в реальном времени** — Monaco Editor + Yjs (CRDT) поверх WebSocket (Django Channels)
- **Запуск кода в Docker-песочнице** — для каждого запуска создаётся одноразовый контейнер; вывод стримится всем участникам комнаты, запуск можно остановить кнопкой **Stop**
- **WebSocket-аутентификация** — JWT проверяется в собственном middleware, доступ только для участников комнаты
- **Swagger / OpenAPI** — автодокументация всех эндпоинтов (drf-spectacular)
- **Docker-окружение** — проект поднимается одной командой

### В разработке

- [ ] Банк задач и наборы (Task / TaskCase)
- [ ] Чат и видеосвязь внутри комнаты
- [ ] Сохранение и разбор решений (Solution)
- [ ] Деплой и публичный доступ

## Технологии

| Слой | Стек |
| --- | --- |
| Backend | Python, Django 6, Django REST Framework |
| Real-time | Django Channels (ASGI), Redis (channel layer) |
| Редактор | Monaco Editor, Yjs (CRDT), y-websocket |
| Песочница | Docker SDK for Python |
| Auth | JWT (djangorestframework-simplejwt) |
| API-документация | drf-spectacular (Swagger UI) |
| База данных | PostgreSQL 15 |
| Контейнеризация | Docker, Docker Compose |

## Быстрый старт

### Требования

- Docker + Docker Compose

### Запуск

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Stas-W1nt3R/InterviewCode.git
cd InterviewCode/InterviewCode

# 2. Создай файл .env на основе примера и подставь свои значения
cp .env.example .env

# 3. Подними проект
docker compose up --build
```

Приложение будет доступно на `http://localhost:8000`, Swagger — на `http://localhost:8000/api/schema/swagger-ui/`.

> При первом запуске кода Docker скачает образ `python:3.13-slim`, поэтому первый запуск может занять больше времени.

### Как попробовать

1. Зарегистрируйся и войди.
2. Создай комнату и скопируй ссылку.
3. Открой ссылку во второй вкладке (лучше под другим пользователем).
4. Пиши код в одной вкладке — он появится во второй. Нажми **Run**: вывод увидят оба.

### Переменные окружения

В папке с `docker-compose.yaml` должен лежать файл `.env` (пример — `.env.example`):

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=interviewcode
DB_USER=interviewcode
DB_PASSWORD=interviewcode
DB_HOST=db
DB_PORT=5432
```

### Тесты

```bash
docker compose exec web python manage.py test
```

## API

### REST

| Метод | Эндпоинт | Описание |
| --- | --- | --- |
| `POST` | `/api/register/` | Регистрация пользователя |
| `POST` | `/api/token/` | Получение JWT (логин) |
| `POST` | `/api/token/refresh/` | Обновление JWT |
| `GET/POST` | `/api/rooms/` | Список комнат / создание |
| `POST` | `/api/rooms/{uuid}/join/` | Кандидат присоединяется к комнате |
| `POST` | `/api/rooms/{uuid}/finish/` | Интервьюер завершает собеседование |
| `GET` | `/api/schema/swagger-ui/` | Swagger UI |

### WebSocket

Токен передаётся в query string: `?token=<access>` (браузерный `WebSocket` не умеет задавать заголовки).

| Адрес | Назначение | Формат |
| --- | --- | --- |
| `/ws/room/{uuid}/` | Синхронизация редактора (Yjs) | бинарные кадры |
| `/ws/run/{uuid}/` | Запуск кода и вывод | JSON |

Сообщения канала запуска:

```text
клиент → сервер:  {"type": "run", "code": "print(1)"}
                  {"type": "stop"}
сервер → клиенты: {"type": "run_output", "data": "1\n"}
                  {"type": "run_finished"}
```

## Архитектура

```text
Браузер ──HTTP──▶ Django REST (DRF) ──▶ PostgreSQL
   │
   ├─WebSocket /ws/room/─▶ RoomConsumer ──┐
   │                                      ├─▶ Redis (channel layer, группы комнат)
   └─WebSocket /ws/run/──▶ RunConsumer ───┘
                               │
                               ▼
                       code_runner ──▶ Docker: одноразовый контейнер python:3.13-slim
```

Структура проекта:

```text
InterviewCode/
├── InterviewCode/          # настройки проекта (settings, urls, asgi)
├── mysite/                 # приложение
│   ├── models.py           # User, Room, RoomParticipant, Task, TaskCase, Solution
│   ├── serializers.py
│   ├── views.py            # ViewSets + кастомные actions (join, finish)
│   ├── routing.py          # маршруты WebSocket
│   ├── consumers.py        # RoomConsumer (байты Yjs) и RunConsumer (JSON, запуск кода)
│   ├── ws_auth.py          # middleware для проверки JWT в WebSocket
│   ├── code_runner.py      # запуск и остановка контейнера-песочницы
│   └── tests/              # тесты
│
├── .env.example
├── Dockerfile
├── docker-compose.yaml     # web (Django) + db (PostgreSQL) + redis
├── requirements.txt
└── manage.py
```

### Ключевые решения

- **Кастомная модель User** (`AbstractUser`) — гибко расширять под будущие роли.
- **Кастомные `@action` в ViewSet** — бизнес-операции (`join`, `finish`) как отдельные эндпоинты со своими правилами доступа.
- **Конечный автомат статусов комнаты** — переходы защищены на уровне API: join невозможен в завершённой комнате, finish — только для интервьюера.
- **UUID как публичный идентификатор комнат** — непредсказуемые ссылки-приглашения без отдельной модели токенов.
- **Два независимых WebSocket-канала** — синхронизация редактора (бинарный протокол Yjs) и управление запуском (JSON) разнесены по разным консьюмерам и группам Channels, чтобы протоколы не мешали друг другу.
- **Запуск в фоне** — выполнение кода вынесено в `asyncio`-задачу, а блокирующее чтение вывода контейнера идёт через `asyncio.to_thread`, поэтому сервер не блокируется и команду **Stop** можно принять во время работы кода.

## Безопасность песочницы

Код кандидата выполняется в одноразовом Docker-контейнере со следующими ограничениями:

| Мера | Защищает от |
| --- | --- |
| `network_disabled` | доступа к сети: утечки данных, атак на другие сервисы и базу |
| `mem_limit=128m` | исчерпания памяти хоста |
| `nano_cpus` (0.5 CPU) | захвата процессора бесконечными циклами |
| `pids_limit=64` | fork-бомб |
| `read_only` | записи в файловую систему контейнера |
| `user="nobody"` | запуска от root внутри контейнера |
| таймаут 10 секунд | бесконечного выполнения |
| лимит вывода 10 КБ | заваливания браузеров потоком вывода |
| `remove(force=True)` | накопления контейнеров на хосте |

### Ограничения

- Контейнеру `web` монтируется `/var/run/docker.sock`, поэтому он имеет широкие права на Docker хоста. Для учебного проекта это допустимо; в продакшене запуск стоит вынести в отдельный изолированный сервис.
- Для более сильной изоляции в продакшене используют gVisor или Firecracker и seccomp-профили.
- Реестр запущенных контейнеров (`room_dict`) хранится в памяти процесса, поэтому сейчас сервер рассчитан на один воркер. При масштабировании его нужно перенести в Redis.

---

### Автор

**Станислав Кондратьев** — backend-разработчик (Python / Django / DRF)

[![GitHub](https://img.shields.io/badge/GitHub-Stas--W1nt3R-181717?logo=github)](https://github.com/Stas-W1nt3R)

> Проект развивается открыто — идеи, issue и PR приветствуются
