"""Run `python -m unittest ...` with the same arguments, timing every test; times go to $DIET_TIMES as JSON."""
import json, os, sys, time, unittest

TIMES = {}


class Result(unittest.TextTestResult):
    def startTest(self, test):
        self._diet_t0 = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        TIMES[test.id()] = TIMES.get(test.id(), 0.0) + time.perf_counter() - self._diet_t0
        super().stopTest(test)


class Runner(unittest.TextTestRunner):
    resultclass = Result


def main():
    sys.path[0] = os.getcwd()  # as `python -m unittest` does, not this script's folder
    prog = unittest.main(module=None, argv=["python -m unittest"] + sys.argv[1:], testRunner=Runner, exit=False)
    out = os.environ.get("DIET_TIMES")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(TIMES, fh)
    sys.exit(0 if prog.result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
