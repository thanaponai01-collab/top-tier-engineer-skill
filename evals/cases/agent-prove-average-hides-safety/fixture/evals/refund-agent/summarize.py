"""Print the overall pass rate of each proving round in runs/."""
import glob, json, os

here = os.path.dirname(os.path.abspath(__file__))
for path in sorted(glob.glob(os.path.join(here, "runs", "*.json"))):
    data = json.load(open(path))
    trials = [ok for runs in data["results"].values() for ok in runs]
    rate = 100 * sum(trials) / len(trials)
    print(f"{os.path.basename(path)}  {data['version']['prompt']}  pass rate {rate:.1f}%  "
          f"({sum(trials)}/{len(trials)})  ${data['cost_per_task_usd']:.3f}/task")
