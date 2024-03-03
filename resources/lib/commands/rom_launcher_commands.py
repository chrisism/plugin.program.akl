# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection launcher management)
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

from akl.utils import kodi
from akl import settings, constants

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, AelAddonRepository, LaunchersRepository
from resources.lib.repositories import ROMCollectionRepository, ROMsRepository, SourcesRepository
from resources.lib.domain import AelAddon, ROMLauncherAddon, ROMLauncherAddonFactory

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# Launcher management.
# -------------------------------------------------------------------------------------------------
@AppMediator.register('ADD_LAUNCHER')
def cmd_add_launcher(args):
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = AelAddonRepository(uow)
        addons = repository.find_all_launcher_addons()

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = kodi.translate(41106)
    selected_option: AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'Selected {selected_option.get_id()}')
    
    selected_launcher = ROMLauncherAddonFactory.create(selected_option, {})
    selected_launcher.configure(args)


@AppMediator.register('EDIT_LAUNCHER')
def cmd_edit_launcher(args):
    logger.debug('EDIT_LAUNCHER')
    launcher_id: str = args['launcher_id'] if 'launcher_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        launcher = repository.find(launcher_id)

    launcher.configure(args)


@AppMediator.register('DELETE_LAUNCHER')
def cmd_delete_launcher(args):
    logger.debug('DELETE_LAUNCHER')
    launcher_id: str = args['launcher_id'] if 'launcher_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        launcher = repository.find(launcher_id)

        confirmed = kodi.dialog_yesno(kodi.translate(41066).format(launcher.get_name()))
        if not confirmed:
            return
        
        repository.delete_launcher(launcher)
        kodi.refresh_container()


