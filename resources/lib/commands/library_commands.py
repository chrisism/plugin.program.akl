# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (library roms management)
#
# Copyright (c) Chrisism <crizizz@gmail.com>
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

import xbmcgui

from akl import constants, platforms
from akl.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import UnitOfWork, LibrariesRepository, ROMsRepository, AelAddonRepository
from resources.lib.domain import Library, AelAddon, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)


# --- Main menu commands ---
@AppMediator.register('ADD_LIBRARY')
def cmd_add_library(args):
    logger.debug('cmd_add_library() BEGIN')
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        library_repository = LibrariesRepository(uow)
        
        addons = addon_repository.find_all_scanner_addons()
        for addon in addons:
            options[addon] = addon.get_name()
    
        s = kodi.translate(41107)
        selected_option: AelAddon = kodi.OrdDictionaryDialog().select(s, options)

        if selected_option is None:
            # >> Exits context menu
            logger.debug('ADD_LIBRARY: cmd_add_library() Selected None. Closing context menu')
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('ADD_LIBRARY: cmd_add_library() Selected {}'.format(selected_option.get_id()))
    
        lib_name = kodi.dialog_keyboard(kodi.translate(41166))
        library = Library(None, selected_option)
        library.set_name(lib_name)
        
        library_repository.insert_library(library)
        uow.commit()
        
        kodi.notify(kodi.translate(40980))
        kodi.run_script(
            selected_option.get_addon_id(),
            library.get_configure_command())


