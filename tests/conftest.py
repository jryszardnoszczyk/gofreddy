"""Shared pytest fixtures for freddy integration tests.

All fixtures use REAL services (PostgreSQL, Gemini, R2, platform APIs).
Test isolation: each test runs inside a DB transaction that rolls back on teardown.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest
import pytest_asyncio
from dotenv import dotenv_values, load_dotenv

# ── Load real credentials ────────────────────────────────────────────────────
# Precedence:
#   1) shell/CI-provided environment (highest)
#   2) .env.test (test defaults/overrides)
#   3) .env (local base defaults)
_project_root = Path(__file__).resolve().parent.parent
_env_test = _project_root / ".env.test"
_env_main = _project_root / ".env"
_preexisting_env_keys = set(os.environ)
_PLACEHOLDER_PREFIXES = ("test_", "dummy_", "fake_", "changeme")
_SAFE_FALLBACK_KEYS = {
    # R2
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    # Live external integrations
    "GEMINI_API_KEY",
    "SCRAPECREATORS_API_KEY",
    "APIFY_TOKEN",
}

# 1. Load .env as base defaults without clobbering shell/CI env.
if _env_main.exists():
    load_dotenv(_env_main, override=False)
else:
    # Adjacent-checkout convenience: source only safe external-integration keys from parent .env.
    # Avoid pulling in unrelated config (e.g., DATABASE_URL) which could make tests
    # destructive if a non-test DB is configured in the parent project.
    if _project_root.parent.name == "." + "work" + "trees":
        _env_main_fallback = _project_root.parent.parent / ".env"
        if _env_main_fallback.exists():
            for k, v in (dotenv_values(_env_main_fallback) or {}).items():
                if not v:
                    continue
                if k in _SAFE_FALLBACK_KEYS:
                    os.environ.setdefault(k, v)

# 2. Load .env.test on top:
#    - overwrite .env values
#    - never overwrite shell/CI-provided env captured before file loads
if _env_test.exists():
    with open(_env_test) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if value and key not in _preexisting_env_keys:
                os.environ[key] = value

# Fallback dummy values so settings classes don't crash if no .env exists.
# These only matter when running pure-logic tests that don't need real services.
os.environ.setdefault("R2_ACCOUNT_ID", "a" * 32)
os.environ.setdefault("R2_ACCESS_KEY_ID", "test_access_key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test_secret_key")
os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
os.environ.setdefault("SCRAPECREATORS_API_KEY", "test_scrapecreators_key")
os.environ.setdefault("APIFY_TOKEN", "test_apify_token")
os.environ.setdefault("GEMINI_API_KEY", "test_gemini_key")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_key")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake_key")
os.environ.setdefault("STRIPE_PUBLISHABLE_KEY", "pk_test_fake_key")
os.environ.setdefault("STRIPE_PRICE_PRO", "price_pro_test")


def _is_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _is_placeholder_secret(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    if not normalized:
        return True
    return normalized.startswith(_PLACEHOLDER_PREFIXES)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip live tests unless explicitly enabled with real-looking credentials.

    This prevents noisy failures when running in local multi-checkout environments that
    only have placeholder defaults.
    """
    run_live_external = _is_truthy("RUN_LIVE_EXTERNAL")
    run_gemini = _is_truthy("RUN_GEMINI")
    run_live_api = _is_truthy("RUN_LIVE_API")

    gemini_key = os.getenv("GEMINI_API_KEY")
    scrapecreators_key = os.getenv("SCRAPECREATORS_API_KEY")
    apify_token = os.getenv("APIFY_TOKEN")
    r2_keys = [
        os.getenv("R2_ACCOUNT_ID"),
        os.getenv("R2_ACCESS_KEY_ID"),
        os.getenv("R2_SECRET_ACCESS_KEY"),
        os.getenv("R2_BUCKET_NAME"),
    ]

    gemini_configured = not _is_placeholder_secret(gemini_key)
    external_configured = (
        not _is_placeholder_secret(scrapecreators_key)
        or not _is_placeholder_secret(apify_token)
    )
    r2_configured = all(not _is_placeholder_secret(v) for v in r2_keys)

    if run_live_external and not external_configured:
        raise pytest.UsageError(
            "RUN_LIVE_EXTERNAL=1 but provider credentials look unset/placeholder "
            "(expected real SCRAPECREATORS_API_KEY and/or APIFY_TOKEN)."
        )
    if run_gemini and not gemini_configured:
        raise pytest.UsageError(
            "RUN_GEMINI=1 but GEMINI_API_KEY looks unset/placeholder."
        )

    skip_live_external = pytest.mark.skip(
        reason="external_api tests require RUN_LIVE_EXTERNAL=1 and real provider credentials"
    )
    skip_gemini = pytest.mark.skip(
        reason="gemini tests require RUN_GEMINI=1 and a real GEMINI_API_KEY"
    )
    skip_r2 = pytest.mark.skip(
        reason="r2 tests require real R2_* credentials"
    )
    skip_live_api = pytest.mark.skip(
        reason="live_api tests require RUN_LIVE_API=1"
    )

    for item in items:
        if "live_api" in item.keywords and not run_live_api:
            item.add_marker(skip_live_api)
        if "external_api" in item.keywords and not run_live_external:
            item.add_marker(skip_live_external)
        if "gemini" in item.keywords and not run_gemini:
            item.add_marker(skip_gemini)
        if "r2" in item.keywords and not r2_configured:
            item.add_marker(skip_r2)

