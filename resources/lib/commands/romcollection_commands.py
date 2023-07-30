# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection management)
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
from resources.lib.repositories import UnitOfWork, CategoryRepository, ROMCollectionRepository, ROMsRepository
from resources.lib.domain import ROMCollection, Category, g_assetFactory

logger = logging.getLogger(__name__)

@AppMediator.register('ADD_ROMCOLLECTION')
def cmd_add_collection(args):
    logger.debug('cmd_add_collection() BEGIN')
    parent_id = args['category_id'] if 'category_id' in args else None
    grand_parent_id = args['parent_category_id'] if 'parent_category_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        parent_category = repository.find_category(parent_id) if parent_id is not None else None
        grand_parent_category = repository.find_category(grand_parent_id) if grand_parent_id is not None else None
        
        if grand_parent_category is not None:
            options_dialog = kodi.ListDialog()
            selected_option = options_dialog.select(kodi.translate(41125), [
                parent_category.get_name(), 
                grand_parent_category.get_name()
            ])
            if selected_option is None:
                return
            if selected_option > 0:
                parent_category = grand_parent_category
    
        wizard = kodi.WizardDialog_Selection(None, 'platform', kodi.translate(41099), platforms.AKL_platform_list)
        wizard = kodi.WizardDialog_Dummy(wizard, 'm_name', '', _get_name_from_platform)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'm_name', kodi.translate(42037))
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'assets_path', kodi.translate(42038), 0, '')
        
        romcollection = ROMCollection()
        entity_data = romcollection.get_data_dic()
        entity_data = wizard.runWizard(entity_data)
        if entity_data is None:
            return
        
        romcollection.import_data_dic(entity_data)
        
        # --- create assets directory ---
        assets_path = entity_data['assets_path']
        assets_path_FN = io.FileName(assets_path)
        romcollection.set_assets_root_path(assets_path_FN, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=True)
                
        # --- Determine box size based on platform --
        platform = platforms.get_AKL_platform(entity_data['platform'])
        romcollection.set_box_sizing(platform.default_box_size)
        
        romcollection_repository = ROMCollectionRepository(uow)
        romcollection_repository.insert_romcollection(romcollection, parent_category)
        uow.commit()
        
        kodi.notify(kodi.translate(41017).format(romcollection.get_name()))
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': parent_category.get_id()})   
    
def _get_name_from_platform(input, item_key, entity_data):
    title = entity_data['platform']
    return title

# -------------------------------------------------------------------------------------------------
# ROMCollection context menu.
# -------------------------------------------------------------------------------------------------

# --- Main menu command ---
@AppMediator.register('EDIT_ROMCOLLECTION')
def cmd_edit_romcollection(args):

    logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() BEGIN')
    romcollection_id:str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    if romcollection_id is None:
        logger.warning('cmd_edit_romcollection(): No romcollection id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        cat_repository = CategoryRepository(uow)
        parent_id = romcollection.get_parent_id()
        category = cat_repository.find_category(romcollection.get_parent_id()) if parent_id is not None else None 
        category_name = kodi.translate(20010) if category is None else category.get_name()

    options = collections.OrderedDict()
    options['ROMCOLLECTION_EDIT_METADATA'] = kodi.translate(40853)
    options['ROMCOLLECTION_EDIT_ASSETS'] = kodi.translate(40854)
    options['ROMCOLLECTION_EDIT_DEFAULT_ASSETS'] = kodi.translate(40859)
    if romcollection.has_launchers():
        options['EDIT_ROMCOLLECTION_LAUNCHERS'] = kodi.translate(42016)
    else: 
        options['ADD_LAUNCHER'] = kodi.translate(42026)  
    options['ROMCOLLECTION_MANAGE_ROMS'] = kodi.translate(42039)
    options['EDIT_ROMCOLLECTION_CATEGORY'] = kodi.translate(42040).format(category_name)
    options['EDIT_ROMCOLLECTION_STATUS'] = kodi.translate(42041).format(kodi.translate(romcollection.get_finished_str_code()))
    options['EXPORT_ROMCOLLECTION'] = kodi.translate(42042)
    options['DELETE_ROMCOLLECTION'] = kodi.translate(42043)

    s = kodi.translate(41126).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('EDIT_ROMCOLLECTION: cmd_edit_romcollection() Selected {}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, {
        'romcollection_id': romcollection_id, 'category_id': romcollection.get_parent_id()
    })

