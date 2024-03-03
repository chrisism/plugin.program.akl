# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: API query implementations. Getting data for the webservice
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# API queries are called through the webservice
#

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import json

# AKL modules
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMsRepository, ROMCollectionRepository, SourcesRepository, LaunchersRepository

logger = logging.getLogger(__name__)
        
        
def qry_get_rom(rom_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository = ROMsRepository(uow)        
        rom = rom_repository.find_rom(rom_id)
        
        if rom is None:
            return None
        
        rom_dto = rom.create_dto()
        return json.dumps(rom_dto.get_data_dic())


def qry_get_rom_collection(collection_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)        
        rom_collection = collection_repository.find_romcollection(collection_id)
        
        if rom_collection is None:
            return None
        
        data = rom_collection.get_data_dic()
        return json.dumps(data)

    
def qry_get_roms(source_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        rom_repository = ROMsRepository(uow)
        
        source = source_repository.find(source_id)
        roms = rom_repository.find_roms_by_source(source)
        
        if roms is None:
            return None
        
        data = []
        for rom in roms:
            rom_dto = rom.create_dto()
            data.append(rom_dto.get_data_dic())
            
        return json.dumps(data)    


def qry_get_launcher_settings(launcher_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        launcher = repository.find(launcher_id)
        
        if launcher is not None:
            return launcher.get_settings_str()
        
    return None
    

def qry_get_collection_launcher_settings(collection_id: str, launcher_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)
        rom_collection = collection_repository.find_romcollection(collection_id)
        
        if rom_collection is None:
            return None
        
        launcher = rom_collection.get_launcher(launcher_id)
        return launcher.get_settings_str()


def qry_get_source_scanner_settings(source_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        source = source_repository.find(source_id)
        
        if source is None:
            return None
        
        return source.get_settings_str()


def qry_get_source_launchers(source_id: str) -> str:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        source = source_repository.find(source_id)
        
        if source is None:
            return None
        
        launchers_data = {}
        launchers = source.get_launchers()
        for launcher in launchers:
            launchers_data[launcher.get_id()] = launcher.get_settings()
            
        return json.dumps(launchers_data)