# ── Imports (after env is set) ───────────────────────────────────────────────

import aioboto3  # noqa: E402
from google import genai  # noqa: E402

from tests.helpers.pool_adapter import SingleConnectionPool  # noqa: E402

from tests.fixtures.stable_ids import YOUTUBE_VIDEO_ID  # noqa: E402
from src.analysis.config import AnalysisSettings, DatabaseSettings  # noqa: E402
from src.analysis.gemini_analyzer import GeminiVideoAnalyzer  # noqa: E402
from src.analysis.repository import PostgresAnalysisRepository  # noqa: E402
from src.analysis.service import AnalysisService  # noqa: E402
from src.billing.repository import BillingRepository  # noqa: E402
from src.billing.service import BillingService  # noqa: E402
from src.brands import BrandService, PostgresBrandRepository  # noqa: E402
from src.common.enums import Platform  # noqa: E402
from src.creative import PostgresCreativePatternRepository  # noqa: E402
from src.deepfake import PostgresDeepfakeRepository  # noqa: E402
from src.demographics import (  # noqa: E402
    DemographicsService,
    PostgresDemographicsRepository,
)
from src.evolution import EvolutionService, PostgresEvolutionRepository  # noqa: E402
from src.fetcher import InstagramFetcher, TikTokFetcher, YouTubeFetcher  # noqa: E402
from src.fetcher.config import FetcherSettings  # noqa: E402
from src.fraud.config import FraudDetectionConfig  # noqa: E402
from src.fraud.repository import PostgresFraudRepository  # noqa: E402
from src.fraud.service import FraudDetectionService  # noqa: E402
from src.jobs.repository import PostgresJobRepository  # noqa: E402
from src.search.service import GeminiQueryParser, SearchConfig, SearchService  # noqa: E402
from src.storage.config import R2Settings  # noqa: E402
from src.storage.r2_storage import R2VideoStorage  # noqa: E402
from src.stories import PostgresStoryRepository, R2StoryStorage, StoryService  # noqa: E402
from src.policies import PostgresPolicyRepository  # noqa: E402
from src.trends import PostgresTrendRepository, TrendService  # noqa: E402


# ── Session-scoped fixtures (created once per test run) ──────────────────────


