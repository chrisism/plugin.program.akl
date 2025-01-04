-------------------------------------------------
-- MAIN ENTITIES
-------------------------------------------------
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

CREATE TABLE IF NOT EXISTS akl_addon(
    id TEXT PRIMARY KEY, 
    name TEXT,
    addon_id TEXT,
    version TEXT,
    addon_type TEXT,
    extra_settings TEXT
);

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

CREATE TABLE IF NOT EXISTS categories(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    parent_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollections(
    id TEXT PRIMARY KEY, 
    name TEXT NOT NULL,
    platform TEXT,
    box_size TEXT,
    parent_id TEXT NULL,
    metadata_id TEXT,
    FOREIGN KEY (parent_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
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
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_id TEXT,
    scanned_by_id TEXT NULL,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (scanned_by_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS tags(
    id TEXT PRIMARY KEY, 
    tag TEXT
);

CREATE TABLE IF NOT EXISTS assets(
    id TEXT PRIMARY KEY,
    filepath TEXT NOT NULL,
    asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assetpaths(
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assetmappings (
    id TEXT PRIMARY KEY,
    mapped_asset_type TEXT NOT NULL,
    to_asset_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS launchers(
    id TEXT PRIMARY KEY,
    name TEXT,
    akl_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (akl_addon_id) REFERENCES akl_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

-------------------------------------------------
-- SECONDARY ENTITIES
-------------------------------------------------
CREATE TABLE IF NOT EXISTS scanned_roms_data(
    rom_id TEXT,
    data_key TEXT NOT NULL,
    data_value TEXT NULL,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
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

-------------------------------------------------
-- ENTITY JOIN TABLES
-------------------------------------------------
CREATE TABLE IF NOT EXISTS metatags(
    metadata_id TEXT,
    tag_id TEXT,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (tag_id) REFERENCES tags (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS roms_in_romcollection(
    rom_id TEXT,
    romcollection_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS roms_in_category(
    rom_id TEXT,
    category_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (category_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_launchers(
    romcollection_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS source_launchers(
    source_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS rom_launchers(
    rom_id TEXT,
    launcher_id TEXT,
    is_default INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (launcher_id) REFERENCES launchers (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

-------------------------------------------------
-- ASSETS JOIN TABLES
-------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata_assetmappings(
    metadata_id TEXT,
    assetmapping_id TEXT,
    FOREIGN KEY (metadata_id) REFERENCES metadata (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetmapping_id) REFERENCES assetmappings (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_roms_assetmappings(
    romcollection_id TEXT,
    assetmapping_id TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetmapping_id) REFERENCES assetmappings (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS category_assets(
    category_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS romcollection_assets(
    romcollection_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (romcollection_id) REFERENCES romcollections (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS rom_assets(
    rom_id TEXT,
    asset_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (asset_id) REFERENCES assets (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS rom_assetpaths(
    rom_id TEXT,
    assetpaths_id TEXT,
    FOREIGN KEY (rom_id) REFERENCES roms (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetpaths_id) REFERENCES assetpaths (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS source_assetpaths(
    source_id TEXT,
    assetpaths_id TEXT,
    FOREIGN KEY (source_id) REFERENCES sources (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION,
    FOREIGN KEY (assetpaths_id) REFERENCES assetpaths (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
-------------------------------------------------
-- VIEWS
-------------------------------------------------
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
    (SELECT COUNT(*) FROM romcollections AS sr WHERE sr.parent_id = c.id) AS num_collections,
    (SELECT COUNT(*) FROM roms AS rms INNER JOIN roms_in_category AS rc ON rms.id = rc.rom_id AND rc.category_id = c.id) as num_roms,
    (SELECT MAX(rms.updated_on) FROM roms AS rms INNER JOIN roms_in_category AS rc ON rms.id = rc.rom_id AND rc.category_id = c.id) as last_change_on
FROM categories AS c 
    INNER JOIN metadata AS m ON c.metadata_id = m.id;

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
    (SELECT COUNT(*) FROM roms AS rms WHERE rms.scanned_by_id = s.id) as num_roms,
    (SELECT MAX(rms.updated_on) FROM roms AS rms WHERE rms.scanned_by_id = s.id) as last_change_on
FROM sources AS s
    INNER JOIN akl_addon AS a ON s.akl_addon_id = a.id;

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
    (SELECT COUNT(*) FROM roms AS rms INNER JOIN roms_in_romcollection AS rrs ON rms.id = rrs.rom_id AND rrs.romcollection_id = r.id) as num_roms,
    (SELECT MAX(rms.updated_on) FROM roms AS rms INNER JOIN roms_in_romcollection AS rrs ON rms.id = rrs.rom_id AND rrs.romcollection_id = r.id) as last_change_on
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
    (SELECT COUNT(*) FROM roms_in_romcollection AS rr WHERE rr.rom_id = r.id) AS collections_count,
    r.is_favourite,
    r.launch_count,
    r.last_launch_timestamp,
    r.created_on,
    r.updated_on,
    (
        SELECT group_concat(t.tag) AS rom_tags
        FROM tags AS t 
        INNER JOIN metatags AS mt ON t.id = mt.tag_id
        WHERE mt.metadata_id = r.metadata_id
        GROUP BY mt.metadata_id
    ) AS rom_tags
FROM roms AS r 
    INNER JOIN metadata AS m ON r.metadata_id = m.id;

CREATE VIEW IF NOT EXISTS vw_category_assets AS SELECT
    a.id as id,
    c.id as category_id,
    c.parent_id,
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN category_assets AS ca ON a.id = ca.asset_id 
 INNER JOIN categories AS c ON ca.category_id = c.id;

CREATE VIEW IF NOT EXISTS vw_romcollection_assets AS SELECT
    a.id as id,
    r.id as romcollection_id,
    r.parent_id,
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN romcollection_assets AS ra ON a.id = ra.asset_id 
 INNER JOIN romcollections AS r ON ra.romcollection_id = r.id;

CREATE VIEW IF NOT EXISTS vw_rom_assets AS SELECT
    a.id as id,
    r.id as rom_id, 
    a.filepath,
    a.asset_type
FROM assets AS a
 INNER JOIN rom_assets AS ra ON a.id = ra.asset_id 
 INNER JOIN roms AS r ON ra.rom_id = r.id;

CREATE VIEW IF NOT EXISTS vw_source_asset_paths AS SELECT
    a.id as id,
    s.id as source_id,
    a.path,
    a.asset_type
FROM assetpaths AS a
 INNER JOIN source_assetpaths AS sa ON a.id = sa.assetpaths_id 
 INNER JOIN sources AS s ON sa.source_id = s.id;

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
    INNER JOIN launchers AS l ON sl.launcher_id = l.id
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
    INNER JOIN launchers AS l ON rl.launcher_id = l.id
    INNER JOIN akl_addon AS a ON l.akl_addon_id = a.id;

CREATE TABLE IF NOT EXISTS akl_version(
    app TEXT, 
    version TEXT
);

CREATE TABLE IF NOT EXISTS akl_migrations(
    migration_file TEXT UNIQUE, 
    applied_version TEXT,
    execution_date TIMESTAMP,
    applied INTEGER DEFAULT 0 
);

-- STATIC VALUES
INSERT INTO akl_addon (id, name, addon_id, version, addon_type)
    VALUES ('856f1cd76f2148aba7953f20f10ec11d', 'Retroplayer', 'retroplayer_launcher_app', '1.0', 'LAUNCHER');

INSERT INTO tags (id, tag) VALUES 
    ('2e1f3086c96b44d2a81f5c08876b4ef6', 'co-op'),
    ('de7bfaa72e924cd9a54ab5d225367b05', 'free-for-all'),
    ('4f64dabdb0f5430f94eca529d6049a13', 'turnbased'),
    ('1c67d7a0cccb47dfb1b36839a4bb1c1f', '4k'),
    ('ccd62da94f7a4bf4ba593670329c2690', '720'),
    ('bf62ca2ffb0347559b1a52ec70b0b189', '1080');

INSERT INTO akl_migrations (migration_file, applied_version, execution_date, applied)
     VALUES
     ('1.2.0.sql','1.4.0',CURRENT_TIMESTAMP,1),
     ('1.4.0_001.sql','1.4.0',CURRENT_TIMESTAMP,1),
     ('1.4.0_002.sql','1.4.0',CURRENT_TIMESTAMP,1),
     ('1.4.0_003.sql','1.4.0',CURRENT_TIMESTAMP,1),
     ('1.5.0_001.sql','1.5.0',CURRENT_TIMESTAMP,1),
     ('1.5.0_002.sql','1.5.0',CURRENT_TIMESTAMP,1),
     ('1.5.0_003.sql','1.5.0',CURRENT_TIMESTAMP,1),
     ('1.5.0_004.sql','1.5.0',CURRENT_TIMESTAMP,1),
     ('1.5.2.sql','1.5.2',CURRENT_TIMESTAMP,1);