# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection roms management)
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
import typing

from akl import constants
from akl.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, LibrariesRepository, ROMsRepository, ROMsJsonFileRepository
from resources.lib.domain import ROM, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# Library management.
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
    # options['EDIT_LIBRARY_SCANNER'] = kodi.translate(42048)
    # options['ADD_SCANNER'] = kodi.translate(42049)
    
    options['EXPORT_ROMS'] = kodi.translate(42051)
    options['SCRAPE_LIBRARY_ROMS'] = kodi.translate(42052)
    options['DELETE_ROMS_NFO'] = kodi.translate(42053)
    options['CLEAR_ROMS'] = kodi.translate(42054)

    s = kodi.translate(41161).format(library.get_library_name())
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
        list_items[AssetInfo()] = kodi.translate(42083).format(root_path_str)
        for asset_info in assets:
            path = library.get_asset_path(asset_info)
            if path:
                list_items[asset_info] = kodi.translate(42084).format(asset_info.plural, path.getPath())

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select(kodi.translate(41129), list_items)

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