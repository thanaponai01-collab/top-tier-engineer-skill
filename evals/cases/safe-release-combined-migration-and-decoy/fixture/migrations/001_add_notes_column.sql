-- Purely additive: a new nullable column, no backfill needed, nothing reads it yet.
ALTER TABLE orders ADD COLUMN notes TEXT;
