-- --------------------------------------
-- CREATE NEW TABLES
-- --------------------------------------
CREATE TABLE IF NOT EXISTS libraries(
    id TEXT PRIMARY KEY,
    library_name TEXT,
    akl_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (akl_addon_id) REFERENCES akl_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS collection_library_ruleset(
    ruleset_id TEXT PRIMARY KEY,
    library_id TEXT,
    collection_id TEXT,
    set_operator INTEGER DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS import_rule(
    rule_id TEXT PRIMARY KEY,
    ruleset_id TEXT,
    property TEXT,
    value TEXT,
    operator INTEGER DEFAULT 1 NOT NULL
);

-- --------------------------------------
-- MIGRATE EXISTING DATA INTO NEW TABLES
-- --------------------------------------
INSERT INTO libraries (id, library_name, akl_addon_id, settings)
    SELECT rcs.id, rc.name || ' ' || aa.name || ' (' || rcs.id || ')' , rcs.akl_addon_id, rcs.settings
    FROM romcollection_scanners as rcs
        LEFT JOIN romcollections as rc ON rc.id = rcs.romcollection_id
        LEFT JOIN akl_addon as aa ON rc.akl_addon_id = aa.id;

INSERT INTO collection_library_ruleset (ruleset_id, library_id, collection_id)
    SELECT rcs.id, rcs.id, rc.id
    FROM romcollection_scanners as rcs
        LEFT JOIN romcollections as rc ON rc.id = rcs.romcollection_id;

-- --------------------------------------
-- ASSOCIATE ROMS WITH LIBRARY INSTEAD OF SCANNER
-- --------------------------------------
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

ALTER TABLE roms RENAME TO _roms_old;

CREATE TABLE IF NOT EXISTS roms(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    num_of_players INTEGER DEFAULT 1 NOT NULL,
    num_of_players_online INTEGER DEFAULT 0 NOT NULL,
    esrb_rating TEXT,
    pegi_rating TEXT,
    nointro_status TEXT, 
    pclone_status TEXT,
    cloneof TEXT,
    platform TEXT,
    box_size TEXT,
    rom_status TEXT,
    is_favourite INTEGER DEFAULT 0 NOT NULL,
    launch_count INTEGER DEFAULT 0 NOT NULL,
    last_launch_timestamp TIMESTAMP,
    metadata_id TEXT,
    scanned_by_id TEXT NULL,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (scanned_by_id) REFERENCES libraries (id) 
        ON DELETE SET NULL ON UPDATE NO ACTION
);

INSERT INTO roms SELECT * FROM _roms_old;

-- --------------------------------------
-- CLEANUP OLD TABLES
-- --------------------------------------
DROP TABLE romcollection_scanners;
DROP TABLE _roms_old;

COMMIT;

PRAGMA foreign_keys=on;

-- --------------------------------------
-- CREATE NEW VIEWS
-- --------------------------------------
DROP VIEW vw_romcollection_scanners;
CREATE VIEW IF NOT EXISTS vw_libraries AS SELECT
    s.id AS id,
    s.romcollection_id,
    a.id AS associated_addon_id,
    s.library_name,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    s.settings
FROM libraries AS s
    INNER JOIN akl_addon AS a ON s.akl_addon_id = a.id;
