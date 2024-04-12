# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (ROM management)
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

from akl import constants, platforms
from akl.utils import kodi, text, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import CategoryRepository, ROMsRepository, ROMCollectionRepository, UnitOfWork
from resources.lib.repositories import SourcesRepository

from resources.lib.domain import g_assetFactory

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------------------
# ROM context menu.
# -------------------------------------------------------------------------------------------------


# --- Main menu command ---
@AppMediator.register('EDIT_ROM')
def cmd_edit_rom(args):
    logger.debug('EDIT_ROM: cmd_edit_rom() BEGIN')
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    if rom_id is None:
        logger.warning('cmd_edit_rom(): No ROM id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

    options = collections.OrderedDict()
    options['ROM_EDIT_METADATA'] = kodi.translate(40853)
    options['ROM_EDIT_ASSETS'] = kodi.translate(40854)
    options['ROM_EDIT_DEFAULT_ASSETS'] = kodi.translate(40859)
    options['EDIT_ROM_STATUS'] = kodi.translate(42013).format(
        kodi.translate(rom.get_finished_str_code()))
    if rom.has_launchers():
        options['EDIT_ROM_LAUNCHERS'] = kodi.translate(42016)
    else:
        options['ADD_ROM_LAUNCHER'] = kodi.translate(42017)
    if rom.amount_of_associated_collections() > 0:
        options['REMOVE_ROM_FROM_COLLECTION'] = kodi.translate(42092)
        
    options['DELETE_ROM'] = kodi.translate(42018)
    options['SCRAPE_ROM'] = kodi.translate(40855)

    s = kodi.translate(41092).format(rom.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROM: Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_ROM: Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


# --- Submenu commands ---
@AppMediator.register('ROM_EDIT_METADATA')
def cmd_rom_metadata(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
    plot_str = text.limit_string(rom.get_plot(), constants.PLOT_STR_MAXSIZE)
    rating = rom.get_rating() if rom.get_rating() != -1 else kodi.translate(42021)
    NFO_FileName = rom.get_nfo_file()
    NFO_found_str = kodi.translate(42019) if NFO_FileName and NFO_FileName.exists() else kodi.translate(42020)

    options = collections.OrderedDict()
    options['ROM_EDIT_METADATA_TITLE'] = kodi.translate(40863).format(rom.get_name())
    options['ROM_EDIT_METADATA_PLATFORM'] = kodi.translate(40864).format(rom.get_platform())
    options['ROM_EDIT_METADATA_RELEASEYEAR'] = kodi.translate(40865).format(rom.get_releaseyear())
    options['ROM_EDIT_METADATA_GENRE'] = kodi.translate(40867).format(rom.get_genre())
    options['ROM_EDIT_METADATA_DEVELOPER'] = kodi.translate(40868).format(rom.get_developer())
    options['ROM_EDIT_METADATA_NPLAYERS'] = kodi.translate(40871).format(rom.get_number_of_players())
    options['ROM_EDIT_METADATA_NPLAYERS_ONL'] = kodi.translate(40872).format(rom.get_number_of_players_online())
    options['ROM_EDIT_METADATA_ESRB'] = kodi.translate(40874).format(rom.get_esrb_rating())
    options['ROM_EDIT_METADATA_PEGI'] = kodi.translate(40873).format(rom.get_pegi_rating())
    options['ROM_EDIT_METADATA_RATING'] = kodi.translate(40869).format(rating)
    options['ROM_EDIT_METADATA_PLOT'] = kodi.translate(40870).format(plot_str)
    options['ROM_EDIT_METADATA_TAGS'] = kodi.translate(40866)
    options['ROM_EDIT_METADATA_BOXSIZE'] = kodi.translate(40875).format(rom.get_box_sizing())
    options['ROM_LOAD_PLOT'] = kodi.translate(40879)
    options['ROM_IMPORT_NFO_FILE_DEFAULT'] = kodi.translate(40876).format(NFO_found_str)
    options['ROM_IMPORT_NFO_FILE_BROWSE'] = kodi.translate(40877)
    options['ROM_SAVE_NFO_FILE_DEFAULT'] = kodi.translate(40878)
    options['SCRAPE_ROM_METADATA'] = kodi.translate(40880)

    s = kodi.translate(41093).format(rom.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('cmd_rom_metadata(EDIT_METADATA) Selected NONE')
        AppMediator.sync_cmd('EDIT_ROM', args)
        return

    # >> Execute edit metadata atomic subcommand.
    # >> Then, execute recursively this submenu again.
    logger.debug(f'cmd_rom_metadata(EDIT_METADATA) Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)

  
@AppMediator.register('ROM_EDIT_ASSETS')
def cmd_rom_assets(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
       
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        source_repository = SourcesRepository(uow)
        source = source_repository.find(rom.get_scanned_by())
        
        romcollection_repository = ROMCollectionRepository(uow)
        rom_romcollections = romcollection_repository.find_romcollections_by_rom(rom_id)
        rom_collection_ids = [collection.get_id() for collection in rom_romcollections]
                
        selected_asset_to_edit = editors.edit_object_assets(rom, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROM', args)
            return
        
        if selected_asset_to_edit == editors.SCRAPE_CMD:
            AppMediator.sync_cmd(editors.SCRAPE_CMD, args)
            return
        
        assets_root_path = source.get_assets_root_path() if source else None
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns a command other than scrape or None changes were made.
        cmd = editors.edit_asset(rom, asset, assets_root_path)
        if cmd is not None:
            if cmd == 'SCRAPE_ASSET':
                args['selected_asset'] = asset.id
                AppMediator.sync_cmd('SCRAPE_ROM_ASSET', args)
                return
            
            repository.update_rom(rom)
            uow.commit()
            for romcollection_id in rom_collection_ids:
                AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})

    AppMediator.sync_cmd('ROM_EDIT_ASSETS', {'rom_id': rom_id, 'selected_asset': asset.id})


@AppMediator.register('ROM_EDIT_DEFAULT_ASSETS')
def cmd_rom_edit_default_assets(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        selected_asset_to_edit = editors.edit_object_default_assets(rom, preselected_option)
        if selected_asset_to_edit is None:
            args["selected_asset"] = None
            AppMediator.sync_cmd('EDIT_ROM', args)
            return

        if editors.edit_default_asset(rom, selected_asset_to_edit):
            repository.update_rom(rom)
            uow.commit()
        
    AppMediator.sync_cmd('ROM_EDIT_DEFAULT_ASSETS', {'rom_id': rom.get_id(), 'selected_asset': selected_asset_to_edit.id})         


@AppMediator.register('REMOVE_ROM_FROM_COLLECTION')
def cmd_rom_remove(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    
    with uow:
        roms_repository = ROMsRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        
        rom = roms_repository.find_rom(rom_id)
        romcollections = romcollections_repository.find_romcollections_by_rom(rom_id)
        
        options = collections.OrderedDict()
        for collection in romcollections:
            options[collection] = collection.get_name()

        s = kodi.translate(40866)
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        if selected_option is None:
            AppMediator.sync_cmd('EDIT_ROM', args)
            return
        
        romcollections_repository.remove_rom_from_romcollection(selected_option.get_id(), rom.get_id())
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': selected_option.get_id()})
    
    kodi.notify(kodi.translate(41196).format(rom.get_name(), selected_option.get_name()))
    AppMediator.sync_cmd('EDIT_ROM', args)


@AppMediator.register('DELETE_ROM')
def cmd_rom_delete(args):
    rom_id: str = args['rom_id'] if 'rom_id' in args else None
    romcollections = []
    categories = []
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        category_repository = CategoryRepository(uow)
        
        rom = roms_repository.find_rom(rom_id)

        question = kodi.translate(41056).format(rom.get_name())
        ret = kodi.dialog_yesno(question)
        if not ret:
            AppMediator.sync_cmd('EDIT_ROM', args)
            return
        
        romcollections = list(romcollections_repository.find_romcollections_by_rom(rom_id))
        categories = list(category_repository.find_categories_by_rom(rom_id))
      
        logger.info(f'Deleting ROM "{rom.get_name()}" ID {rom.get_id()}')
        roms_repository.delete_rom(rom.get_id())
        uow.commit()
        
    for romcollection in romcollections:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
    for category in categories:
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
    AppMediator.async_cmd('RENDER_VIRTUAL_VIEWS')
    
    kodi.notify(kodi.translate(41024).format(rom.get_name()))


# --- Atomic commands ---
@AppMediator.register('ROM_EDIT_METADATA_TITLE')
def cmd_rom_metadata_title(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, kodi.translate(40812), rom.get_name, rom.set_name):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_TITLE_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_PLATFORM')
def cmd_rom_metadata_platform(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, kodi.translate(40807), platforms.AKL_platform_list,
                                      rom.get_platform, rom.set_platform):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
                        
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_ESRB')
def cmd_rom_metadata_esrb(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, kodi.translate(40804), constants.ESRB_LIST,
                                      rom.get_esrb_rating, rom.set_esrb_rating):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_ESRB_ID})
                
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_PEGI')
def cmd_rom_metadata_pegi(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, kodi.translate(40805), constants.PEGI_LIST,
                                      rom.get_pegi_rating, rom.set_pegi_rating):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_PEGI_ID})
                
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_RELEASEYEAR')
def cmd_rom_metadata_releaseyear(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, kodi.translate(40803), rom.get_releaseyear, rom.set_releaseyear):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_YEARS_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_GENRE')
def cmd_rom_metadata_genre(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, kodi.translate(40801), rom.get_genre, rom.set_genre):
            repository.update_rom(rom)
            uow.commit()            
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_GENRE_ID})
                    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_DEVELOPER')
def cmd_rom_metadata_developer(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, kodi.translate(40802), rom.get_developer, rom.set_developer):
            repository.update_rom(rom)
            uow.commit()    
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_DEVELOPER_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_NPLAYERS')
def cmd_rom_metadata_nplayers(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        default_options = list(constants.NPLAYERS_LIST.keys())
        menu_list = [
            kodi.translate(42001),
            kodi.translate(42022)
        ] + default_options
        selected_option = kodi.ListDialog().select(kodi.translate(41094), menu_list)
        
        if selected_option is None or selected_option < 0:
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

        if selected_option == 0:
            rom.set_number_of_players('')
    
        if selected_option == 1:
            # >> Manual entry. Open a text entry dialog.
            if not editors.edit_field_by_int(rom, kodi.translate(40808), rom.get_number_of_players, rom.set_number_of_players):
                AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
                return

        if selected_option > 1:
            list_idx = selected_option - 2
            np_key = default_options[list_idx]
            rom.set_number_of_players(constants.NPLAYERS_LIST[np_key])
                
        repository.update_rom(rom)
        uow.commit()
        AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_NPLAYERS_ID})
        kodi.notify(kodi.translate(41025))
        
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_NPLAYERS_ONL')
def cmd_rom_metadata_nplayers_online(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        default_options = list(constants.NPLAYERS_LIST.keys())
        menu_list = [
            kodi.translate(42001),
            kodi.translate(42022)
        ] + default_options
        selected_option = kodi.ListDialog().select(kodi.translate(41095), menu_list)
        
        if selected_option is None or selected_option < 0:
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

        if selected_option == 0:
            rom.set_number_of_players_online('')
    
        if selected_option == 1:
            # >> Manual entry. Open a number entry dialog.
            if not editors.edit_field_by_int(rom, kodi.translate(40809), rom.get_number_of_players, rom.set_number_of_players):
                AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
                return

        if selected_option > 1:
            list_idx = selected_option - 2
            np_key = default_options[list_idx]
            rom.set_number_of_players_online(constants.NPLAYERS_LIST[np_key])
                
        repository.update_rom(rom)
        uow.commit()
        AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
        AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_NPLAYERS_ID})
        kodi.notify(kodi.translate(41026))
        
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_RATING')
def cmd_rom_metadata_rating(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_rating(rom, rom.get_rating, rom.set_rating):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': constants.VCATEGORY_RATING_ID})
            
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_PLOT')
def cmd_rom_metadata_plot(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if editors.edit_field_by_str(rom, kodi.translate(40811), rom.get_plot, rom.set_plot):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_EDIT_METADATA_TAGS')
def cmd_rom_metadata_tags(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        selected_option = 1
        did_remove_tag = False

        options = collections.OrderedDict()
        options['ROM_ADD_METADATA_TAGS'] = kodi.translate(42023)
        options['ROM_CLEAR_METADATA_TAGS'] = kodi.translate(42024)

        for tag in rom.get_tags():
            options[tag] = tag

        while selected_option is not None:
            s = kodi.translate(40866)
            selected_option = kodi.OrdDictionaryDialog().select(s, options)
            if selected_option is None:
                continue
            
            if selected_option == 'ROM_ADD_METADATA_TAGS' or selected_option == 'ROM_CLEAR_METADATA_TAGS':
                break
            
            if not kodi.dialog_yesno(kodi.translate(41057).format(selected_option)):
                continue

            did_remove_tag = True
            logger.debug(f'cmd_rom_metadata_remove_tag() Remove tag {options[selected_option]}')
            kodi.notify(kodi.translate(41027).format(selected_option))
            del options[selected_option]
            rom.remove_tag(selected_option)

        if did_remove_tag:
            kodi.notify(kodi.translate(41028))
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})

        if selected_option is None:
            # >> Return recursively to parent menu.
            logger.debug('cmd_rom_metadata_tags() Selected NONE')
            AppMediator.sync_cmd('ROM_EDIT_METADATA', args)
            return

    logger.debug(f'cmd_rom_metadata_tags() Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('ROM_ADD_METADATA_TAGS')
def cmd_rom_metadata_add_tag(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        available_tags = repository.find_all_tags()

        options = collections.OrderedDict()
        options['MANUAL'] = kodi.translate(42025)
        if available_tags is not None and len(available_tags) > 0:
            options.update({value: key for key, value in available_tags.items()})
        
        selected_option = 'MANUAL'
        did_add_tag = False

        while selected_option is not None:
            selected_option = kodi.OrdDictionaryDialog().select(kodi.translate(41096), options)
                
            if selected_option is None:
                break
            
            if selected_option == 'MANUAL':
                tag = kodi.dialog_keyboard(kodi.translate(40814))
                if tag is not None:
                    did_add_tag = True
                    logger.debug(f'cmd_rom_metadata_add_tag() Adding tag "{tag}"')
                    kodi.notify(kodi.translate(41029).format(tag))
                    rom.add_tag(tag)
            else:
                tag = options[selected_option]
                did_add_tag = True
                logger.debug(f'cmd_rom_metadata_add_tag() Adding tag "{tag}"')
                kodi.notify(kodi.translate(41029).format(tag))
                rom.add_tag(tag)

        if did_add_tag:
            kodi.notify(kodi.translate(41030))
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA_TAGS', args)


@AppMediator.register('ROM_CLEAR_METADATA_TAGS')
def cmd_rom_metadata_clear_tags(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if kodi.dialog_yesno(kodi.translate(41058).format(rom.get_name())):
            rom.clear_tags()
            repository.update_rom(rom)
            uow.commit()
            kodi.notify(kodi.translate(41031).format(rom.get_name()))
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA_TAGS', args)


@AppMediator.register('ROM_EDIT_METADATA_BOXSIZE')
def cmd_rom_metadata_boxsize(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)

        if editors.edit_field_by_list(rom, kodi.translate(40816), constants.BOX_SIZES,
                                      rom.get_box_sizing, rom.set_box_sizing):
            repository.update_rom(rom)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_LOAD_PLOT')
def cmd_rom_load_plot(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    plot_file = kodi.browse(text=kodi.translate(41157), mask='.txt|.dat')
    logger.debug('cmd_rom_load_plot() Dialog().browse returned "{0}"'.format(plot_file))
    if not plot_file:
        return
    plot_FileName = io.FileName(plot_file)
    if not plot_FileName.exists():
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        file_data = editors.import_TXT_file(plot_FileName)
        rom.set_plot(file_data)
        
        repository.update_rom(rom)
        uow.commit()
        kodi.notify(kodi.translate(41032))
    
    AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('EDIT_ROM_STATUS')
def cmd_rom_status(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        rom.change_finished_status()
        repository.update_rom(rom)
        uow.commit()
    
    kodi.dialog_OK(kodi.translate(42091).format(rom.get_name(), kodi.translate(rom.get_finished_str_code())))
    AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
    AppMediator.sync_cmd('EDIT_ROM', args)


# --- Import ROM metadata from NFO file (default location) ---
@AppMediator.register('ROM_IMPORT_NFO_FILE_DEFAULT')
def cmd_rom_import_nfo_file(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        NFO_file = rom.get_nfo_file()
        
        if not NFO_file:
            kodi.dialog_OK(kodi.translate(41148))
            return
        
        if rom.update_with_nfo_file(NFO_file):
            repository.update_rom(rom)
            uow.commit()
            kodi.notify(kodi.translate(41033).format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_IMPORT_NFO_FILE_BROWSE')
def cmd_rom_browse_import_nfo_file(args):    
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    NFO_file = kodi.browse(text=kodi.translate(41143), mask='.nfo')
    logger.debug('cmd_rom_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file:
        return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists():
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
        if rom.update_with_nfo_file(NFO_FileName):
            repository.update_rom(rom)
            uow.commit()
            kodi.notify(kodi.translate(41033).format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_ROM_VIEWS', {'rom_id': rom.get_id()})
            AppMediator.async_cmd('RENDER_VCATEGORY_VIEWS')
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('ROM_SAVE_NFO_FILE_DEFAULT')
def cmd_rom_save_nfo_file(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        rom = repository.find_rom(rom_id)
        
    NFO_FileName = rom.get_nfo_file()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        rom.export_to_NFO_file(NFO_FileName)
    except Exception:
        kodi.notify_warn(kodi.translate(41042).format(NFO_FileName.getPath()))
        logger.error("cmd_rom_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_rom_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify(kodi.translate(41034).format(NFO_FileName.getPath()))
    
    AppMediator.sync_cmd('ROM_EDIT_METADATA', args)


@AppMediator.register('MANAGE_ROM_TAGS')
def cmd_manage_rom_tags(args):

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        available_tags = repository.find_all_tags()

        options = collections.OrderedDict()
        options['ADD_TAG'] = kodi.translate(42023)
        if available_tags is not None and len(available_tags) > 0:
            options.update({value: key for key, value in available_tags.items()})

        selected_option = 'ADD_TAG'
        did_tag_change = False
        while selected_option is not None:
            s = kodi.translate(41097)
            selected_option = kodi.OrdDictionaryDialog().select(s, options)
            if selected_option is None:
                continue
            
            if selected_option == 'ADD_TAG':
                tag = kodi.dialog_keyboard(kodi.translate(40814))
                if tag is not None:
                    did_tag_change = True
                    logger.debug(f'cmd_manage_rom_tags() Adding tag "{tag}"')
                    kodi.notify(kodi.translate(41029).format(tag))
                    tag_id = repository.insert_tag(tag)
                    options[tag_id] = tag
                continue
                           
            if not kodi.dialog_yesno(kodi.translate(41057).format(options[selected_option])):
                continue

            did_tag_change = True
            logger.debug(f'cmd_manage_rom_tags() Remove tag {options[selected_option]}')
            kodi.notify(kodi.translate(41027).format(options[selected_option]))
            del options[selected_option]
            repository.delete_tag(selected_option)

        if did_tag_change:
            uow.commit()


@AppMediator.register('LINK_ROM')
def cmd_link_rom(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    
    destination_dialog = kodi.ListDialog()
    selected_type = destination_dialog.select(kodi.translate(41186), [
        kodi.translate(42513),  # COLLECTIONS [0]
        kodi.translate(42512)   # CATEGORIES [1]
    ])
    
    if selected_type is None:
        logger.debug("LINK_ROM: No destination type selected. Ending")
        return
            
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        collections_repository = ROMCollectionRepository(uow)
        categories_repository = CategoryRepository(uow)
                
        options = collections.OrderedDict()
        if selected_type == 0:
            romcollections = collections_repository.find_all_romcollections()
            for collection in romcollections:
                options[collection] = collection.get_name()
        else:
            categories = categories_repository.find_all_categories()
            for category in categories:
                options[category] = category.get_name()
                
        dialog = kodi.OrdDictionaryDialog()
        selected_destination = dialog.select(kodi.translate(41186), options)
        
        if selected_destination is None:
            logger.debug("LINK_ROM: No destination selected. Ending")
            return
        
        rom = repository.find_rom(rom_id)
        if selected_type == 0:
            collections_repository.add_rom_to_romcollection(selected_destination.get_id(), rom.get_id())
        else:
            categories_repository.add_rom_to_category(selected_destination.get_id(), rom.get_id())
                    
        uow.commit()
    
    if selected_type == 0:
        kodi.notify(kodi.translate(41188).format(rom.get_name(), selected_destination.get_name()))
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': selected_destination.get_id()})
    else:
        kodi.notify(kodi.translate(41187).format(rom.get_name(), selected_destination.get_name()))
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': selected_destination.get_id()})
