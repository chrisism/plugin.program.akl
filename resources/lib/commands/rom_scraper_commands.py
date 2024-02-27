# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (ROM scraper management)
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
from akl.scrapers import ScraperSettings

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, ROMsRepository
from resources.lib.repositories import ROMCollectionRepository, SourcesRepository
from resources.lib.domain import ROMCollection, Source, ScraperAddon, g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# Start scraping
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCRAPE_ROMS')
def cmd_scrape_romcollection(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)
        collection = collection_repository.find_romcollection(romcollection_id)   
    
        scraper_settings: ScraperSettings = ScraperSettings.from_addon_settings()
        
        dialog_title = kodi.translate(41124).format(collection.get_name())
        selected_addon = _select_scraper(uow, dialog_title, scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROMS: cmd_scrape_romcollection() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return

        scraper_settings.asset_IDs_to_scrape = selected_addon.get_supported_assets()
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()

        logger.debug(f'cmd_scrape_romcollection() Selected scraper#{selected_addon.get_name()}')
        args['scraper_settings'] = scraper_settings
        args['scraper_id'] = selected_addon.addon.get_id()
        args['scraper_supported_metadata'] = selected_addon.get_supported_metadata()
        args['scraper_supported_assets'] = selected_addon.get_supported_assets()
        
    AppMediator.sync_cmd('SCRAPE_ROMS_WITH_SETTINGS', args)


@AppMediator.register('SCRAPE_SOURCE_ROMS')
def cmd_scrape_source(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        source = source_repository.find(source_id)
    
        scraper_settings: ScraperSettings = ScraperSettings.from_addon_settings()
        
        dialog_title = kodi.translate(41110).format(source.get_name())
        selected_addon = _select_scraper(uow, dialog_title, scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_SOURCE_ROMS: cmd_scrape_source() Selected None. Closing context menu')
            AppMediator.sync_cmd('SOURCE_MANAGE_ROMS', args)
            return

        scraper_settings.asset_IDs_to_scrape = selected_addon.get_supported_assets()
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()

        logger.debug(f'cmd_scrape_source() Selected scraper#{selected_addon.get_name()}')
        args['scraper_settings'] = scraper_settings
        args['scraper_id'] = selected_addon.addon.get_id()
        args['scraper_supported_metadata'] = selected_addon.get_supported_metadata()
        args['scraper_supported_assets'] = selected_addon.get_supported_assets()
        
    AppMediator.sync_cmd('SCRAPE_ROMS_WITH_SETTINGS', args)


# Scrape ROM - Select scraper to use    
@AppMediator.register('SCRAPE_ROM')
def cmd_scrape_rom(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)
         
        scraper_settings: ScraperSettings = ScraperSettings.from_addon_settings()
        
        dialog_title = kodi.translate(41123).format(rom.get_name())
        selected_addon = _select_scraper(uow, dialog_title, scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM: Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM', args)
            return

        scraper_settings.asset_IDs_to_scrape = selected_addon.get_supported_assets()
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()

        logger.debug(f'Selected scraper#{selected_addon.get_name()}')
        args['scraper_settings'] = scraper_settings
        args['scraper_id'] = selected_addon.addon.get_id()
        args['scraper_supported_metadata'] = selected_addon.get_supported_metadata()
        args['scraper_supported_assets'] = selected_addon.get_supported_assets()
        
    AppMediator.sync_cmd('SCRAPE_ROM_WITH_SETTINGS', args)


@AppMediator.register('SCRAPE_ROMS_WITH_SETTINGS')
def cmd_scrape_roms_in_collection_or_source(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    source_id: str = args['source_id'] if 'source_id' in args else None
    scraper_id: str = args['scraper_id'] if 'scraper_id' in args else None
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        collection_repository = ROMCollectionRepository(uow)
        source_repository = SourcesRepository(uow)
        
        collection = collection_repository.find_romcollection(romcollection_id)
        source = source_repository.find(source_id)
        addon = addon_repository.find(scraper_id)
        selected_addon = ScraperAddon(addon, scraper_settings)
        
        assets_to_scrape = g_assetFactory.get_asset_list_by_IDs(scraper_settings.asset_IDs_to_scrape)
        metadata_to_scrape = [constants.METADATA_DESCRIPTIONS[meta_id] for meta_id in scraper_settings.metadata_IDs_to_scrape]

        options = collections.OrderedDict()        
        options['SCRAPER_METADATA_POLICY'] = kodi.translate(41115).format(kodi.translate(scraper_settings.scrape_metadata_policy))
        options['SCRAPER_ASSET_POLICY'] = kodi.translate(41116).format(kodi.translate(scraper_settings.scrape_assets_policy))
        options['SCRAPER_SEARCH_TERM_MODE'] = kodi.translate(41117).format(kodi.translate(scraper_settings.search_term_mode))
        options['SCRAPER_GAME_SELECTION_MODE'] = kodi.translate(41118).format(kodi.translate(scraper_settings.game_selection_mode))
        options['SCRAPER_ASSET_SELECTION_MODE'] = kodi.translate(41119).format(kodi.translate(scraper_settings.asset_selection_mode))
        options['SCRAPER_META_TO_SCRAPE'] = kodi.translate(42030).format(', '.join(metadata_to_scrape))
        options['SCRAPER_ASSETS_TO_SCRAPE'] = kodi.translate(42031).format(', '.join([a.plural for a in assets_to_scrape]))
        options['SCRAPER_OVERWRITE_META_MODE'] = kodi.translate(42032).format(kodi.translate(42035) if scraper_settings.overwrite_existing_meta else kodi.translate(42036))
        options['SCRAPER_OVERWRITE_ASSETS_MODE'] = kodi.translate(42033).format(kodi.translate(42035) if scraper_settings.overwrite_existing_assets else kodi.translate(42036))
        options['SCRAPER_IGNORE_TITLES_MODE'] = kodi.translate(42034).format(kodi.translate(42035) if scraper_settings.ignore_scrap_title else kodi.translate(42036))
        options['SCRAPE'] = kodi.translate(40881)
        
        dialog_title = kodi.translate(41000 if source is None else 41111).format(
            collection.get_name() if collection is not None else source.get_name(),
            selected_addon.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(dialog_title, options, preselect='SCRAPE')
        if selected_option is None:
            logger.debug('cmd_scrape_roms_in_collection_or_source() Selected None. Closing context menu')
            del args['scraper_settings']
            ret_cmd = 'SCRAPE_ROMS' if collection is not None else 'SCRAPE_SOURCE_ROMS'
            AppMediator.sync_cmd(ret_cmd, args)
            return
        
        if selected_option != 'SCRAPE':
            args['ret_cmd'] = 'SCRAPE_ROMS_WITH_SETTINGS'
            AppMediator.sync_cmd(selected_option, args)
            return

        if not source:
            sources = source_repository.find_sources_by_collection(romcollection_id)
            for source in sources:
                _check_collection_unset_asset_dirs(source, scraper_settings)
        else:
            _check_collection_unset_asset_dirs(source, scraper_settings)

    selected_addon.set_scraper_settings(scraper_settings)
    kodi.notify(kodi.translate(40979))
    entity = collection if collection else source
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(entity))
    

# Scrape ROM - Apply settings and run scrape action
@AppMediator.register('SCRAPE_ROM_WITH_SETTINGS')
def cmd_scrape_rom_with_settings(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    scraper_id: str = args['scraper_id'] if 'scraper_id' in args else None
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        roms_repository = ROMsRepository(uow)
        
        rom = roms_repository.find_rom(rom_id)   
        addon = addon_repository.find(scraper_id)
        selected_addon = ScraperAddon(addon, scraper_settings)
        
        assets_to_scrape = g_assetFactory.get_asset_list_by_IDs(scraper_settings.asset_IDs_to_scrape)
        metadata_to_scrape = [constants.METADATA_DESCRIPTIONS[meta_id] for meta_id in scraper_settings.metadata_IDs_to_scrape]

        options = collections.OrderedDict()        
        options['SCRAPER_METADATA_POLICY'] = kodi.translate(41115).format(kodi.translate(scraper_settings.scrape_metadata_policy))
        options['SCRAPER_ASSET_POLICY'] = kodi.translate(41116).format(kodi.translate(scraper_settings.scrape_assets_policy))
        options['SCRAPER_SEARCH_TERM_MODE'] = kodi.translate(41117).format(kodi.translate(scraper_settings.search_term_mode))
        options['SCRAPER_GAME_SELECTION_MODE'] = kodi.translate(41118).format(kodi.translate(scraper_settings.game_selection_mode))
        options['SCRAPER_ASSET_SELECTION_MODE'] = kodi.translate(41119).format(kodi.translate(scraper_settings.asset_selection_mode))
        options['SCRAPER_META_TO_SCRAPE'] = kodi.translate(42030).format(', '.join(metadata_to_scrape))
        options['SCRAPER_ASSETS_TO_SCRAPE'] = kodi.translate(42031).format(', '.join([a.plural for a in assets_to_scrape]))
        options['SCRAPER_OVERWRITE_META_MODE'] = kodi.translate(42032).format(kodi.translate(42035) if scraper_settings.overwrite_existing_meta else kodi.translate(42036))
        options['SCRAPER_OVERWRITE_ASSETS_MODE'] = kodi.translate(42033).format(kodi.translate(42035) if scraper_settings.overwrite_existing_assets else kodi.translate(42036))
        options['SCRAPER_IGNORE_TITLES_MODE'] = kodi.translate(42034).format(kodi.translate(42035) if scraper_settings.ignore_scrap_title else kodi.translate(42036))
        options['SCRAPE'] = kodi.translate(40881)
        
        s = kodi.translate(41112).format(rom.get_name(),selected_addon.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect='SCRAPE')
        if selected_option is None:
            logger.debug('cmd_scrape_rom_with_settings() Selected None. Closing context menu')
            del args['scraper_settings']
            AppMediator.sync_cmd('SCRAPE_ROM', args)
            return
        
        if selected_option != 'SCRAPE':
            args['ret_cmd'] = 'SCRAPE_ROM_WITH_SETTINGS'
            AppMediator.sync_cmd(selected_option, args)
            return

        # >> Execute scraper
        selected_addon.set_scraper_settings(scraper_settings)
        kodi.notify(kodi.translate(40979))   
        kodi.run_script(
            selected_addon.addon.get_addon_id(),
            selected_addon.get_scrape_command(rom))


@AppMediator.register('SCRAPE_ROM_METADATA')
def cmd_scrape_rom_metadata(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)   
        
        scraper_settings = ScraperSettings().from_addon_settings()
        scraper_settings.scrape_metadata_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_assets_policy = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode = constants.SCRAPE_MANUAL
        scraper_settings.game_selection_mode = constants.SCRAPE_MANUAL
        scraper_settings.overwrite_existing_meta = True
        
        selected_addon = _select_scraper(uow, kodi.translate(41122), scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM_METADATA: Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

        logger.debug(f'SCRAPE_ROM_METADATA: Selected scraper#{selected_addon.get_name()}')
        scraper_settings.metadata_IDs_to_scrape = selected_addon.get_supported_metadata()
    
        options = collections.OrderedDict()
        for metadata_id in constants.METADATA_IDS:
            if selected_addon.is_metadata_supported(metadata_id):
                options[metadata_id] = constants.METADATA_DESCRIPTIONS[metadata_id]
        
        selected_options = kodi.MultiSelectDialog().select(kodi.translate(41113), options, preselected=scraper_settings.metadata_IDs_to_scrape)
            
        if selected_options is not None:
            scraper_settings.metadata_IDs_to_scrape = selected_options 

    # >> Execute scraper
    selected_addon.set_scraper_settings(scraper_settings)
    kodi.notify(kodi.translate(40979))
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))


@AppMediator.register('SCRAPE_ROM_ASSET')
def cmd_scrape_rom_asset(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    asset_id: str = args['selected_asset'] if 'selected_asset' in args else None
    
    asset_to_scrape = g_assetFactory.get_asset_info(asset_id)
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)   
        
        scraper_settings = ScraperSettings()
        scraper_settings.scrape_assets_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_metadata_policy = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode = constants.SCRAPE_MANUAL
        scraper_settings.game_selection_mode = constants.SCRAPE_MANUAL
        scraper_settings.asset_selection_mode = constants.SCRAPE_MANUAL
        scraper_settings.asset_IDs_to_scrape = [asset_id]
        scraper_settings.overwrite_existing_assets = True
        
        selected_addon = _select_scraper(uow, kodi.translate(41121).format(asset_to_scrape.name), scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM_ASSET: cmd_scrape_rom_asset() Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_ASSETS', args)
            return

    # >> Execute scraper
    logger.debug(f'SCRAPE_ROM_ASSET: Selected scraper#{selected_addon.get_name()}')
    
    kodi.notify(kodi.translate(40979))
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))    


@AppMediator.register('SCRAPE_ROM_ASSETS')
def cmd_scrape_rom_assets(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)   
    
        scraper_settings = ScraperSettings.from_addon_settings()
        scraper_settings.scrape_assets_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        scraper_settings.scrape_metadata_policy = constants.SCRAPE_ACTION_NONE
        scraper_settings.search_term_mode = constants.SCRAPE_MANUAL
        scraper_settings.asset_selection_mode = constants.SCRAPE_MANUAL
    
        selected_addon = _select_scraper(uow, kodi.translate(41120), scraper_settings)
        if selected_addon is None:
            # >> Exits context menu
            logger.debug('SCRAPE_ROM_ASSETS: Selected None. Closing context menu')
            AppMediator.sync_cmd('ROM_EDIT_ASSETS', args)
            return

        logger.debug('SCRAPE_ROM_ASSETS: Selected scraper#{}'.format(selected_addon.get_name()))
        scraper_settings.asset_IDs_to_scrape = selected_addon.get_supported_assets()
    
        asset_options = g_assetFactory.get_all()
        options = collections.OrderedDict()
        for asset_option in asset_options:
            if selected_addon.is_asset_supported(asset_option.id):
                options[asset_option.id] = kodi.translate(asset_option.name_id)
        
        selected_options = kodi.MultiSelectDialog().select(
            kodi.translate(41114), options, preselected=scraper_settings.asset_IDs_to_scrape)
    
        if selected_options is not None:
            scraper_settings.asset_IDs_to_scrape = selected_options 

        scraper_settings.overwrite_existing_assets = kodi.dialog_yesno(kodi.translate(41061))
    
    selected_addon.set_scraper_settings(scraper_settings)
    kodi.notify(kodi.translate(40979))
    # >> Execute scraper
    kodi.run_script(
        selected_addon.addon.get_addon_id(),
        selected_addon.get_scrape_command(rom))


# -------------------------------------------------------------------------------------------------
# Scraper settings configuration
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCRAPER_METADATA_POLICY')
def cmd_configure_scraper_metadata_policy(args):    
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    
    options = collections.OrderedDict()
    options[constants.SCRAPE_ACTION_NONE] = kodi.translate(constants.SCRAPE_ACTION_NONE)
    options[constants.SCRAPE_POLICY_TITLE_ONLY] = kodi.translate(constants.SCRAPE_POLICY_TITLE_ONLY)
    options[constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE] = kodi.translate(constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE)
    options[constants.SCRAPE_POLICY_SCRAPE_ONLY] = kodi.translate(constants.SCRAPE_POLICY_SCRAPE_ONLY)
    
    s = kodi.translate(41115).format(kodi.translate(scraper_settings.scrape_metadata_policy))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.scrape_metadata_policy)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.scrape_metadata_policy = selected_option
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_ASSET_POLICY')
def cmd_configure_scraper_asset_policy(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
      
    options = collections.OrderedDict()
    options[constants.SCRAPE_ACTION_NONE] = kodi.translate(constants.SCRAPE_ACTION_NONE)
    options[constants.SCRAPE_POLICY_LOCAL_ONLY] = kodi.translate(constants.SCRAPE_POLICY_LOCAL_ONLY)
    options[constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE] = kodi.translate(constants.SCRAPE_POLICY_LOCAL_AND_SCRAPE)
    options[constants.SCRAPE_POLICY_SCRAPE_ONLY] = kodi.translate(constants.SCRAPE_POLICY_SCRAPE_ONLY)
    
    s = kodi.translate(41116).format(kodi.translate(scraper_settings.scrape_assets_policy))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.scrape_assets_policy)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.scrape_assets_policy = selected_option
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)


@AppMediator.register('SCRAPER_SEARCH_TERM_MODE')
def cmd_configure_scraper_search_term_mode(args):
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    
    options = collections.OrderedDict()
    options[constants.SCRAPE_MANUAL]    = kodi.translate(constants.SCRAPE_MANUAL)
    options[constants.SCRAPE_AUTOMATIC] = kodi.translate(constants.SCRAPE_AUTOMATIC)
    s = kodi.translate(41117).format(kodi.translate(scraper_settings.search_term_mode))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.search_term_mode)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.search_term_mode = selected_option
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_GAME_SELECTION_MODE')
def cmd_configure_scraper_game_selection_mode(args):
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    
    options = collections.OrderedDict()
    options[constants.SCRAPE_MANUAL] = kodi.translate(constants.SCRAPE_MANUAL)
    options[constants.SCRAPE_AUTOMATIC] = kodi.translate(constants.SCRAPE_AUTOMATIC)
    s = kodi.translate(41118).format(kodi.translate(scraper_settings.game_selection_mode))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.game_selection_mode)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.game_selection_mode = selected_option  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_ASSET_SELECTION_MODE')
