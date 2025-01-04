-- --------------------------------------
-- DROP OLD VIEWS
-- --------------------------------------

DROP VIEW vw_romcollection_launchers;

-- --------------------------------------
-- CREATE NEW VIEWS: fixing INNER JOIN launchers
-- --------------------------------------
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
    