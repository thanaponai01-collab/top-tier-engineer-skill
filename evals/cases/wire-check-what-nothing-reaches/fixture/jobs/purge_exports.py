import glob
import os


def run():
    for f in glob.glob("export-*.csv"):
        os.remove(f)
