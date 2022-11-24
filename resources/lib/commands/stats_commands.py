# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (generating stats and counts)
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

from akl import constants
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMsRepository

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# ROM stats
# -------------------------------------------------------------------------------------------------

@AppMediator.register('ROM_WAS_LAUNCHED')
def cmd_process_launching_of_rom(args):
    logger.debug('ROM_WAS_LAUNCHED: cmd_process_launching_of_rom() Processing that a ROM was launched')
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    if rom_id is None:
        logger.warning('cmd_process_launching_of_rom(): No rom id supplied.')
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        rom.increase_launch_count()
        repository.update_rom(rom)

        uow.commit()
        logger.debug('ROM_WAS_LAUNCHED: cmd_process_launching_of_rom() Processed stats for ROM {}'.format(rom.get_name()))
        AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_RECENT_ID})
        AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_MOST_PLAYED_ID})


@AppMediator.register('ADD_ROM_TO_FAVOURITES')
def cmd_add_rom_to_favourites(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    if rom_id is None:
        logger.warning('No rom id supplied.')
        kodi.notify_warn("Invalid parameters supplied.")
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        rom.add_to_favourites()
        repository.update_rom(rom)
        uow.commit()
        
    logger.debug(f'Added ROM {rom.get_rom_identifier()} to favourites')
    AppMediator.async_cmd('RENDER_VCOLLECTION_VIEW', {'vcollection_id': constants.VCOLLECTION_FAVOURITES_ID})
