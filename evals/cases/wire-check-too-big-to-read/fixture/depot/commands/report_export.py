from depot import exporters, store
from depot.registry import command


@command("export")
def run(args):
    collection, fmt = args[0], args[1]
    print(exporters.get(fmt).render(store.load(collection)))