def cmd_configure_scraper_asset_selection_mode(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
      
    options = collections.OrderedDict()
    options[constants.SCRAPE_MANUAL] = kodi.translate(constants.SCRAPE_MANUAL)
    options[constants.SCRAPE_AUTOMATIC] = kodi.translate(constants.SCRAPE_AUTOMATIC)
    s = kodi.translate(41119).format(kodi.translate(scraper_settings.asset_selection_mode))
    selected_option = kodi.OrdDictionaryDialog().select(s, options, preselect=scraper_settings.asset_selection_mode)
    
    if selected_option is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.asset_selection_mode = selected_option  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_META_TO_SCRAPE')
def cmd_configure_scraper_metadata_to_scrape(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_supported_metadata: list  = args['scraper_supported_metadata'] if 'scraper_supported_metadata' in args else []

    options = collections.OrderedDict()
    for metadata_id in constants.METADATA_IDS:
        if scraper_supported_metadata is None or metadata_id in scraper_supported_metadata:
            options[metadata_id] = constants.METADATA_DESCRIPTIONS[metadata_id]
    
    selected_options = kodi.MultiSelectDialog().select(kodi.translate(41113), options, preselected=scraper_settings.metadata_IDs_to_scrape)
    
    if selected_options is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.metadata_IDs_to_scrape = selected_options  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_ASSETS_TO_SCRAPE')
def cmd_configure_scraper_assets_to_scrape(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    supported_assets: list = args['scraper_supported_assets'] if 'scraper_supported_assets' in args else []

    asset_options = g_assetFactory.get_all()
    options = collections.OrderedDict()
    for asset_option in asset_options:
        if supported_assets is None or asset_option.id in supported_assets:
            options[asset_option.id] = kodi.translate(asset_option.name_id)
    
    selected_options = kodi.MultiSelectDialog().select(kodi.translate(41114), options, preselected=scraper_settings.asset_IDs_to_scrape)
    
    if selected_options is None:
        AppMediator.sync_cmd(args['ret_cmd'], args)
        return
    
    scraper_settings.asset_IDs_to_scrape = selected_options  
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)
    return


@AppMediator.register('SCRAPER_OVERWRITE_META_MODE')
def cmd_configure_scraper_overwrite_meta_mode(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_settings.overwrite_existing_meta = not scraper_settings.overwrite_existing_meta
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)

    
@AppMediator.register('SCRAPER_OVERWRITE_ASSETS_MODE')
def cmd_configure_scraper_overwrite_assets_mode(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_settings.overwrite_existing_assets = not scraper_settings.overwrite_existing_assets
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)


@AppMediator.register('SCRAPER_IGNORE_TITLES_MODE')
def cmd_configure_scraper_ignore_mode(args):  
    scraper_settings: ScraperSettings = args['scraper_settings'] if 'scraper_settings' in args else ScraperSettings.from_addon_settings()
    scraper_settings.ignore_scrap_title = not scraper_settings.ignore_scrap_title
    args['scraper_settings'] = scraper_settings
    AppMediator.sync_cmd(args['ret_cmd'], args)


def _select_scraper(uow: UnitOfWork, title: str, scraper_settings: ScraperSettings) -> ScraperAddon:
    selected_addon = None
    repository = AelAddonRepository(uow)
    addons = repository.find_all_scraper_addons()
    
    # --- Make a menu list of available metadata scrapers ---
    options = {}
    for addon in addons:
        scraper_addon = ScraperAddon(addon, scraper_settings)
        if scraper_addon.settings_are_applicable():
            options[scraper_addon] = addon.get_name()
                    
    selected_addon: ScraperAddon = kodi.OrdDictionaryDialog().select(title, options)
    return selected_addon


def _check_collection_unset_asset_dirs(source: Source, scraper_settings: ScraperSettings) -> bool:
    logger.debug('_check_launcher_unset_asset_dirs() BEGIN ...')
    
    unconfigured_name_list = []
    enabled_asset_list = []
    for asset_id in scraper_settings.asset_IDs_to_scrape:
        rom_asset = g_assetFactory.get_asset_info(asset_id)
        asset_path = source.get_asset_path(rom_asset, False)
        
        if asset_path is None:
            logger.debug(f'Directory not set. Asset "{rom_asset}" will be disabled')
            unconfigured_name_list.append(rom_asset.name)
        else:
            enabled_asset_list.append(rom_asset.id)
    
    scraper_settings.asset_IDs_to_scrape = enabled_asset_list
    if unconfigured_name_list:
        unconfigured_asset_srt = ', '.join(unconfigured_name_list)
        msg = kodi.translate(41149).format(unconfigured_asset_srt)
        logger.debug(msg)
        kodi.dialog_OK(msg)
        return False
    return True
