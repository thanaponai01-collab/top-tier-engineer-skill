import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from history import build, FINAL

build(sys.argv[1], [
    {'message': 'Start export acceptance', 'date': '2026-10-09T10:00:00',
     'files': {'app.py': 'def export_allowed(rows):\n    return rows >= 0\n'}},
    {'message': 'Bound exports after memory pressure\n\n1000 rows caps allocations on small customer machines.',
     'date': '2026-10-10T10:00:00', 'files': {'app.py': FINAL}},
], final_message='Record revised owner limit and pending boundary work',
   final_date='2026-10-12T10:00:00')
