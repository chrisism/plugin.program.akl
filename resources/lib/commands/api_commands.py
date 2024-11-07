# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (API actions)
##
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Commands executed by the webservice API
#

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
from akl.scrapers import ScraperSettings

from akl.utils import kodi
from akl.api import ROMObj
from akl import constants

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, SourcesRepository
from resources.lib.repositories import AklAddonRepository, LaunchersRepository
from resources.lib.domain import ROM, ROMLauncherAddon

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# ROMCollection API commands
# -------------------------------------------------------------------------------------------------
def cmd_set_launcher_args(args) -> bool:
    launcher_id: str = args['launcher_id'] if 'launcher_id' in args else None
    addon_id: str = args['addon_id'] if 'addon_id' in args else None
    launcher_settings = args['settings'] if 'settings' in args else None
    
    entity_type = args['entity_type'] if 'entity_type' in args else None
    entity_id: str = args['entity_id'] if 'entity_id' in args else None
        
    redirect_to_action = None
    args = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AklAddonRepository(uow)
        launchers_repository = LaunchersRepository(uow)
        
        addon = addon_repository.find_by_addon_id(addon_id, constants.AddonType.LAUNCHER)
        launcher = launchers_repository.find(launcher_id)
        
        if launcher is None:
            launcher = ROMLauncherAddon(None, addon)
            launcher.set_settings(launcher_settings)
            launchers_repository.insert_launcher(launcher)
        else:
            launcher.set_settings(launcher_settings)
            launchers_repository.update_launcher(launcher)
        
        if entity_type:
            if entity_type == constants.OBJ_ROM:
                entity_repo = ROMsRepository(uow)
                rom = entity_repo.find_rom(entity_id)
                rom.add_launcher(launcher)
                entity_repo.update_rom(rom)
                redirect_to_action = "EDIT_ROM_LAUNCHERS"
                args = {'rom_id': entity_id}
                
            if entity_type == constants.OBJ_ROMCOLLECTION:
                entity_repo = ROMCollectionRepository(uow)
                collection = entity_repo.find_romcollection(entity_id)
                collection.add_launcher(launcher)
                entity_repo.update_romcollection(collection)
                redirect_to_action = "EDIT_ROMCOLLECTION_LAUNCHERS"
                args = {'romcollection_id': entity_id}
                
            if entity_type == constants.OBJ_SOURCE:
                entity_repo = SourcesRepository(uow)
                source = entity_repo.find(entity_id)
                source.add_launcher(launcher)
                entity_repo.update_source(source)
                redirect_to_action = "EDIT_SOURCE_LAUNCHERS"
                args = {'source_id': entity_id}
                
        uow.commit()
    
    kodi.refresh_container()
    kodi.notify(kodi.translate(41005).format(launcher.get_name()))
    
    if entity_type:
        AppMediator.async_cmd(redirect_to_action, args)
            
    return True


# -------------------------------------------------------------------------------------------------
# Source scanner API commands
# -------------------------------------------------------------------------------------------------
def cmd_set_scanner_settings(args) -> bool:
    # TODO: backwards compatiblity
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    source_id: str = args['source_id'] if 'source_id' in args else None
    source_id = romcollection_id if not source_id else source_id
    
    settings: dict = args['settings'] if 'settings' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        src_repository = SourcesRepository(uow)
        source = src_repository.find(source_id)
        
        source.set_settings(settings)
            
        src_repository.update_source(source)
        uow.commit()
    
    kodi.notify(kodi.translate(41006).format(source.addon.get_name()))
    AppMediator.async_cmd('RENDER_SOURCES_VIEW')
    
    if kodi.dialog_yesno(kodi.translate(41051)):
        AppMediator.async_cmd('SCAN_ROMS', {'source_id': source_id})
    else:
        AppMediator.async_cmd('SOURCE_MANAGE_ROMS', {'source_id': source_id})
    return True


