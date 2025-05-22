CREATE TABLE IF NOT EXISTS kv_store (
  key          TEXT      PRIMARY KEY,
  value        TEXT      NOT NULL,
  last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
