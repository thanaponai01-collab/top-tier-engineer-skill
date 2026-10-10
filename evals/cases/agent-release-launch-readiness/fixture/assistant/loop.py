"""The agent loop: one customer message in, tool calls, one reply out."""
from . import settings, runlog
from .llm import call_model
from .tools import TOOLS


class StepCapHit(Exception):
    pass


def handle(message, customer):
    if not settings.ENABLED:
        return "The assistant is unavailable right now; a person will reply."
    prompt = open(settings.prompt_path()).read()
    history = [{"role": "user", "content": message}]
    spent = 0.0
    for step in range(settings.CONFIG["max_steps"]):
        reply, cost = call_model(settings.CONFIG["model"], prompt, history)
        spent += cost
        if spent > settings.CONFIG["max_cost_per_run_usd"]:
            runlog.write(customer, message, history, "stopped: cost cap")
            return "Handing you to a person."
        if reply.tool is None:
            runlog.write(customer, message, history, reply.text)
            return reply.text
        result = TOOLS[reply.tool](**reply.args)
        history.append({"role": "tool", "name": reply.tool, "content": result})
    runlog.write(customer, message, history, "stopped: step cap")
    raise StepCapHit(f"{settings.CONFIG['max_steps']} steps")