def cmd_store_scanned_roms(args) -> bool:
    # TODO: backwards compatiblity
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    source_id: str = args['source_id'] if 'source_id' in args else None
    source_id = romcollection_id if not source_id else source_id
    
    new_roms: list = args['roms'] if 'roms' in args else None
    
    if new_roms is None:
        AppMediator.async_cmd('SOURCE_MANAGE_ROMS', {'source_id': source_id})
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository = ROMsRepository(uow)
        src_repository = SourcesRepository(uow)
        source = src_repository.find(source_id)

        for rom_data in new_roms:
            api_rom_obj = ROMObj(rom_data)
            
            rom_obj = ROM()
            rom_obj.update_with(api_rom_obj, overwrite_existing_metadata=True, update_scanned_data=True)
            rom_obj.set_platform(source.get_platform())
            rom_obj.scanned_by(source.get_id())
            rom_obj.apply_source_asset_paths(source)
                                    
            rom_repository.insert_rom(rom_obj)
        uow.commit()
    
    kodi.notify(kodi.translate(41007).format(source.get_name()))

    AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
    AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_TITLE_ID})
    AppMediator.async_cmd('SOURCE_MANAGE_ROMS', {'source_id': source_id})
    return True


def cmd_remove_roms(args) -> bool:
    # TODO: backwards compatiblity
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    source_id: str = args['source_id'] if 'source_id' in args else None
    source_id = romcollection_id if not source_id else source_id
    
    rom_ids: list = args['rom_ids'] if 'rom_ids' in args else None
    if rom_ids is None:
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        sources_repository = SourcesRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        rom_repository = ROMsRepository(uow)
        
        romcollections = [*romcollections_repository.find_romcollections_by_source(source_id)]
        source = sources_repository.find(source_id)
        
        for rom_id in rom_ids:
            rom_repository.delete_rom(rom_id)
        uow.commit()
    
    kodi.notify(kodi.translate(41010).format(source.get_name()))
    
    AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
    for collection in romcollections:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection.get_id()})
    AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    for romcollection in romcollections:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
    AppMediator.async_cmd('EDIT_SOURCE', {'source_id': source_id})
    return True


def cmd_store_scraped_roms(args) -> bool:
    entity_type = args['entity_type'] if 'entity_type' in args else None
    entity_id: str = args['entity_id'] if 'entity_id' in args else None
    scraped_roms: list = args['roms'] if 'roms' in args else None
    settings_dic: dict = args['applied_settings'] if 'applied_settings' in args else {}
    applied_settings = ScraperSettings.from_settings_dict(settings_dic)
    
    if scraped_roms is None:
        return
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository = ROMsRepository(uow)
        
        entity_name = 'UNKNOWN'
        if entity_type == constants.OBJ_SOURCE:
            source = source_repository.find(entity_id)
            existing_roms = rom_repository.find_roms_by_source(source)
            entity_name = source.get_name()
            
        if entity_type == constants.OBJ_ROMCOLLECTION:
            romcollection = romcollection_repository.find_romcollection(entity_id)
            existing_roms = rom_repository.find_roms_by_romcollection(romcollection)
            entity_name = romcollection.get_name()
        
        existing_roms_by_id = {rom.get_id(): rom for rom in existing_roms}

        metadata_is_updated = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
        assets_are_updated = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE

        metadata_to_update = applied_settings.metadata_IDs_to_scrape if metadata_is_updated else []
        assets_to_update = applied_settings.asset_IDs_to_scrape if assets_are_updated else []

        logger.debug('========================== Applied scraper settings ==========================')
        logger.debug('Metadata IDs:         {}'.format(', '.join(applied_settings.metadata_IDs_to_scrape)))
        logger.debug('Asset IDs:            {}'.format(', '.join(applied_settings.asset_IDs_to_scrape)))
        logger.debug('Overwrite existing:')
        logger.debug(' - Metadata           {}'.format('Yes' if applied_settings.overwrite_existing_meta else 'No'))
        logger.debug(' - Assets             {}'.format('Yes' if applied_settings.overwrite_existing_assets else 'No'))

        for rom_data in scraped_roms:
            api_rom_obj = ROMObj(rom_data)
            
            if api_rom_obj.get_id() not in existing_roms_by_id:
                logger.warning('Scraped ROM {} with ID {} could not be found in {}#{} {}. Will be skipped.'.format(
                    api_rom_obj.get_name(),
                    api_rom_obj.get_id(),
                    kodi.translate(entity_type),
                    entity_id,
                    entity_name))
                continue
            
            rom_obj = existing_roms_by_id[api_rom_obj.get_id()]
            rom_obj.update_with(
                api_rom_obj,
                metadata_to_update,
                assets_to_update,
                overwrite_existing_metadata=applied_settings.overwrite_existing_meta,
                overwrite_existing_assets=applied_settings.overwrite_existing_assets,
                update_scanned_data=not settings.getSettingAsBool('scan_ignore_scrap_title'))
            # rom_obj.scraped_with(scraper_id)
            
            rom_repository.update_rom(rom_obj)
        uow.commit()
    
    kodi.notify(kodi.translate(41008).format(romcollection.get_name()))
    
    if metadata_is_updated:
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    if entity_type == constants.OBJ_ROMCOLLECTION:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': entity_id})
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': entity_id})
        
    if entity_type == constants.OBJ_SOURCE:
        AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': entity_id})
        AppMediator.async_cmd('SOURCE_MANAGE_ROMS', {'source_id': entity_id})
    return True


