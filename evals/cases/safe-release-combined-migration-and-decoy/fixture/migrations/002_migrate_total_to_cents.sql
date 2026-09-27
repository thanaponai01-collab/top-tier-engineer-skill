-- Move `total` (dollars, float) to `total_cents` (integer) in one shot.
ALTER TABLE orders ADD COLUMN total_cents INTEGER;
UPDATE orders SET total_cents = CAST(ROUND(total * 100) AS INTEGER);
ALTER TABLE orders DROP COLUMN total;
