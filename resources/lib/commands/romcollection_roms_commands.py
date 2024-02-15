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

from akl import constants
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, LibrariesRepository
from resources.lib.domain import g_assetFactory, RuleSet

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# ROMCollection ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMCOLLECTION_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
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
    options['IMPORT_ROMS'] = kodi.translate(42050)
    if has_roms:
        options['SCRAPE_ROMS'] = kodi.translate(42052)
        options['CLEAR_ROMS'] = kodi.translate(42054)

    s = kodi.translate(41128).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args:
            del args['scraper_settings']
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)


# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
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
        
        logger.debug(f'Main select() returned {selected_asset_info.name}')
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

    AppMediator.async_cmd('SET_ROMS_DEFAULT_ARTWORK', {
        'romcollection_id': romcollection.get_id(),
        'selected_asset': selected_asset_info.id})


@AppMediator.register('IMPORT_ROMS')
def cmd_import_roms(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        import_rules = repository.find_import_rules_by_collection(romcollection)

        options = collections.OrderedDict()
        for import_rule in import_rules:
            options[import_rule.get_ruleset_id()] = (f"{kodi.translate(42509)}: {import_rule.get_library_name()} "
                                                     f"({import_rule.get_rules_description()})")

        options['NEW_IMPORT_RULESET'] = kodi.translate(40921)

    s = kodi.translate(41130).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('IMPORT_ROMS: Selected None. Closing context menu')
        AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
        return
    
    if selected_option == 'NEW_IMPORT_RULESET':
        AppMediator.async_cmd(selected_option, args)
        return
    
    logger.debug(f'IMPORT_ROMS: Selected set {selected_option}')
    args['ruleset_id'] = selected_option
    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)


@AppMediator.register('NEW_IMPORT_RULESET')
def cmd_new_import_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        lib_repository = LibrariesRepository(uow)
        libraries = lib_repository.find_all()
        
        options = collections.OrderedDict()
        for library in libraries:
            options[library] = library.get_name()

        s = kodi.translate(41172)
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        if selected_option is None:
            # >> Exits context menu
            logger.debug('NEW_IMPORT_RULESET: No library selected. Closing context menu')
            AppMediator.async_cmd('IMPORT_ROMS', args)
            return
        
        selected_library = selected_option
        logger.debug(f'NEW_IMPORT_RULESET: Selected library {selected_library.get_id()}')
        
        ruleset = RuleSet()
        ruleset.apply_library_and_collection(selected_library, romcollection)
        
        repository.add_ruleset_to_romcollection(romcollection.get_id(), ruleset)
        uow.commit()
        
    args['ruleset_id'] = ruleset.get_ruleset_id()
    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
        

@AppMediator.register('EDIT_IMPORT_RULESET')
def cmd_edit_import_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    ruleset_id: str = args['ruleset_id'] if 'ruleset_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        lib_repository = LibrariesRepository(uow)
        libraries = lib_repository.find_all()
        
        

# --- Empty Launcher ROMs ---
@AppMediator.register('CLEAR_ROMS')
def cmd_clear_roms(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        
        romcollection = collection_repository.find_romcollection(romcollection_id)
        roms = roms_repository.find_roms_by_romcollection(romcollection)
        
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
