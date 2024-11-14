DO $$
DECLARE
  db RECORD;
BEGIN
  FOR db IN SELECT datname FROM pg_database WHERE datistemplate = false LOOP
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', db.datname, current_user);
  END LOOP;
END $$;

CREATE SCHEMA IF NOT EXISTS AUTHORIZATION current_user;
