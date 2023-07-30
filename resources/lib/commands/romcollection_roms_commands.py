# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection roms management)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import collections
import typing

from akl import constants
from akl.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, ROMsJsonFileRepository
from resources.lib.domain import ROM, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROMCollection ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMCOLLECTION_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    if romcollection_id is None:
        logger.warning('cmd_manage_roms(): No romcollection id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    has_roms = romcollection.has_roms()

    options = collections.OrderedDict()
    options['SET_ROMS_DEFAULT_ARTWORK'] = kodi.translate(42044)
    options['SET_ROMS_ASSET_DIRS'] = kodi.translate(42045)
    
    if romcollection.has_scanners(): 
        options['SCAN_ROMS'] = kodi.translate(42046)
        options['REMOVE_DEAD_ROMS'] = kodi.translate(42047)
        options['EDIT_ROMCOLLECTION_SCANNERS'] = kodi.translate(42048)
    else: options['ADD_SCANNER'] = kodi.translate(42049)
    
    options['IMPORT_ROMS'] = kodi.translate(42050)
    if has_roms:
        options['EXPORT_ROMS'] = kodi.translate(42051)
        options['SCRAPE_ROMS'] = kodi.translate(42052)
        options['DELETE_ROMS_NFO'] = kodi.translate(42053)
        options['CLEAR_ROMS'] = kodi.translate(42054)

    s = kodi.translate(41128).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args: del args['scraper_settings']
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)

# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        # --- Build Dialog.select() list ---
        default_assets_list = romcollection.get_ROM_mappable_asset_list()
        options = collections.OrderedDict()
        for default_asset_info in default_assets_list:
            # >> Label is the string 'Choose asset for XXXX (currently YYYYY)'
            mapped_asset_info = romcollection.get_ROM_asset_mapping(default_asset_info)
            # --- Append to list of ListItems ---
            options[default_asset_info] = kodi.translate(42055).format(
                kodi.translate(default_asset_info.name_id), 
                kodi.translate(mapped_asset_info.name_id))
        
        dialog = kodi.OrdDictionaryDialog()
        selected_asset_info = dialog.select(kodi.translate(41077).format("ROM"), options)
        
        if selected_asset_info is None:
            # >> Return to parent menu.
            logger.debug('Main selected NONE. Returning to parent menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return
        
        logger.debug('Main select() returned {0}'.format(selected_asset_info.name))    
        mapped_asset_info = romcollection.get_ROM_asset_mapping(selected_asset_info)
        mappable_asset_list = g_assetFactory.get_asset_list_by_IDs(constants.ROM_ASSET_ID_LIST, 'image')
        logger.debug(f'{selected_asset_info.name} currently is mapped to {mapped_asset_info.name}')
            
        # --- Create ListItems ---
        options = collections.OrderedDict()
        for mappable_asset_info in mappable_asset_list:
            # >> Label is the asset name (Icon, Fanart, etc.)
            options[mappable_asset_info] = kodi.translate(mappable_asset_info.name_id)

        dialog = kodi.OrdDictionaryDialog()
        dialog_title_str = kodi.translate(41078).format(romcollection.get_object_name(), 
                                                        kodi.translate(selected_asset_info.name_id))
        new_selected_asset_info = dialog.select(dialog_title_str, options, mapped_asset_info)
    
        if new_selected_asset_info is None:
            # >> Return to this method recursively to previous menu.
            logger.debug('Mapable selected NONE. Returning to previous menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return   
        
        logger.debug(f'Mapable selected {new_selected_asset_info.name}.')
        romcollection.set_mapped_ROM_asset(selected_asset_info, new_selected_asset_info)
        kodi.notify(kodi.translate(40983).format(
            romcollection.get_object_name(), 
            kodi.translate(selected_asset_info.name_id), 
            kodi.translate(new_selected_asset_info.name_id)
        ))
        
        repository.update_romcollection(romcollection)
        uow.commit()
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.async_cmd('SET_ROMS_DEFAULT_ARTWORK', {'romcollection_id': romcollection.get_id(), 'selected_asset': selected_asset_info.id})         

@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    list_items = collections.OrderedDict()
    assets = g_assetFactory.get_assets_for_type(constants.KIND_ASSET_ROM)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        root_path = romcollection.get_assets_root_path()
        root_path_str = root_path.getPath() if root_path else kodi.translate(41158)
        list_items[AssetInfo()] = kodi.translate(42083).format(root_path_str)
        for asset_info in assets:
            path = romcollection.get_asset_path(asset_info)
            if path:
                list_items[asset_info] = kodi.translate(42084).format(asset_info.plural, path.getPath())

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select(kodi.translate(41129), list_items)

        if selected_asset is None:
            AppMediator.sync_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return

        # rootpath?
        if selected_asset.id == '':
            dir_path = kodi.browse(type=0, text=kodi.translate(41159), preselected_path=root_path.getPath() if root_path else None)
            if not dir_path or (root_path is not None and dir_path == root_path.getPath()):  
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            
            root_path = io.FileName(dir_path)
            apply_to_all = kodi.dialog_yesno(kodi.translate(41062))
            romcollection.set_assets_root_path(root_path, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=apply_to_all)            
        else:
            selected_asset_path = romcollection.get_asset_path(selected_asset)
            dir_path = kodi.browse(type=0, text=kodi.translate(41160).format(selected_asset.plural), preselected_path=selected_asset_path.getPath())
            if not dir_path or dir_path == selected_asset_path.getPath():  
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            romcollection.set_asset_path(selected_asset, dir_path)
            
        repository.update_romcollection(romcollection)
        uow.commit()
                
    # >> Check for duplicate paths and warn user.
    AppMediator.async_cmd('CHECK_DUPLICATE_ASSET_DIRS', args)

    kodi.notify(kodi.translate(40984).format(selected_asset.name, dir_path))
    AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
    
@AppMediator.register('IMPORT_ROMS')
def cmd_import_roms(args):
    logger.debug('IMPORT_ROMS: cmd_import_roms() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    options = collections.OrderedDict()
    options['IMPORT_ROMS_NFO'] = kodi.translate(42056)
    options['IMPORT_ROMS_JSON'] = kodi.translate(42057)

    s = kodi.translate(41130).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('IMPORT_ROMS: cmd_import_roms() Selected None. Closing context menu')
        AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('IMPORT_ROMS: cmd_import_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)
    
# --- Import ROM metadata from NFO files ---
@AppMediator.register('IMPORT_ROMS_NFO')
def cmd_import_roms_nfo(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    # >> Load ROMs, iterate and import NFO files
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository            = ROMsRepository(uow)
        collection_repository = ROMCollectionRepository(uow)

        collection = collection_repository.find_romcollection(romcollection_id)
        roms = repository.find_roms_by_romcollection(collection)
    
        pDialog = kodi.ProgressDialog()
        pDialog.startProgress(kodi.translate(41153), num_steps=len(roms))
        num_read_NFO_files = 0

        step = 0
        for rom in roms:
            step = step + 1
            nfo_filepath = rom.get_nfo_file()
            pDialog.updateProgress(step)
            if rom.update_with_nfo_file(nfo_filepath, verbose = False):
                num_read_NFO_files += 1
                repository.update_rom(rom)
                
        # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
        pDialog.updateProgress(len(roms), kodi.translate(41154))
        uow.commit()
        pDialog.close()
        
    kodi.notify(kodi.translate(40985).format(num_read_NFO_files))
    AppMediator.async_cmd('IMPORT_ROMS', args)
    
# --- Import ROM metadata from json config file ---
@AppMediator.register('IMPORT_ROMS_JSON')
def cmd_import_roms_json(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    file_list = kodi.browse(text=kodi.translate(41155),mask='.json',multiple=True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository        = ROMsRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow) 
        
        romcollection       = romcollection_repository.find_romcollection(romcollection_id)
        existing_roms       = [*repository.find_roms_by_romcollection(romcollection)]
        existing_rom_ids    = map(lambda r: r.get_id(), existing_roms)
        existing_rom_names  = map(lambda r: r.get_name(), existing_roms)

        roms_to_insert:typing.List[ROM]  = []
        roms_to_update:typing.List[ROM]  = []

        # >> Process file by file
        for json_file in file_list:
            logger.debug('cmd_import_roms_json() Importing "{0}"'.format(json_file))
            import_FN = io.FileName(json_file)
            if not import_FN.exists(): continue

            json_file_repository  = ROMsJsonFileRepository(import_FN)
            imported_roms = json_file_repository.load_ROMs()
            logger.debug("cmd_import_roms_json() Loaded {} roms".format(len(imported_roms)))
    
            for imported_rom in imported_roms:
                if imported_rom.get_id() in existing_rom_ids:
                     # >> ROM exists (by id). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno(kodi.translate(41063).format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                elif imported_rom.get_name() in existing_rom_names:
                     # >> ROM exists (by name). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno(kodi.translate(41063).format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                else:
                    logger.debug('Add new ROM {}'.format(imported_rom.get_name()))
                    imported_rom.set_platform(romcollection.get_platform())
                    roms_to_insert.append(imported_rom)
                        
        for rom_to_insert in roms_to_insert:
            repository.insert_rom(rom_to_insert)
            romcollection_repository.add_rom_to_romcollection(romcollection.get_id(), rom_to_insert.get_id())

        for rom_to_update in roms_to_update:
            repository.update_rom(rom_to_update)
            
        uow.commit()

    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})  
    kodi.notify(kodi.translate(40978))

# --- Empty Launcher ROMs ---
@AppMediator.register('CLEAR_ROMS')
def cmd_clear_roms(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository   = ROMCollectionRepository(uow)
        roms_repository         = ROMsRepository(uow)
        
        romcollection = collection_repository.find_romcollection(romcollection_id)
        roms          = roms_repository.find_roms_by_romcollection(romcollection)
        
        # If collection is empty (no ROMs) do nothing
        num_roms = len([*roms])
        if num_roms == 0:
            kodi.dialog_OK(kodi.translate(41151))
            return

        # Confirm user wants to delete ROMs    
        ret = kodi.dialog_yesno(kodi.translate(41142).format(romcollection.get_name(), num_roms))
        if not ret:
            return

        # --- If there is a No-Intro XML DAT configured remove it ---
        # TODO fix
        # romcollection.reset_nointro_xmldata()

        # Confirm if the user wants to remove the ROMs also when linked to other collections.
        delete_completely = kodi.dialog_yesno(kodi.translate(41064))
        if not delete_completely: 
            collection_repository.remove_all_roms_in_launcher(romcollection_id)
        else:
            roms_repository.delete_roms_by_romcollection(romcollection_id)        
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})  
    kodi.notify(kodi.translate(40977))