# -------------------------------------------------------------------------------------------------
# Launcher association.
# -------------------------------------------------------------------------------------------------
@AppMediator.register('EDIT_SOURCE_LAUNCHERS')
def cmd_manage_source_launchers(args):
    logger.debug('EDIT_SOURCE_LAUNCHERS: SHOW MENU')
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
        
    launchers = source.get_launchers()
    default_launcher = next((lr for lr in launchers if lr.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else 'None'
    
    options = collections.OrderedDict()
    options['ADD_SOURCE_LAUNCHER'] = kodi.translate(42026)
    options['REMOVE_SOURCE_LAUNCHER'] = kodi.translate(42028)
    options['SET_DEFAULT_SOURCE_LAUNCHER'] = kodi.translate(42029).format(default_launcher_name)
        
    s = kodi.translate(41100).format(source.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_SOURCE_LAUNCHERS: Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_SOURCE', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_SOURCE_LAUNCHERS: Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('EDIT_ROMCOLLECTION_LAUNCHERS')
def cmd_manage_romcollection_launchers(args):
    logger.debug('EDIT_ROMCOLLECTION_LAUNCHERS: cmd_manage_romcollection_launchers() SHOW MENU')
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    launchers = romcollection.get_launchers()
    default_launcher = next((lc for lc in launchers if lc.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else 'None'
    
    options = collections.OrderedDict()
    options['ADD_COLLECTION_LAUNCHER'] = kodi.translate(42026)
    options['REMOVE_COLLECTION_LAUNCHER'] = kodi.translate(42028)
    options['SET_DEFAULT_COLLECTION_LAUNCHER'] = kodi.translate(42029).format(default_launcher_name)
        
    s = kodi.translate(41100).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION_LAUNCHERS: Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_ROMCOLLECTION_LAUNCHERS: Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('EDIT_ROM_LAUNCHERS')
def cmd_manage_rom_launchers(args):
    logger.debug('EDIT_ROM_LAUNCHERS: cmd_manage_rom_launchers() SHOW MENU')
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
    launchers = rom.get_launchers()
    default_launcher = next((lc for lc in launchers if lc.is_default()), launchers[0]) if len(launchers) > 0 else None
    default_launcher_name = default_launcher.get_name() if default_launcher is not None else kodi.translate(20010)
    
    options = collections.OrderedDict()
    options['ADD_ROM_LAUNCHER'] = kodi.translate(42026)
    options['REMOVE_ROM_LAUNCHER'] = kodi.translate(42028)
    options['SET_DEFAULT_ROM_LAUNCHER'] = kodi.translate(42029).format(default_launcher_name)
        
    s = kodi.translate(41100).format(rom.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('Selected None. Closing context menu')
        AppMediator.sync_cmd('EDIT_ROM', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)
    

# --- Sub commands ---
@AppMediator.register('ADD_ROM_LAUNCHER')
def cmd_add_rom_launchers(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        rom_repository = ROMsRepository(uow)
        
        launchers = repository.find_all()
        rom = rom_repository.find_rom(rom_id)

        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        options["NEW"] = kodi.translate(42090)
        
        s = kodi.translate(41101)
        selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        if selected_option == "NEW":
            args["entity_type"] = constants.OBJ_ROM
            args["entity_id"] = rom_id
            AppMediator.sync_cmd("ADD_LAUNCHER", args)
            return
        
        selected_option: ROMLauncherAddon = selected_option
        logger.debug(f'Selected {selected_option.get_id()}')
        is_default = kodi.dialog_yesno(kodi.translate(41171).format(selected_option.get_name()))
        
        rom.add_launcher(launcher, is_default)
        rom_repository.update_rom(rom)    
        logger.info(f'Added launcher#{selected_option.get_id()} to ROM {rom.get_id()}')
        uow.commit()

        repository = AelAddonRepository(uow)
        addons = repository.find_all_launcher_addons()

        for addon in addons:
            options[addon] = addon.get_name()
    
    s = kodi.translate(41106)
    selected_option: AelAddon = kodi.OrdDictionaryDialog().select(s, options)
    
    kodi.notify(kodi.translate(41109).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)


@AppMediator.register('ADD_SOURCE_LAUNCHER')
def cmd_add_source_launchers(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
        
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        source_repository = SourcesRepository(uow)
        
        launchers = repository.find_all()
        source = source_repository.find(source_id)

        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        options["NEW"] = kodi.translate(42090)
    
        s = kodi.translate(41101)
        selected_option: ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('ADD_SOURCE_LAUNCHER: Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        if selected_option == "NEW":
            args["entity_type"] = constants.OBJ_SOURCE
            args["entity_id"] = source_id
            AppMediator.sync_cmd("ADD_LAUNCHER", args)
            return
        
        logger.debug(f'ADD_SOURCE_LAUNCHER: Selected {selected_option.get_id()}')
        is_default = kodi.dialog_yesno(kodi.translate(41171).format(selected_option.get_name()))
        
        source.add_launcher(launcher, is_default)
        if kodi.dialog_yesno(kodi.translate(41050)):
            source.import_data_dic(launcher.get_settings()['romcollection'])
            
        source_repository.update_source(source)
        logger.info(f'Added launcher#{selected_option.get_id()} to Source {source.get_id()}')
        uow.commit()

    kodi.notify(kodi.translate(41109).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)


@AppMediator.register('ADD_COLLECTION_LAUNCHER')
def cmd_add_romcollection_launchers(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    metadata_updated = False
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = LaunchersRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        
        launchers = repository.find_all()
        romcollection = romcollection_repository.find_romcollection(romcollection_id)

        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        options["NEW"] = kodi.translate(42090)
           
        s = kodi.translate(41101)
        selected_option: ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
    
        if selected_option is None:
            # >> Exits context menu
            logger.debug('ADD_COLLECTION_LAUNCHER: Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
    
        if selected_option == "NEW":
            args["entity_type"] = constants.OBJ_ROMCOLLECTION
            args["entity_id"] = romcollection_id
            AppMediator.sync_cmd("ADD_LAUNCHER", args)
            return
        
        logger.debug(f'ADD_COLLECTION_LAUNCHER: Selected {selected_option.get_id()}')
        is_default = kodi.dialog_yesno(kodi.translate(41171).format(selected_option.get_name()))
        
        romcollection.add_launcher(launcher, is_default)
        if kodi.dialog_yesno(kodi.translate(41050)):
            romcollection.import_data_dic(launcher.get_settings()['romcollection'])
            metadata_updated = True
            
        romcollection_repository.update_romcollection(romcollection)
        logger.info(f'Added launcher#{selected_option.get_id()} to ROMCollection {romcollection.get_id()}')
        uow.commit()
    
    if metadata_updated:
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
        
    kodi.notify(kodi.translate(41109).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)

          
@AppMediator.register('REMOVE_COLLECTION_LAUNCHER')
def cmd_remove_romcollection_launchers(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)        
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        launchers = romcollection.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41003))
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        
        s = kodi.translate(41103)
        selected_option: ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_COLLECTION_LAUNCHER: cmd_remove_romcollection_launchers() Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug('REMOVE_COLLECTION_LAUNCHER: Selected {}'.format(selected_option.get_id()))
        if not kodi.dialog_yesno(kodi.translate(41059).format(selected_option.get_name())):
            logger.debug('REMOVE_COLLECTION_LAUNCHER: cmd_remove_romcollection_launchers() Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        romcollection_repository.remove_launcher(romcollection.get_id(), selected_option.get_id())
        logger.info(f'Removed launcher#{selected_option.get_id()}')
        uow.commit()
    
    kodi.notify(kodi.translate(41004).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)

   
@AppMediator.register('REMOVE_SOURCE_LAUNCHER')
def cmd_remove_source_launchers(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        source = source_repository.find(source_id)
    
        launchers = source.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41168))
            AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        
        s = kodi.translate(41103)
        selected_option: ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('REMOVE_SOURCE_LAUNCHER: Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        logger.debug(f'REMOVE_SOURCE_LAUNCHER: Selected {selected_option.get_id()}')
        if not kodi.dialog_yesno(kodi.translate(41059).format(selected_option.get_name())):
            logger.debug('REMOVE_SOURCE_LAUNCHER: Cancelled operation.')
            AppMediator.async_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        source_repository.remove_launcher(source.get_id(), selected_option.get_id())
        logger.info(f'Removed launcher#{selected_option.get_id()}')
        uow.commit()
    
    kodi.notify(kodi.translate(41004).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)

  
@AppMediator.register('REMOVE_ROM_LAUNCHER')
def cmd_remove_rom_launchers(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)        
        rom = repository.find_rom(rom_id)
    
        launchers = rom.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41002))
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        
        s = kodi.translate(41103)
        selected_option: ROMLauncherAddon = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        logger.debug(f'Selected {selected_option.get_id()}')
        if not kodi.dialog_yesno(kodi.translate(41059).format(selected_option.get_name())):
            logger.debug('Cancelled operation.')
            AppMediator.async_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        repository.remove_launcher(rom.get_id(), selected_option.get_id())
        logger.info(f'Removed launcher#{selected_option.get_id()}')
        uow.commit()
    
    kodi.notify(kodi.translate(41004).format(selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)

      
@AppMediator.register('SET_DEFAULT_COLLECTION_LAUNCHER')
def cmd_set_default_romcollection_launchers(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollection_repository = ROMCollectionRepository(uow)
        romcollection = romcollection_repository.find_romcollection(romcollection_id)
    
        launchers = romcollection.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41003))
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        
        s = kodi.translate(41104)
        selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('SET_DEFAULT_COLLECTION_LAUNCHER: Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug(f'SET_DEFAULT_COLLECTION_LAUNCHER: Selected {selected_option}')
        romcollection.set_launcher_as_default(selected_option)
        romcollection_repository.update_romcollection(romcollection)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION_LAUNCHERS', args)

    
@AppMediator.register('SET_DEFAULT_SOURCE_LAUNCHER')
def cmd_set_default_source_launchers(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        source = source_repository.find(source_id)

        launchers = source.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41168))
            AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = launcher.get_name()
        
        s = kodi.translate(41104)
        selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug(f'Selected {selected_option}')
        source.set_launcher_as_default(selected_option)
        source_repository.update_source(source)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_SOURCE_LAUNCHERS', args)


@AppMediator.register('SET_DEFAULT_ROM_LAUNCHER')
def cmd_set_default_rom_launchers(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
    
        launchers = rom.get_launchers()
        if len(launchers) == 0:
            kodi.notify(kodi.translate(41002))
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        options = collections.OrderedDict()
        for launcher in launchers:
            options[launcher.get_id()] = kodi.get_listitem(launcher.get_name(), launcher.get_addon_name())
        
        s = kodi.translate(41104)
        selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        
        if selected_option is None:
            # >> Exits context menu
            logger.debug('Selected None. Closing context menu')
            AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)
            return
        
        # >> Execute subcommand. May be atomic, maybe a submenu.
        logger.debug(f'Selected {selected_option}')
        rom.set_launcher_as_default(selected_option)
        repository.update_rom(rom)
        uow.commit()
    
    AppMediator.sync_cmd('EDIT_ROM_LAUNCHERS', args)


# -------------------------------------------------------------------------------------------------
# ROMCollection Launcher executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('EXECUTE_ROM')
def cmd_execute_rom_with_launcher(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        rom_repository = ROMsRepository(uow)
        romcollection_repository = ROMCollectionRepository(uow)
        source_repository = SourcesRepository(uow)
        addon_repository = AelAddonRepository(uow)

        rom = rom_repository.find_rom(rom_id)
        logger.info(f'Executing ROM {rom.get_name()}')
        
        romcollections = romcollection_repository.find_romcollections_by_rom(rom.get_id())
        source = source_repository.find(rom.get_scanned_by())
        launchers = rom.get_launchers()
        if source:
            launchers.extend(source.get_launchers())
        
        for romcollection in romcollections:
            launchers.extend(romcollection.get_launchers())
        
        if launchers is None or len(launchers) == 0:
            logger.warning(f'No launcher configured for ROM {rom.get_name()}')
            if not settings.getSettingAsBool('fallback_to_retroplayer'):
                kodi.notify_warn(kodi.translate(41001))
                return
            
            logger.info('Automatic fallback to Retroplayer as launcher applied.')
            retroplayer_addon = addon_repository.find_by_addon_id(constants.RETROPLAYER_LAUNCHER_APP_NAME, constants.AddonType.LAUNCHER)
            retroplayer_launcher = ROMLauncherAddonFactory.create(retroplayer_addon, {})
            launchers.append(retroplayer_launcher)
            
    selected_launcher = launchers[0]
    if len(launchers) > 1:
        launcher_options = collections.OrderedDict()
        preselected = None
        for launcher in launchers:
            launcher_options[launcher] = launcher.get_name()
            if launcher.is_default():
                preselected = launcher
        dialog = kodi.OrdDictionaryDialog()
        selected_launcher = dialog.select(kodi.translate(41105), launcher_options, preselect=preselected)

    if selected_launcher is None:
        return
    
    selected_launcher.launch(rom)
    AppMediator.async_cmd('ROM_WAS_LAUNCHED', args)
