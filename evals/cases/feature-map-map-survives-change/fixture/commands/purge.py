import os

import store


def run(store_, args):
    if not args.yes:
        print("refusing without --yes")
        return 1
    # audit trail: every purge leaves a line next to the notes it wiped
    with open(os.path.join(os.path.dirname(store.PATH), "purge.log"), "a", encoding="utf-8") as fh:
        fh.write("purged all notes\n")
    store_.save([])
    print("all notes deleted")
    return 0
