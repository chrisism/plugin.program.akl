-- --------------------------------------
-- Update Addon settings for default plugins
-- --------------------------------------

UPDATE akl_addon
    SET version = '1.6' WHERE addon_id = 'script.akl.defaults';

UPDATE akl_addon
    SET name = 'Application/Emulator Launcher' 
    WHERE addon_id = 'script.akl.defaults' 
        AND addon_type = 'LAUNCHER';