@pytest_asyncio.fixture(scope="session")
async def db_pool():
    """Real asyncpg connection pool to test database."""
    db_config = DatabaseSettings()
    pool = await asyncpg.create_pool(
        dsn=db_config.database_url.get_secret_value(),
        min_size=2,
        max_size=10,
        command_timeout=60,
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture(scope="session")
async def gemini_analyzer():
    """Real GeminiVideoAnalyzer with conservative settings for tests."""
    config = AnalysisSettings()
    analyzer = GeminiVideoAnalyzer(
        api_key=config.gemini_api_key.get_secret_value(),
        model=config.model,
        max_retries=2,
        base_delay=1.0,
        max_concurrent=2,
    )
    yield analyzer
    await analyzer.close()


@pytest_asyncio.fixture(scope="session")
async def r2_storage():
    """Real R2VideoStorage with test bucket."""
    config = R2Settings()
    session = aioboto3.Session(
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key.get_secret_value(),
    )
    storage = R2VideoStorage(session, config)
    yield storage
    await storage.close()


@pytest_asyncio.fixture(scope="session")
async def fetchers(r2_storage):
    """Real platform fetchers (TikTok, Instagram, YouTube)."""
    settings = FetcherSettings()
    fetcher_map = {
        Platform.TIKTOK: TikTokFetcher(r2_storage, settings),
        Platform.INSTAGRAM: InstagramFetcher(r2_storage, settings),
        Platform.YOUTUBE: YouTubeFetcher(r2_storage, settings),
    }
    for f in fetcher_map.values():
        await f.__aenter__()
    yield fetcher_map
    for f in fetcher_map.values():
        await f.__aexit__(None, None, None)


@pytest_asyncio.fixture(scope="session")
async def gemini_client():
    """Real Gemini client for agent tests."""
    config = AnalysisSettings()
    return genai.Client(api_key=config.gemini_api_key.get_secret_value())


@pytest_asyncio.fixture(scope="session")
async def gemini_query_parser():
    """Real Gemini-based query parser for search tests."""
    config = AnalysisSettings()
    return GeminiQueryParser(
        api_key=config.gemini_api_key.get_secret_value(),
    )


# ── Function-scoped fixtures (per test, with transaction rollback) ───────────


@pytest_asyncio.fixture
async def db_conn(db_pool):
    """Single DB connection inside a transaction — rolls back after each test."""
    conn = await db_pool.acquire()
    tx = conn.transaction()
    await tx.start()
    yield conn
    await tx.rollback()
    await db_pool.release(conn)


# ── Repository fixtures (function-scoped, use transactional connection) ──────


@pytest_asyncio.fixture
async def analysis_repo(db_conn):
    """Real PostgresAnalysisRepository with transactional isolation."""
    return PostgresAnalysisRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def billing_repo(db_conn):
    """Real BillingRepository with transactional isolation."""
    return BillingRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def brand_repo(db_conn):
    """Real PostgresBrandRepository with transactional isolation."""
    return PostgresBrandRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def creative_repo(db_conn):
    """Real PostgresCreativePatternRepository with transactional isolation."""
    return PostgresCreativePatternRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def demographics_repo(db_conn):
    """Real PostgresDemographicsRepository with transactional isolation."""
    return PostgresDemographicsRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def deepfake_repo(db_conn):
    """Real PostgresDeepfakeRepository with transactional isolation."""
    return PostgresDeepfakeRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def evolution_repo(db_conn):
    """Real PostgresEvolutionRepository with transactional isolation."""
    return PostgresEvolutionRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def fraud_repo(db_conn):
    """Real PostgresFraudRepository with transactional isolation."""
    return PostgresFraudRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def job_repo(db_conn):
    """Real PostgresJobRepository with transactional isolation."""
    return PostgresJobRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def story_repo(db_conn):
    """Real PostgresStoryRepository with transactional isolation."""
    return PostgresStoryRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def trend_repo(db_conn):
    """Real PostgresTrendRepository with transactional isolation."""
    return PostgresTrendRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def policy_repo(db_conn):
    """Real PostgresPolicyRepository with transactional isolation."""
    return PostgresPolicyRepository(SingleConnectionPool(db_conn))


# ── Service fixtures (function-scoped, compose repos + real services) ────────


@pytest_asyncio.fixture
async def analysis_service(gemini_analyzer, analysis_repo, r2_storage):
    """Real AnalysisService with real Gemini + real DB."""
    return AnalysisService(
        analyzer=gemini_analyzer,
        repository=analysis_repo,
        storage=r2_storage,
    )


@pytest_asyncio.fixture
async def billing_service(billing_repo):
    """Real BillingService with real DB."""
    return BillingService(billing_repo)


@pytest_asyncio.fixture
async def credit_repo(db_conn):
    """Real CreditRepository with transactional isolation."""
    from src.billing.credits import CreditRepository

    return CreditRepository(SingleConnectionPool(db_conn))


@pytest_asyncio.fixture
async def credit_service(credit_repo):
    """Real CreditService with real DB."""
    from src.billing.credits import CreditService, CreditSettings

    return CreditService(repository=credit_repo, settings=CreditSettings())


@pytest_asyncio.fixture
async def brand_service(gemini_analyzer, brand_repo):
    """Real BrandService with real Gemini + real DB."""
    return BrandService(
        analyzer=gemini_analyzer,
        repository=brand_repo,
    )


@pytest_asyncio.fixture
async def demographics_service(gemini_analyzer, demographics_repo):
    """Real DemographicsService with real Gemini + real DB."""
    return DemographicsService(
        analyzer=gemini_analyzer,
        repository=demographics_repo,
    )


@pytest_asyncio.fixture
async def evolution_service(evolution_repo):
    """Real EvolutionService with real DB."""
    return EvolutionService(repository=evolution_repo)


@pytest_asyncio.fixture
async def fraud_service(fraud_repo):
    """Real FraudDetectionService with real DB."""
    config = FraudDetectionConfig()
    return FraudDetectionService(repository=fraud_repo, config=config)


@pytest_asyncio.fixture
async def trend_service(trend_repo):
    """Real TrendService with real DB."""
    return TrendService(repository=trend_repo)


@pytest_asyncio.fixture
async def search_service(gemini_query_parser, fetchers):
    """Real SearchService with real Gemini parser + real platform fetchers."""
    config = SearchConfig()
    return SearchService(
        parser=gemini_query_parser,
        tiktok_fetcher=fetchers[Platform.TIKTOK],
        instagram_fetcher=fetchers[Platform.INSTAGRAM],
        youtube_fetcher=fetchers[Platform.YOUTUBE],
        config=config,
    )


@pytest_asyncio.fixture
async def r2_story_storage(r2_storage):
    """Real R2StoryStorage with real R2VideoStorage."""
    r2_config = R2Settings()
    return R2StoryStorage(r2_storage, r2_config)


@pytest_asyncio.fixture
async def youtube_video_in_r2(fetchers):
    """Ensure the stable YouTube video exists in R2 before analysis tests.

    Uses the real YouTube fetcher. The fetcher handles R2 caching —
    if already stored, this is a no-op.
    """
    yt_fetcher = fetchers[Platform.YOUTUBE]
    await yt_fetcher.fetch_video(Platform.YOUTUBE, YOUTUBE_VIDEO_ID)


@pytest_asyncio.fixture
async def r2_cleanup(r2_storage):
    """Track R2 keys to clean up after test."""
    keys: list[str] = []
    yield keys
    client = await r2_storage._get_client()
    for key in keys:
        try:
            await client.delete_object(
                Bucket=r2_storage._config.bucket_name, Key=key,
            )
        except Exception:
            pass


@pytest_asyncio.fixture
async def story_service(story_repo, r2_storage, fetchers):
    """Real StoryService with real DB + R2 + Instagram fetcher."""
    r2_config = R2Settings()
    storage = R2StoryStorage(r2_storage, r2_config)
    return StoryService(
        repository=story_repo,
        storage=storage,
        instagram_fetcher=fetchers[Platform.INSTAGRAM],
    )


# ── Test data fixtures ───────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def test_user(db_conn):
    """Insert a test user into the DB (rolled back after test)."""
    user_id = uuid4()
    email = f"test-{user_id.hex[:8]}@test.com"
    await db_conn.execute(
        "INSERT INTO users (id, email) VALUES ($1, $2)",
        user_id, email,
    )
    return {"id": user_id, "email": email}


@pytest_asyncio.fixture
async def test_api_key(db_conn, test_user):
    """Insert a test API key for the test user (rolled back after test)."""
    import hashlib

    key_id = uuid4()
    raw_key = f"vi_test_{key_id.hex[:16]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    await db_conn.execute(
        "INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name) VALUES ($1, $2, $3, $4, $5)",
        key_id, test_user["id"], key_hash, key_prefix, "test-key",
    )
    return {"id": key_id, "raw_key": raw_key, "key_hash": key_hash, "user_id": test_user["id"]}


# ── File fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_video_path() -> Path:
    """Path to the real test video file (5-second MP4)."""
    path = Path(__file__).parent / "fixtures" / "test_video.mp4"
    assert path.exists(), f"Test video not found at {path}. Generate with ffmpeg."
    return path


@pytest.fixture
def large_video_path(tmp_path: Path) -> Path:
    """Create a video file exceeding the size limit (for validation tests)."""
    video_path = tmp_path / "large_video.mp4"
    video_path.write_bytes(b"x" * (501 * 1024 * 1024))
    return video_path
