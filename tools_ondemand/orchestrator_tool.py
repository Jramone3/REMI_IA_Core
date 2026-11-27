def context_memory(query: str, memory_fn=None) -> str:
    if callable(memory_fn):
        return str(memory_fn(query))[:1200]
    return "Sin función de memoria externa conectada."

def task_orchestrator(steps: list, runner_fn) -> list:
    results = []
    if not isinstance(steps, list) or not callable(runner_fn):
        return results
    for step in steps[:6]:
        res = runner_fn(step)
        results.append({"step": step.get("name", "step"), "result": str(res)[:800]})
        if step.get("stop_on_error") and "ERROR" in str(res).upper():
            break
    return results