# --- Submenu commands ---
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA')
def cmd_romcollection_metadata(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    plot_str = text.limit_string(romcollection.get_plot(), constants.PLOT_STR_MAXSIZE)
    rating = romcollection.get_rating() if romcollection.get_rating() != -1 else kodi.translate(42021)
    NFO_FileName = romcollection.get_NFO_name()
    NFO_found_str = kodi.translate(42019) if NFO_FileName.exists() else kodi.translate(42020)

    options = collections.OrderedDict()
    options['ROMCOLLECTION_EDIT_METADATA_TITLE'] = kodi.translate(40863).format(romcollection.get_name())
    options['ROMCOLLECTION_EDIT_METADATA_PLATFORM'] = kodi.translate(40864).format(romcollection.get_platform())
    options['ROMCOLLECTION_EDIT_METADATA_RELEASEYEAR'] = kodi.translate(40865).format(romcollection.get_releaseyear())
    options['ROMCOLLECTION_EDIT_METADATA_GENRE'] = kodi.translate(40867).format(romcollection.get_genre())
    options['ROMCOLLECTION_EDIT_METADATA_DEVELOPER'] = kodi.translate(40868).format(romcollection.get_developer())
    options['ROMCOLLECTION_EDIT_METADATA_RATING'] = kodi.translate(40869).format(rating)
    options['ROMCOLLECTION_EDIT_METADATA_PLOT'] = kodi.translate(40870).format(plot_str)
    options['ROMCOLLECTION_EDIT_METADATA_BOXSIZE'] = kodi.translate(40875).format(romcollection.get_box_sizing())
    options['ROMCOLLECTION_IMPORT_NFO_FILE_DEFAULT'] = kodi.translate(40876).format(NFO_found_str)
    options['ROMCOLLECTION_IMPORT_NFO_FILE_BROWSE'] = kodi.translate(40877)
    options['ROMCOLLECTION_SAVE_NFO_FILE_DEFAULT'] = kodi.translate(40878)

    s = kodi.translate(41127).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('cmd_romcollection_metadata(EDIT_METADATA) Selected NONE')
        AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
        return

    # >> Execute launcher edit metadata atomic subcommand.
    # >> Then, execute recursively this submenu again.
    logger.debug('cmd_romcollection_metadata(EDIT_METADATA) Selected {0}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)

@AppMediator.register('ROMCOLLECTION_EDIT_ASSETS')
def cmd_romcollection_edit_assets(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        selected_asset_to_edit = editors.edit_object_assets(romcollection, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return
        
        if selected_asset_to_edit == editors.SCRAPE_CMD:
            AppMediator.async_cmd(editors.SCRAPE_CMD, args)
            return
        #    globals.run_command(scrape_cmd, rom=obj_instance)
        #    edit_object_assets(obj_instance, selected_option)
        #    return True
        
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns a cmd other than None changes were made.
        if editors.edit_asset(romcollection, asset) is not None:
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_ASSETS', {'romcollection_id': romcollection.get_id(), 'selected_asset': asset.id})         

@AppMediator.register('ROMCOLLECTION_EDIT_DEFAULT_ASSETS')
def cmd_romcollection_edit_default_assets(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        selected_asset_to_edit = editors.edit_object_default_assets(romcollection, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return

        if editors.edit_default_asset(romcollection, selected_asset_to_edit):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})     

    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_DEFAULT_ASSETS', {'romcollection_id': romcollection.get_id(), 'selected_asset': selected_asset_to_edit.id})         
    
@AppMediator.register('EDIT_ROMCOLLECTION_STATUS')
def cmd_romcollection_status(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        romcollection.change_finished_status()
        kodi.dialog_OK(kodi.translate(41150).format(romcollection.get_name(), kodi.translate(romcollection.get_finished_str_code())))
        repository.update_romcollection(romcollection)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})     
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
    
#
# Remove ROMCollection
#
@AppMediator.register('DELETE_ROMCOLLECTION')
def cmd_romcollection_delete(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        romcollection_name = romcollection.get_name()
        
        if romcollection.num_roms() > 0:
            question = kodi.translate(41069).format(romcollection_name, romcollection.num_roms()) + \
                       kodi.translate(41066).format(romcollection_name)
        else:
            question = kodi.translate(41066).format(romcollection_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret: return
            
        logger.info('Deleting romcollection "{}" ID {}'.format(romcollection_name, romcollection.get_id()))
        repository.delete_romcollection(romcollection.get_id())
        uow.commit()
        
    kodi.notify(kodi.translate(41018).format(romcollection_name))
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.async_cmd('CLEANUP_VIEWS')
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)

# --- Atomic commands ---
# --- Edition of the launcher name ---
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_TITLE')
def cmd_romcollection_metadata_title(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, kodi.translate(40812), romcollection.get_name, romcollection.set_name):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_PLATFORM')
def cmd_romcollection_metadata_platform(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        if editors.edit_field_by_list(romcollection, kodi.translate(40807), platforms.AKL_platform_list,
                                    romcollection.get_platform, romcollection.set_platform):
            repository.update_romcollection(romcollection)
            update_roms_too = kodi.dialog_yesno(kodi.translate(40955))
            
            if update_roms_too:
                roms_repository = ROMsRepository(uow)
                roms_to_update = roms_repository.find_roms_by_romcollection(romcollection)
                platform_to_apply = romcollection.get_platform()
                for rom in roms_to_update:
                    rom.set_platform(platform_to_apply)
                    roms_repository.update_rom(rom)

            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_RELEASEYEAR')
def cmd_romcollection_metadata_releaseyear(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, kodi.translate(40803), romcollection.get_releaseyear, romcollection.set_releaseyear):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_GENRE')
def cmd_romcollection_metadata_genre(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None 
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, kodi.translate(40801), romcollection.get_genre, romcollection.set_genre):
            repository.update_romcollection(romcollection)
            uow.commit()            
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
    
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_DEVELOPER')
def cmd_romcollection_metadata_developer(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, kodi.translate(40802), romcollection.get_developer, romcollection.set_developer):
            repository.update_romcollection(romcollection)
            uow.commit()    
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_RATING')
def cmd_romcollection_metadata_rating(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None   
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_rating(romcollection, romcollection.get_rating, romcollection.set_rating):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_PLOT')
def cmd_romcollection_metadata_plot(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if editors.edit_field_by_str(romcollection, kodi.translate(40811), romcollection.get_plot, romcollection.set_plot):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
    
@AppMediator.register('ROMCOLLECTION_EDIT_METADATA_BOXSIZE')
def cmd_romcollection_metadata_boxsize(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None  
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        if editors.edit_field_by_list(romcollection, kodi.translate(40816), constants.BOX_SIZES,
                                    romcollection.get_box_sizing, romcollection.set_box_sizing):
            repository.update_romcollection(romcollection)
            uow.commit()
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})            
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

# --- Import launcher metadata from NFO file (default location) ---
@AppMediator.register('ROMCOLLECTION_IMPORT_NFO_FILE_DEFAULT')
def cmd_romcollection_import_nfo_file(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        NFO_file = romcollection.get_NFO_name()
        
        if romcollection.import_NFO_file(NFO_file):
            repository.update_romcollection(romcollection)
            uow.commit()
            kodi.notify(kodi.translate(41019).format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_IMPORT_NFO_FILE_BROWSE')
def cmd_romcollection_browse_import_nfo_file(args):    
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    
    NFO_file = kodi.browse(text=kodi.translate(41143), mask='.nfo')
    logger.debug('cmd_romcollection_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file: return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists(): return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
        if romcollection.import_NFO_file(NFO_FileName):
            repository.update_romcollection(romcollection)
            uow.commit()
            kodi.notify(kodi.translate(41019).format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('ROMCOLLECTION_SAVE_NFO_FILE_DEFAULT')
def cmd_romcollection_save_nfo_file(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        
    NFO_FileName = romcollection.get_NFO_name()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        romcollection.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn(kodi.translate(41042).format(NFO_FileName.getPath()))
        logger.error("cmd_romcollection_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_romcollection_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify(kodi.translate(41020).format(NFO_FileName.getPath()))
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)

@AppMediator.register('EDIT_ROMCOLLECTION_CATEGORY')
def cmd_romcollection_change_category(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository      = ROMCollectionRepository(uow)
        cat_repository  = CategoryRepository(uow)
        
        romcollection   = repository.find_romcollection(romcollection_id)
        all_categories  = cat_repository.find_all_categories()
        root_category   = cat_repository.find_category(constants.VCATEGORY_ADDONROOT_ID)
        
        previous_category_id = romcollection.get_parent_id()
        if previous_category_id is None: previous_category_id = root_category.get_id()

        options = collections.OrderedDict()
        options[root_category] = root_category.get_name()
        options.update({category:category.get_name() for category in all_categories})

        selected_option = kodi.OrdDictionaryDialog().select(kodi.translate(41128), options)
        if selected_option is None:
            # >> Return recursively to parent menu.
            logger.debug('cmd_romcollection_change_category(): Selected NONE')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return
        
        selected_category:Category = selected_option
        if not kodi.dialog_yesno(kodi.translate(41065).format(romcollection.get_name(), selected_category.get_name())):
            logger.debug('cmd_romcollection_change_category(): Cancelled')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return

        logger.debug(f'cmd_romcollection_change_category() Moving collection#{romcollection_id} to category#{selected_category.get_id()}')        
        repository.update_romcollection_parent_reference(romcollection, selected_category)
        uow.commit() 
        
        kodi.notify(kodi.translate(41021)) 
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': selected_category.get_id()})   
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': previous_category_id})          
    AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            
@AppMediator.register('ROMCOLLECTION_EXPORT_ROMCOLLECTION_XML')
# --- Export Category XML configuration ---
def cmd_romcollection_export_xml(args):
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
    
    romcollection_fn_str = 'Romset_' + text.str_to_filename_str(romcollection.get_name()) + '.xml'
    logger.debug('cmd_romcollection_export_xml() Exporting ROMCollection configuration')
    logger.debug('cmd_romcollection_export_xml() Name     "{0}"'.format(romcollection.get_name()))
    logger.debug('cmd_romcollection_export_xml() ID       {0}'.format(romcollection.get_id()))
    logger.debug('cmd_romcollection_export_xml() l_fn_str "{0}"'.format(romcollection_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = kodi.browse(type=0, text='Select directory to export XML')
    if not dir_path: 
        AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
        return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = io.FileName(dir_path).pjoin(romcollection_fn_str)
    if export_FN.exists():
        ret = kodi.dialog_yesno(kodi.translate(41052).format(export_FN.getPath()))
        if not ret:
            kodi.notify_warn(kodi.translate(41022))
            AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AKL code.
    try:
        romcollection.export_to_file(export_FN)
    except constants.AddonError as E:
        kodi.notify_warn(str(E))
    else:
        kodi.notify(kodi.translate(41023).format(romcollection.get_name()))
    
    AppMediator.sync_cmd('ROMCOLLECTION_EDIT_METADATA', args)