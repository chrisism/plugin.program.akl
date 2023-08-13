
CREATE TABLE IF NOT EXISTS library_source(
    id TEXT PRIMARY KEY,
    name TEXT,
    akl_addon_id TEXT,
    settings TEXT,
    FOREIGN KEY (akl_addon_id) REFERENCES akl_addon (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
