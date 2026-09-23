from fastapi import APIRouter, Request

from app.evaluation.harness import EvaluationHarness, SCENARIOS

router = APIRouter(prefix="/v1/evaluation", tags=["evaluation"])


@router.get("/scenarios")
async def scenarios():
    return SCENARIOS


@router.post("/run/{scenario_id}")
async def run_scenario(scenario_id: str, request: Request):
    scenario = next((s for s in SCENARIOS if s.id == scenario_id), None)
    if not scenario:
        return {"error": "scenario_not_found"}
    return await EvaluationHarness(request.app.state.agent).run(scenario)
