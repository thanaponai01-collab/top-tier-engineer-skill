-- Phone numbers move out of users into their own table, so a user can have
-- a verified number separate from their account row.
CREATE TABLE contacts (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    phone TEXT NOT NULL
);
ALTER TABLE users DROP COLUMN phone;
