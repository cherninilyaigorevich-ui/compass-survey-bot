import logging
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from app.api.answers import router as answers_router
from app.api.compass import router as compass_router
from app.api.health import router as health_router
from app.config import settings
from app.core.logging import setup_logging
from app.database import get_session_factory
from app.services.survey_seed import seed_location_survey


setup_logging()

logger = logging.getLogger(__name__)

# Каталог, в котором расположен текущий файл app/main.py
APP_DIR = Path(__file__).resolve().parent

# Каталог со статическими файлами
STATIC_DIR = APP_DIR / "static"

# Полный путь к favicon
FAVICON_PATH = STATIC_DIR / "favicon.svg"


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Код до yield выполняется при запуске приложения.
    Код после yield выполняется при корректной остановке.
    """

    logger.info("%s started", settings.app_name)
    logger.info("Version: %s", settings.app_version)
    logger.info("Environment: %s", settings.environment)

    try:
        session_factory = get_session_factory()

        with session_factory() as db:
            seed_location_survey(db)
            db.commit()

        logger.info(
            "Location survey seed completed successfully"
        )

    except Exception:
        logger.exception(
            "Location survey seed failed"
        )

    yield

    logger.info("%s stopped", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API сервиса Compass Survey Bot",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.api_route(
    "/favicon.ico",
    methods=["GET", "HEAD"],
    response_class=FileResponse,
    include_in_schema=False,
)
async def favicon() -> FileResponse:
    return FileResponse(
        path=FAVICON_PATH,
        media_type="image/svg+xml",
    )


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def root() -> HTMLResponse:
    """
    Публичная информационная страница сервиса.

    Этот маршрут не выполняет проверку базы данных.
    Для мониторинга используется отдельный endpoint /health.
    """
    app_name = escape(str(settings.app_name))
    app_version = escape(str(settings.app_version))
    environment = escape(str(settings.environment))

    html = f"""
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <meta
            name="robots"
            content="noindex, nofollow"
        >

        <title>{app_name}</title>

        <link
            rel="icon"
            href="/favicon.ico"
            type="image/svg+xml"
        >

        <style>
            :root {{
                color-scheme: dark;
                font-family:
                    Inter,
                    ui-sans-serif,
                    system-ui,
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    sans-serif;
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
                background:
                    radial-gradient(
                        circle at top,
                        #183b34 0%,
                        #101a18 42%,
                        #090d0c 100%
                    );
                color: #f4f7f6;
            }}

            .card {{
                width: min(680px, 100%);
                padding: 40px;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
                background: rgba(18, 27, 25, 0.88);
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
                backdrop-filter: blur(12px);
            }}

            .status {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(57, 211, 83, 0.12);
                color: #8ff09d;
                font-size: 14px;
                font-weight: 600;
            }}

            .status-dot {{
                width: 9px;
                height: 9px;
                border-radius: 50%;
                background: #4ade80;
                box-shadow: 0 0 14px rgba(74, 222, 128, 0.8);
            }}

            h1 {{
                margin: 24px 0 12px;
                font-size: clamp(32px, 6vw, 52px);
                line-height: 1.05;
                letter-spacing: -0.04em;
            }}

            .subtitle {{
                margin: 0;
                color: #aab8b4;
                font-size: 18px;
                line-height: 1.6;
            }}

            .info {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
                margin-top: 30px;
            }}

            .info-item {{
                padding: 16px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.045);
            }}

            .label {{
                display: block;
                margin-bottom: 6px;
                color: #82908c;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            .value {{
                font-weight: 600;
                overflow-wrap: anywhere;
            }}

            .actions {{
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 30px;
            }}

            .button {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 44px;
                padding: 0 18px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                color: #f4f7f6;
                background: rgba(255, 255, 255, 0.06);
                font-weight: 600;
                text-decoration: none;
                transition:
                    transform 0.15s ease,
                    background 0.15s ease;
            }}

            .button:hover {{
                transform: translateY(-1px);
                background: rgba(255, 255, 255, 0.11);
            }}

            .button-primary {{
                border-color: transparent;
                background: #35b66b;
                color: #06130c;
            }}

            .button-primary:hover {{
                background: #48ca7d;
            }}

            footer {{
                margin-top: 30px;
                color: #71807b;
                font-size: 13px;
            }}

            @media (max-width: 560px) {{
                .card {{
                    padding: 28px 22px;
                }}

                .info {{
                    grid-template-columns: 1fr;
                }}

                .actions {{
                    flex-direction: column;
                }}

                .button {{
                    width: 100%;
                }}
            }}
        </style>
    </head>

    <body>
        <main class="card">
            <div class="status">
                <span class="status-dot"></span>
                Service is running
            </div>

            <h1>{app_name}</h1>

            <p class="subtitle">
                API-сервис запущен и доступен через защищённое
                HTTPS-соединение.
            </p>

            <section class="info">
                <div class="info-item">
                    <span class="label">Версия</span>
                    <span class="value">{app_version}</span>
                </div>

                <div class="info-item">
                    <span class="label">Окружение</span>
                    <span class="value">{environment}</span>
                </div>
            </section>

            <nav class="actions" aria-label="Ссылки сервиса">
                <a class="button button-primary" href="/health">
                    Проверить состояние
                </a>

                <a class="button" href="/docs">
                    Swagger API
                </a>

                <a class="button" href="/redoc">
                    ReDoc
                </a>
            </nav>

            <footer>
                Compass Survey Bot · FastAPI · Traefik
            </footer>
        </main>
    </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)


app.include_router(health_router)
app.include_router(answers_router)
app.include_router(compass_router)
