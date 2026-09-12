"""
ARQ-compatible report generation worker.
Per README §6.3: picked up by ARQ when Redis is available.
Also callable directly as a FastAPI BackgroundTask when Redis is unavailable.
"""

async def generate_report(ctx, brand_input: dict, user_id: str, report_id: str):
    """
    ARQ worker function. Runs the full diagnostic pipeline and saves results.

    Args:
        ctx: ARQ worker context (provides Redis, etc.)
        brand_input: {name, website_url, industry, competitor, social_accounts}
        user_id: Clerk user ID
        report_id: UUID of the report row to update
    """
    from app.services import report_pipeline

    await report_pipeline.run(brand_input, user_id, report_id)


async def generate_report_sync(brand_input: dict, user_id: str, report_id: str):
    """Synchronous wrapper for use as FastAPI BackgroundTask (no Redis)."""
    return await generate_report(None, brand_input, user_id, report_id)
