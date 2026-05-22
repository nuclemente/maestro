"""Router /skills — invoca skills via `skill_runner`.

Frontend usa este endpoint para disparar skills longas (prepare, analyze-transcript).
Para skills síncronas, espera o retorno; para skills de background (`async=true`),
agenda no `BackgroundTasks` e responde 202.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.logging import get_logger
from app.services.skill_runner import SkillContractError, SkillNotFoundError, run_skill

router = APIRouter(prefix="/skills", tags=["skills"])
log = get_logger(__name__)


class SkillRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    async_: bool = Field(default=False, alias="async")
    timeout_s: int | None = None
    max_turns: int | None = None


@router.post("/{skill_name}/run")
def run_skill_endpoint(
    skill_name: str,
    payload: SkillRunRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    if payload.async_:
        def _job() -> None:
            try:
                run_skill(
                    skill_name,
                    payload.params,
                    timeout_s=payload.timeout_s,
                    max_turns=payload.max_turns,
                )
            except Exception:
                log.exception("skill.background.failed", skill=skill_name)

        background_tasks.add_task(_job)
        log.info("skill.background.scheduled", skill=skill_name)
        return {"ok": True, "scheduled": True, "skill": skill_name}

    try:
        result = run_skill(
            skill_name,
            payload.params,
            timeout_s=payload.timeout_s,
            max_turns=payload.max_turns,
        )
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SkillContractError as exc:
        raise HTTPException(status_code=502, detail=f"skill returned malformed output: {exc}")
    return {"ok": True, "data": result}
