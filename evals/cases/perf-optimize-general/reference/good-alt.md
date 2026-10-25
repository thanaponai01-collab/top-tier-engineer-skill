Profiled the report with cProfile. Baseline 1.5 s.

Two causes. First, regions re-reads its CSV on each call: tax_rate is called once per order, so
the file is opened 12,000 times. I load it once into a dict. Second, dedupe keeps seen ids in a
list, which is O(n²); switched to a set, keeping the first row for each order_id.

After: 0.1 s on the export, and about 0.5 s on a 10x copy I generated. The output diff against the
old run is empty. layout.table is not a cost despite its comment.
