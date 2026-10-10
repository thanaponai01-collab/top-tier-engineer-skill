"""Score an agent against tasks.jsonl.  Usage: python evals/triage/grade.py [module]"""
import importlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
QUEUES = {"billing", "shipping", "account", "returns", "escalate"}


def ok(out, task):
    # the agent must answer with a known queue
    return isinstance(out, dict) and out.get("queue") in QUEUES


def main():
    agent = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "triage_agent")
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl")) if l.strip()]
    passed = sum(ok(agent.triage(t["ticket"]), t) for t in tasks)
    print(f"{passed}/{len(tasks)} passed")
    return 0 if passed == len(tasks) else 1


if __name__ == "__main__":
    sys.exit(main())
