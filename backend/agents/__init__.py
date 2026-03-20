"""
Credit Clarity Autonomous Agent System
=======================================

Modular agent architecture for automated credit report processing,
dispute strategy generation, and bureau correspondence management.

Architecture:
    agents/
    ├── credit_report/          # PDF parsing, tradeline classification, scoring
    ├── dispute/                # Strategy, letter generation, response tracking
    └── orchestration/          # Coordinates sub-agents into end-to-end workflows

Usage from FastAPI endpoints:
    from agents.orchestration.autonomous_credit_agent import AutonomousCreditAgent
    agent = AutonomousCreditAgent()
    result = await agent.execute(user_id=user_id, pdf_path=path)

Usage from Celery workers:
    from agents.orchestration.autonomous_credit_agent import AutonomousCreditAgent
    agent = AutonomousCreditAgent()
    # Celery tasks call agent.execute() synchronously via asyncio.run()
"""

__version__ = "1.0.0"
