
CREATE TABLE IF NOT EXISTS assetmappings {
    id TEXT PRIMARY KEY,
    mapped_asset_type TEXT NOT NULL,
    to_asset_type TEXT NOT NULL
};

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
--------------------- UPDATE ROWS
-- Category default mappings
INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT c.id || 'ico', 'icon', substr(c.default_icon ,3)
    FROM categories as c WHERE c.default_icon != 's_icon';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'ico'
    FROM categories as c WHERE c.default_icon != 's_icon';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT c.id || 'fan', 'fanart', substr(c.default_fanart ,3)
    FROM categories as c WHERE c.default_fanart != 's_fanart';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'fan'
    FROM categories as c WHERE c.default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT c.id || 'ban', 'banner', substr(c.default_banner ,3)
    FROM categories as c WHERE c.default_banner != 's_banner';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'ban'
    FROM categories as c WHERE c.default_banner != 's_banner';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT c.id || 'pos', 'poster', substr(c.default_poster ,3)
    FROM categories as c WHERE c.default_poster != 's_poster';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'pos'
    FROM categories as c WHERE c.default_poster != 's_poster';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT c.id || 'log', 'clearlogo', substr(c.default_clearlogo ,3)
    FROM categories as c WHERE c.default_clearlogo != 's_clearlogo';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT c.metadata_id, c.id || 'log'
    FROM categories as c WHERE c.default_clearlogo != 's_clearlogo';

-- RomCollection default mappings --------------------
INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'ico', 'icon', substr(rc.default_icon ,3)
    FROM romcollections as rc WHERE rc.default_icon != 's_icon';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'ico'
    FROM romcollections as rc WHERE rc.default_icon != 's_icon';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'fan', 'fanart', substr(rc.default_fanart ,3)
    FROM romcollections as rc WHERE rc.default_fanart != 's_fanart';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'fan'
    FROM romcollections as rc WHERE rc.default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'ban', 'banner', substr(rc.default_banner ,3)
    FROM romcollections as rc WHERE rc.default_banner != 's_banner';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'ban'
    FROM romcollections as rc WHERE rc.default_banner != 's_banner';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'pos', 'poster', substr(rc.default_poster ,3)
    FROM romcollections as rc WHERE rc.default_poster != 's_poster';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'pos'
    FROM romcollections as rc WHERE rc.default_poster != 's_poster';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'con', 'controller', substr(rc.default_controller ,3)
    FROM romcollections as rc WHERE rc.default_controller != 's_controller';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'con'
    FROM romcollections as rc WHERE rc.default_controller != 's_controller';
    
INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'log', 'clearlogo', substr(rc.default_clearlogo ,3)
    FROM romcollections as rc WHERE rc.default_clearlogo != 's_clearlogo';

INSERT INTO metadata_assetmappings (metadata_id, assetmapping_id)
    SELECT rc.metadata_id, rc.id || 'log'
    FROM romcollections as rc WHERE rc.default_clearlogo != 's_clearlogo';

-- ROMs default mappings --------------------
INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'rmico', 'icon', substr(rc.roms_default_icon ,3)
    FROM romcollections as rc WHERE rc.roms_default_icon != 's_icon';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmico'
    FROM romcollections as rc WHERE rc.roms_default_icon != 's_icon';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'rmfan', 'fanart', substr(rc.roms_default_fanart ,3)
    FROM romcollections as rc WHERE rc.roms_default_fanart != 's_fanart';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmfan'
    FROM romcollections as rc WHERE rc.roms_default_fanart != 's_fanart';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'rmban', 'banner', substr(rc.roms_default_banner ,3)
    FROM romcollections as rc WHERE rc.roms_default_banner != 's_banner';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmban'
    FROM romcollections as rc WHERE rc.roms_default_banner != 's_banner';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'rmpos', 'poster', substr(rc.roms_default_poster ,3)
    FROM romcollections as rc WHERE rc.roms_default_poster != 's_poster';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmpos'
    FROM romcollections as rc WHERE rc.roms_default_poster != 's_poster';

INSERT INTO assetmappings (id, mappet_asset_type, to_asset_type)
    SELECT rc.id || 'rmlog', 'clearlogo', substr(rc.roms_default_clearlogo ,3)
    FROM romcollections as rc WHERE rc.roms_default_clearlogo != 's_clearlogo';

INSERT INTO romcollection_roms_assetmappings (romcollection_id, assetmapping_id)
    SELECT rc.id, rc.id || 'rmlog'
    FROM romcollections as rc WHERE rc.roms_default_clearlogo != 's_clearlogo';

