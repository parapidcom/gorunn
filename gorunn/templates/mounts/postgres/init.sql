DO $$
DECLARE
  db RECORD;
BEGIN
  FOR db IN SELECT datname FROM pg_database WHERE datistemplate = false LOOP
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %L', db.datname, current_user);
  END LOOP;
END $$;