def cmd_store_scraped_single_rom(args) -> bool:
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    scraped_rom_data: dict = args['rom'] if 'rom' in args else None
    settings_dic: dict = args['applied_settings'] if 'applied_settings' in args else {}
    applied_settings = ScraperSettings.from_settings_dict(settings_dic)
    
    if scraped_rom_data is None:
        return
        
    scraped_rom = ROMObj(scraped_rom_data)
    rom_collection_ids = []
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        rom_repository = ROMsRepository(uow)
                
        rom_romcollections = romcollection_repository.find_romcollections_by_rom(rom_id)
        rom_collection_ids = [collection.get_id() for collection in rom_romcollections]
        
        rom = rom_repository.find_rom(rom_id)

        metadata_is_updated = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
        assets_are_updated = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE
        
        metadata_to_update = applied_settings.metadata_IDs_to_scrape if metadata_is_updated else []
        assets_to_update = applied_settings.asset_IDs_to_scrape if assets_are_updated else []
       
        logger.debug('========================== Applied scraper settings ==========================')
        logger.debug('Metadata IDs:         {}'.format(', '.join(applied_settings.metadata_IDs_to_scrape)))
        logger.debug('Asset IDs:            {}'.format(', '.join(applied_settings.asset_IDs_to_scrape)))
        logger.debug('Overwrite existing:')
        logger.debug(' - Metadata           {}'.format('Yes' if applied_settings.overwrite_existing_meta else 'No'))
        logger.debug(' - Assets             {}'.format('Yes' if applied_settings.overwrite_existing_assets else 'No'))
        logger.debug('Metadata updated:     {}'.format('Yes' if metadata_is_updated else 'No'))
        logger.debug('Assets updated:       {}'.format('Yes' if assets_are_updated else 'No'))

        rom.update_with(scraped_rom,
                        metadata_to_update,
                        assets_to_update,
                        overwrite_existing_metadata=applied_settings.overwrite_existing_meta,
                        overwrite_existing_assets=applied_settings.overwrite_existing_assets,
                        update_scanned_data=not settings.getSettingAsBool('scan_ignore_scrap_title'))
        #  rom_obj.scraped_with(scraper_id)
        
        rom_repository.update_rom(rom)
        uow.commit()
    
    kodi.notify(kodi.translate(41009).format(rom.get_name()))
    
    AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': rom.get_scanned_by()})
    for collection_id in rom_collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
        
    scraped_meta = applied_settings.scrape_metadata_policy != constants.SCRAPE_ACTION_NONE
    scraped_assets = applied_settings.scrape_assets_policy != constants.SCRAPE_ACTION_NONE
    
    if metadata_is_updated:
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    if scraped_meta and not scraped_assets:
        AppMediator.async_cmd('ROM_EDIT_METADATA', {'rom_id': rom_id})
    elif scraped_assets and not scraped_meta:
        if len(applied_settings.asset_IDs_to_scrape) == 1:
            AppMediator.async_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id, 'selected_asset': applied_settings.asset_IDs_to_scrape[0]})
        else:
            AppMediator.async_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id})
    else:
        AppMediator.async_cmd('EDIT_ROM', {'rom_id': rom_id})
        
    return True
