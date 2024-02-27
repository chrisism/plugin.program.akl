-- --------------------------------------
-- CREATE NEW TABLES
-- --------------------------------------
CREATE TABLE IF NOT EXISTS sources(
    id TEXT PRIMARY KEY,
    name TEXT,
    platform TEXT,
    box_size TEXT,
    assets_path TEXT,
    last_scan_timestamp TIMESTAMP,
    akl_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (akl_addon_id) REFERENCES akl_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS collection_source_ruleset(
    ruleset_id TEXT PRIMARY KEY,
    source_id TEXT,
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

CREATE TABLE IF NOT EXISTS source_assetpaths(
    source_id TEXT,
    assetpaths_id TEXT,
    FOREIGN KEY (source_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetpaths_id) REFERENCES assetpaths (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS launchers(
    id TEXT PRIMARY KEY,
    name TEXT,
    akl_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (akl_addon_id) REFERENCES akl_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS source_launchers(
    source_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launcher (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
-- --------------------------------------
-- MIGRATE EXISTING DATA INTO NEW TABLES
-- --------------------------------------
INSERT INTO sources (id, name, platform, box_size, assets_path, akl_addon_id, settings)
    SELECT rcs.id, rc.name || ' (' || rcs.id || ')', rc.platform, rc.box_size, m.assets_path, rcs.akl_addon_id, rcs.settings
    FROM romcollection_scanners as rcs
        LEFT JOIN romcollections as rc ON rc.id = rcs.romcollection_id
        INNER JOIN metadata as m ON m.id = rc.metadata_id
        LEFT JOIN akl_addon as aa ON rcs.akl_addon_id = aa.id;

INSERT INTO collection_source_ruleset (ruleset_id, source_id, collection_id)
    SELECT rcs.id, rcs.id, rc.id
    FROM romcollection_scanners as rcs
        LEFT JOIN romcollections as rc ON rc.id = rcs.romcollection_id;

INSERT INTO source_assetpaths (source_id, assetpaths_id)
    SELECT ra.romcollection_id, ra.assetpaths_id
    FROM romcollection_assetpaths as ra;

INSERT INTO launchers (id, name, akl_addon_id, settings)
    SELECT rl.id, a.name || ' (' || rl.id || ')', a.id, rl.settings
    FROM rom_launchers AS rl
        INNER JOIN akl_addon AS a ON rl.akl_addon_id = a.id;

INSERT INTO launchers (id, name, akl_addon_id, settings)
    SELECT rcl.id, a.name || ' (' || rcl.id || ')', a.id, rcl.settings
    FROM romcollection_launchers AS rcl
        INNER JOIN akl_addon AS a ON rcl.akl_addon_id = a.id;

INSERT INTO source_launchers(source_id, launcher_id, is_default)
    SELECT rcl.romcollection_id, rcl.id, rcl.is_default
    FROM romcollection_launchers AS rcl;

-- --------------------------------------
-- ASSOCIATE ROMS WITH SOURCE INSTEAD OF SCANNER
-- AND ALTER LAUNCHER TABLES
-- --------------------------------------
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

ALTER TABLE roms RENAME TO _roms_old;
ALTER TABLE romcollection_launchers RENAME TO _romcollection_launchers_old;
ALTER TABLE rom_launchers RENAME TO _rom_launchers_old;
ALTER TABLE metadata RENAME TO _metadata_old;

CREATE TABLE IF NOT EXISTS metadata(
    id TEXT PRIMARY KEY, 
    year TEXT,
    genre TEXT,
    developer TEXT,
    rating INTEGER NULL,
    plot TEXT,
    extra TEXT,
    finished INTEGER DEFAULT 0
);

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
    FOREIGN KEY (scanned_by_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_launchers(
    romcollection_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launcher (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
CREATE TABLE IF NOT EXISTS rom_launchers(
    rom_id TEXT,

    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launcher (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

INSERT INTO metadata (id, year, genre, developer, rating, plot, extra, finished) 
SELECT id, year, genre, developer, rating, plot, extra, finished
 FROM _metadata_old;

INSERT INTO roms (
    id,name,num_of_players,num_of_players_online,esrb_rating,pegi_rating,nointro_status,pclone_status,cloneof,
    platform,box_size,rom_status,is_favourite, launch_count, last_launch_timestamp, metadata_id, scanned_by_id
) SELECT 
    id,name,num_of_players,num_of_players_online,esrb_rating,pegi_rating,nointro_status,pclone_status,cloneof,
    platform,box_size,rom_status,is_favourite, launch_count, last_launch_timestamp, metadata_id, scanned_by_id
 FROM _roms_old;

INSERT INTO romcollection_launchers(romcollection_id, launcher_id, is_default)
    SELECT rcl.romcollection_id, rcl.id, rcl.is_default
    FROM _romcollection_launchers_old AS rcl;

INSERT INTO rom_launchers(rom_id, launcher_id, is_default)
    SELECT rc.rom_id, rc.id, rc.is_default
    FROM _rom_launchers_old AS rc;

-- --------------------------------------
-- CLEANUP OLD TABLES
-- --------------------------------------
DROP TABLE romcollection_scanners;
DROP TABLE romcollection_assetpaths;
DROP TABLE _roms_old;
DROP TABLE _romcollection_launchers_old;
DROP TABLE _rom_launchers_old;

COMMIT;

PRAGMA foreign_keys=on;

-- --------------------------------------
-- CREATE NEW VIEWS / DROP OLD VIEWS
-- --------------------------------------
DROP VIEW vw_romcollection_scanners;
DROP VIEW vw_romcollection_asset_paths;
DROP VIEW vw_romcollections;
DROP VIEW vw_roms;
DROP VIEW vw_rom_assets;
DROP VIEW vw_rom_asset_paths;
DROP VIEW vw_rom_tags;
DROP VIEW vw_romcollection_launchers;
DROP VIEW vw_rom_launchers;
DROP VIEW vw_categories;

CREATE VIEW IF NOT EXISTS vw_sources AS SELECT 
    s.id AS id, 
    s.name AS name,
    s.platform AS platform,
    s.box_size AS box_size,
    s.assets_path AS assets_path,
    s.last_scan_timestamp AS last_scan_timestamp,
    s.settings AS settings,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    (SELECT COUNT(*) FROM roms AS rms WHERE rms.scanned_by_id = s.id) as num_roms
FROM sources AS s
    INNER JOIN akl_addon AS a ON s.akl_addon_id = a.id;

CREATE VIEW IF NOT EXISTS vw_source_asset_paths AS SELECT
    a.id as id,
    s.id as source_id,
    a.path,
    a.asset_type
FROM assetpaths AS a
 INNER JOIN source_assetpaths AS sa ON a.id = sa.assetpaths_id 
 INNER JOIN sources AS s ON sa.source_id = s.id;

CREATE VIEW IF NOT EXISTS vw_categories AS SELECT 
    c.id AS id, 
    c.parent_id AS parent_id,
    c.metadata_id,
    c.name AS m_name,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.extra AS extra,
    m.finished AS finished,
    (SELECT COUNT(*) FROM categories AS sc WHERE sc.parent_id = c.id) AS num_categories,
    (SELECT COUNT(*) FROM romcollections AS sr WHERE sr.parent_id = c.id) AS num_collections
FROM categories AS c 
    INNER JOIN metadata AS m ON c.metadata_id = m.id;

CREATE VIEW IF NOT EXISTS vw_romcollections AS SELECT 
    r.id AS id, 
    r.parent_id AS parent_id,
    r.metadata_id,
    r.name AS m_name,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.extra AS extra,
    m.finished AS finished,
    r.platform AS platform,
    r.box_size AS box_size,
    (SELECT COUNT(*) FROM roms AS rms INNER JOIN roms_in_romcollection AS rrs ON rms.id = rrs.rom_id AND rrs.romcollection_id = r.id) as num_roms
FROM romcollections AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;
    
CREATE VIEW IF NOT EXISTS vw_roms AS SELECT 
    r.id AS id, 
    r.metadata_id,
    r.name AS m_name,
    r.num_of_players AS nplayers,
    r.num_of_players_online AS nplayers_online,
    r.esrb_rating AS esrb,
    r.pegi_rating AS pegi,
    r.nointro_status AS nointro_status,
    r.pclone_status AS pclone_status,
    r.cloneof AS cloneof,
    r.platform AS platform,
    r.box_size AS box_size,
    r.scanned_by_id AS scanned_by_id,
    m.year AS m_year, 
    m.genre AS m_genre,
    m.developer AS m_developer,
    m.rating AS m_rating,
    m.plot AS m_plot,
    m.extra AS extra,
    m.finished,
    r.rom_status,
    r.is_favourite,
    r.launch_count,
    r.last_launch_timestamp,
    (
        SELECT group_concat(t.tag) AS rom_tags
        FROM tags AS t 
        INNER JOIN metatags AS mt ON t.id = mt.tag_id
        WHERE mt.metadata_id = r.metadata_id
        GROUP BY mt.metadata_id
    ) AS rom_tags
FROM roms AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;

CREATE VIEW IF NOT EXISTS vw_rom_assets AS SELECT
    a.id as id,
    r.id as rom_id, 
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN rom_assets AS ra ON a.id = ra.asset_id 
 INNER JOIN roms AS r ON ra.rom_id = r.id;

CREATE VIEW IF NOT EXISTS vw_rom_asset_paths AS SELECT
    a.id as id,
    r.id as rom_id, 
    a.path,
    a.asset_type
FROM assetpaths AS a
 INNER JOIN rom_assetpaths AS ra ON a.id = ra.assetpaths_id 
 INNER JOIN roms AS r ON ra.rom_id = r.id;

CREATE VIEW IF NOT EXISTS vw_rom_tags AS SELECT
    t.id as id,
    r.id as rom_id, 
    t.tag
FROM tags AS t
 INNER JOIN metatags AS mt ON t.id = mt.tag_id
 INNER JOIN roms AS r ON mt.metadata_id = r.metadata_id;
 
CREATE VIEW IF NOT EXISTS vw_romcollection_launchers AS SELECT
    l.id AS id,
    l.name AS name,
    rcl.romcollection_id,
    a.id AS associated_addon_id,
    a.name,
    a.addon_id,
    a.version,
    a.addon_type,
    a.extra_settings,
    l.settings,
    rcl.is_default
FROM romcollection_launchers AS rcl
    INNER JOIN launchers AS l ON rcl.launcher_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;
    
CREATE VIEW IF NOT EXISTS vw_source_launchers AS SELECT
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
    INNER JOIN launchers AS l ON sl.source_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;

CREATE VIEW IF NOT EXISTS vw_rom_launchers AS SELECT
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
    INNER JOIN launchers AS l ON rl.rom_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;