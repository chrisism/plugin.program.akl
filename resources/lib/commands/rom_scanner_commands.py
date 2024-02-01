# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection scanner management)
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
from __future__ import annotations

import logging
import collections

from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, LibrariesRepository, AelAddonRepository
from resources.lib.domain import ROM, AelAddon

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM Scanners management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('EDIT_ROMCOLLECTION_SCANNERS')
def cmd_manage_romcollection_scanners(args):
    logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() SHOW MENU')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    options = collections.OrderedDict()
    options['ADD_SCANNER'] = kodi.translate(42080)
    options['EDIT_SCANNER'] = kodi.translate(42081)
    options['REMOVE_SCANNER'] = kodi.translate(42082)
        
    s = kodi.translate(41106).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMCOLLECTION_SCANNERS: cmd_manage_romcollection_scanners() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)

# --- Sub commands ---
@AppMediator.register('ADD_SCANNER')
def cmd_add_romcollection_scanner(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository               = AelAddonRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        addons = repository.find_all_scanners()
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        
        for addon in addons:
            options[addon] = addon.get_name()
    
    s = kodi.translate(41107)
    selected_option:AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ADD_SCANNER: cmd_add_romcollection_scanner() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ADD_SCANNER: cmd_add_romcollection_scanner() Selected {}'.format(selected_option.get_id()))
    
    scanner_addon = ROMCollectionScanner(selected_option, {})
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        selected_option.get_addon_id(), 
        scanner_addon.get_configure_command(romcollection))

@AppMediator.register('EDIT_SCANNER')
def cmd_edit_romcollection_scanners(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
        default_launcher = romcollection.get_default_launcher()
    
    scanners = romcollection.get_scanners()
    if len(scanners) == 0:
        kodi.notify(kodi.translate(40982))
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    options = collections.OrderedDict()
    for scanner in scanners:
        options[scanner] = scanner.get_name()
    
    s = kodi.translate(41108)
    selected_option:ROMCollectionScanner = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_SCANNER: cmd_edit_romcollection_scanners() Selected None. Closing context menu')
        AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_SCANNER: cmd_edit_romcollection_scanners() Selected {}'.format(selected_option.get_id()))
    
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        selected_option.addon.get_addon_id(),
        selected_option.get_configure_command(romcollection))  
       
@AppMediator.register('REMOVE_SCANNER')
def cmd_remove_romcollection_scanner(args):
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        scanners = romcollection.get_scanners()
        if len(scanners) == 0:
            kodi.notify(kodi.translate(40982))
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        options = collections.OrderedDict()
        for scanner in scanners:
            options[scanner] = scanner.get_name()
        
        s = kodi.translate(41109)
        selected_option:ROMCollectionScanner = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Selected None. Closing context menu')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno(kodi.translate(41060).format(selected_option.get_name())):
            logger.debug('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args)
            return
        
        romcollection_repository.remove_scanner(romcollection.get_id(), selected_option.get_id())
        logger.info('REMOVE_SCANNER: cmd_remove_romcollection_scanner() Removed scanner#{}'.format(selected_option.get_id()))
        uow.commit()
    
    AppMediator.async_cmd('EDIT_ROMCOLLECTION_SCANNERS', args) 


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
        library.get_scan_command(library))