@AppMediator.register('EDIT_LIBRARY')
def cmd_edit_library(args):
    logger.debug('EDIT_LIBRARY: cmd_edit_library() BEGIN')
    library_id: str = args['library_id'] if 'library_id' in args else None
    
    if library_id is None:
        logger.warning('cmd_edit_library(): No library_id id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)

    options = collections.OrderedDict()
    options['LIBRARY_EDIT_TITLE'] = kodi.translate(40863).format(library.get_name())
    options['LIBRARY_EDIT_PLATFORM'] = kodi.translate(40864).format(library.get_platform())
    options['LIBRARY_EDIT_SCANNER'] = kodi.translate(42081)
    if library.has_launchers():
        options['EDIT_LIBRARY_LAUNCHERS'] = kodi.translate(42016)
    else:
        options['ADD_LIBRARY_LAUNCHER'] = kodi.translate(42026)
    options['LIBRARY_MANAGE_ROMS'] = kodi.translate(42039)
    options['DELETE_LIBRARY'] = kodi.translate(42085)

    s = kodi.translate(41167).format(library.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_LIBRARY: cmd_edit_library() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_LIBRARY: cmd_edit_library() Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('LIBRARY_EDIT_TITLE')
def cmd_library_title(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)
        
        s = kodi.translate(41137).format(
            kodi.translate(constants.OBJ_LIBRARY),
            library.get_name(),
            kodi.translate(40812))
        new_value = kodi.dialog_keyboard(s, library.get_name())
        if new_value is not None and library.get_name() != new_value:
            library.set_name(new_value)
            kodi.notify(kodi.translate(40986).format(
                kodi.translate(constants.OBJ_LIBRARY),
                kodi.translate(40812),
                new_value))
        
            repository.update_library(library)
            uow.commit()
            AppMediator.async_cmd('RENDER_LIBRARY_VIEW', {'library_id': library_id})
        else:
            kodi.notify(kodi.translate(40987).format(
                kodi.translate(constants.OBJ_LIBRARY),
                kodi.translate(40812)))
        
    AppMediator.sync_cmd('EDIT_LIBRARY', args)


@AppMediator.register('LIBRARY_EDIT_PLATFORM')
def cmd_library_metadata_platform(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)
    
        if editors.edit_field_by_list(library, kodi.translate(40807), platforms.AKL_platform_list,
                                      library.get_platform, library.set_platform):
            repository.update_library(library)
            update_roms_too = kodi.dialog_yesno(kodi.translate(40982))
            
            if update_roms_too:
                roms_repository = ROMsRepository(uow)
                roms_to_update = roms_repository.find_roms_by_library(library)
                platform_to_apply = library.get_platform()
                for rom in roms_to_update:
                    rom.set_platform(platform_to_apply)
                    roms_repository.update_rom(rom)

            uow.commit()
            AppMediator.async_cmd('RENDER_LIBRARY_VIEW', {'library_id': library_id})
    AppMediator.sync_cmd('EDIT_LIBRARY', args)


@AppMediator.register('LIBRARY_EDIT_SCANNER')
def cmd_edit_library_scanner(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)
     
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        library.addon.get_addon_id(),
        library.get_configure_command())
       

@AppMediator.register('DELETE_LIBRARY')
def cmd_library_delete(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)
        library_name = library.get_name()
        collection_ids = repository.find_romcollection_ids_by_library(library_id)
        
        if library.num_roms() > 0:
            question = kodi.translate(41169).format(library_name, library.num_roms()) + \
                kodi.translate(41066).format(library_name)
        else:
            question = kodi.translate(41066).format(library_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret:
            return
            
        logger.info(f'Deleting library "{library_name}" ID {library.get_id()}')
        repository.delete_library(library.get_id())
        uow.commit()
        
    kodi.notify(kodi.translate(41170).format(library_name))
    for collection_id in collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
    AppMediator.async_cmd('CLEANUP_VIEWS')


# -------------------------------------------------------------------------------------------------
# Library ROM management.
# -------------------------------------------------------------------------------------------------
# --- Submenu menu command ---
@AppMediator.register('LIBRARY_MANAGE_ROMS')
def cmd_manage_library_roms(args):
    logger.debug('LIBRARY_MANAGE_ROMS: cmd_manage_library_roms() SHOW MENU')
    library_id: str = args['library_id'] if 'library_id' in args else None
    
    if library_id is None:
        logger.warning('cmd_manage_library_roms(): No library id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)

    options = collections.OrderedDict()
    options['SET_ROMS_ASSET_DIRS'] = kodi.translate(42045)
    options['SCAN_ROMS'] = kodi.translate(42046)
    options['REMOVE_DEAD_ROMS'] = kodi.translate(42047)
    options['EXPORT_ROMS'] = kodi.translate(42051)
    options['SCRAPE_LIBRARY_ROMS'] = kodi.translate(42052)
    options['DELETE_ROMS_NFO'] = kodi.translate(42053)
    options['CLEAR_LIBRARY_ROMS'] = kodi.translate(42080)

    s = kodi.translate(41161).format(library.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('LIBRARY_MANAGE_ROMS: cmd_manage_library_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args:
            del args['scraper_settings']
        AppMediator.async_cmd('EDIT_LIBRARY', args)
        return
    
    logger.debug(f'LIBRARY_MANAGE_ROMS: cmd_manage_library_roms() Selected {selected_option}')
    AppMediator.async_cmd(selected_option, args)


@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    
    list_items = collections.OrderedDict()
    assets = g_assetFactory.get_assets_for_type(constants.KIND_ASSET_ROM)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LibrariesRepository(uow)
        library = repository.find(library_id)
        
        root_path = library.get_assets_root_path()
        root_path_str = root_path.getPath() if root_path else kodi.translate(41158)
        
        gui_listitem = xbmcgui.ListItem(label=kodi.translate(42083), label2=root_path_str)
        gui_listitem.setArt({'icon': 'DefaultFolder.png'})
        list_items[AssetInfo()] = gui_listitem
        for asset_info in assets:
            path = library.get_asset_path(asset_info)
            if path:
                gui_listitem = xbmcgui.ListItem(label=kodi.translate(42084).format(asset_info.plural), label2=path.getPath())
                gui_listitem.setArt({'icon': 'DefaultFolder.png'})
                list_items[asset_info] = gui_listitem

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select(kodi.translate(41129), list_items, use_details=True)

        if selected_asset is None:
            AppMediator.sync_cmd('LIBRARY_MANAGE_ROMS', args)
            return

        # rootpath?
        if selected_asset.id == '':
            dir_path = kodi.browse(type=0, text=kodi.translate(41159), preselected_path=root_path.getPath() if root_path else None)
            if not dir_path or (root_path is not None and dir_path == root_path.getPath()):
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            
            root_path = io.FileName(dir_path)
            apply_to_all = kodi.dialog_yesno(kodi.translate(41062))
            library.set_assets_root_path(root_path, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=apply_to_all)
        else:
            selected_asset_path = library.get_asset_path(selected_asset)
            dir_path = kodi.browse(type=0, text=kodi.translate(41160).format(selected_asset.plural),
                                   preselected_path=selected_asset_path.getPath())
            if not dir_path or dir_path == selected_asset_path.getPath():
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            library.set_asset_path(selected_asset, dir_path)
            
        repository.update_library(library)
        uow.commit()
                
    # >> Check for duplicate paths and warn user.
    AppMediator.async_cmd('CHECK_DUPLICATE_ASSET_DIRS', args)

    kodi.notify(kodi.translate(40984).format(selected_asset.name, dir_path))
    AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)


@AppMediator.register('REMOVE_DEAD_ROMS')
def cmd_remove_dead_roms(args):
    # library_id: str = args['library_id'] if 'library_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('EXPORT_ROMS')
def cmd_export_roms(args):
    # library_id: str = args['library_id'] if 'library_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('DELETE_ROMS_NFO')
def cmd_delete_rom_nfos(args):
    # library_id: str = args['library_id'] if 'library_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('CLEAR_LIBRARY_ROMS')
def cmd_clear_library_roms(args):
    library_id: str = args['library_id'] if 'library_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        library_repository = LibrariesRepository(uow)
        roms_repository = ROMsRepository(uow)
        
        library = library_repository.find(library_id)
        roms = roms_repository.find_roms_by_library(library)
        
        # If library is empty (no ROMs) do nothing
        num_roms = len([*roms])
        if num_roms == 0:
            kodi.dialog_OK(kodi.translate(41163))
            return

        # Confirm user wants to delete ROMs
        ret = kodi.dialog_yesno(kodi.translate(41164).format(library.get_name(), num_roms))
        if not ret:
            return

        # --- If there is a No-Intro XML DAT configured remove it ---
        # TODO fix
        # romcollection.reset_nointro_xmldata()
        
        collection_ids = library_repository.find_romcollection_ids_by_library(library_id)
        library_repository.remove_all_roms_in_library(library_id)
        uow.commit()
    
    AppMediator.async_cmd('RENDER_LIBRARY_VIEW', {'library_id': library_id})
    for collection_id in collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
    kodi.notify(kodi.translate(41165))


# -------------------------------------------------------------------------------------------------
# Library Scanner executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCAN_ROMS')
def cmd_execute_rom_scanner(args):
    library_id: str = args['library_id'] if 'library_id' in args else None

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        libraries_repository = LibrariesRepository(uow)
        library = libraries_repository.find(library_id)

    logger.info(f'SCAN_ROMS: scanner for library "{library.get_name()}"')
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        library.addon.get_addon_id(),
        library.get_scan_command())
