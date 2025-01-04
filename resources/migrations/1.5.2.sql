-- --------------------------------------
-- DROP OLD VIEWS
-- --------------------------------------

DROP VIEW vw_source_launchers;
DROP VIEW vw_rom_launchers;

-- --------------------------------------
-- FIX TABLES DEFINITIONS: fixing FOREIGN KEY (launcher_id) REFERENCES launchers
-- --------------------------------------
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

ALTER TABLE romcollection_launchers RENAME TO _romcollection_launchers_old;
ALTER TABLE source_launchers RENAME TO _source_launchers_old;
ALTER TABLE rom_launchers RENAME TO _rom_launchers_old;

CREATE TABLE romcollection_launchers(
    romcollection_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE source_launchers(
    source_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE rom_launchers(
    rom_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

-- --------------------------------------
-- MIGRATE EXISTING DATA INTO NEW TABLES
-- --------------------------------------
INSERT INTO romcollection_launchers (romcollection_id, launcher_id, is_default)
    SELECT romcollection_id, launcher_id, is_default
    FROM _romcollection_launchers_old;

INSERT INTO source_launchers (source_id, launcher_id, is_default)
    SELECT source_id, launcher_id, is_default
    FROM _source_launchers_old;

INSERT INTO rom_launchers(rom_id, launcher_id, is_default)
    SELECT rom_id, launcher_id, is_default
    FROM _rom_launchers_old;

-- --------------------------------------
-- CLEANUP OLD TABLES
-- --------------------------------------
DROP TABLE _romcollection_launchers_old;
DROP TABLE _source_launchers_old;
DROP TABLE _rom_launchers_old;

COMMIT;
PRAGMA foreign_keys=on;

-- --------------------------------------
-- CREATE NEW VIEWS: fixing INNER JOIN launchers AS l ON sl.launcher_id = l.id
-- --------------------------------------
CREATE VIEW vw_source_launchers AS SELECT
    l.id AS id,
    l.name AS name,
    sl.source_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    l.settings,
    sl.is_default
FROM source_launchers AS sl
    INNER JOIN launchers AS l ON sl.launcher_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;

CREATE VIEW vw_rom_launchers AS SELECT
    l.id AS id,
    l.name AS name,
    rl.rom_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    l.settings,
    rl.is_default
FROM rom_launchers AS rl
    INNER JOIN launchers AS l ON rl.launcher_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;
