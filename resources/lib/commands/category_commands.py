# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (category management)
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

# --- Python standard source ---
from __future__ import unicode_literals
from __future__ import division

import logging
import collections

from akl.utils import kodi, text, io
from akl import constants

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import UnitOfWork, CategoryRepository
from resources.lib.domain import Category, g_assetFactory

logger = logging.getLogger(__name__)


@AppMediator.register('ADD_ITEM')
def cmd_add_item(args):
    logger.debug('cmd_add_item() BEGIN')
    
    options = collections.OrderedDict()
    options['ADD_SOURCE'] = kodi.translate(42506)
    options['ADD_LAUNCHER'] = kodi.translate(42514)
    options['ADD_CATEGORY'] = kodi.translate(42501)
    options['ADD_ROMCOLLECTION'] = kodi.translate(42503)
    
    selected_option = kodi.OrdDictionaryDialog().select(
        kodi.translate(41192),
        options)
    
    if selected_option is None:
        return
    
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('ADD_CATEGORY')
def cmd_add_category(args):
    logger.debug('cmd_add_category() BEGIN')
    parent_id = args['category_id'] if 'category_id' in args else None
    grand_parent_id = args['parent_category_id'] if 'parent_category_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        parent_category = repository.find_category(parent_id) if parent_id is not None else None
        grand_parent_category = repository.find_category(grand_parent_id) if grand_parent_id is not None else None
        
        if grand_parent_category is not None:
            options_dialog = kodi.ListDialog()
            selected_option = options_dialog.select(kodi.translate(41084), [
                parent_category.get_name(),
                grand_parent_category.get_name()
            ])
            if selected_option > 0:
                parent_category = grand_parent_category
    
        # --- Get new Category name ---
        name = kodi.dialog_keyboard(kodi.translate(41085))
        if not name:
            return
        
        category = Category()
        category.set_name(name)
    
        # --- Save Category ---
        repository.insert_category(category, parent_category)
        uow.commit()
        
        kodi.notify(kodi.translate(41036).format(category.get_name()))
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': parent_category.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})


@AppMediator.register('EDIT_CATEGORY')
def cmd_edit_category(args):
    logger.debug('EDIT_CATEGORY: BEGIN')
    category_id: str = args['category_id'] if 'category_id' in args else None
    
    if category_id is None:
        logger.warning('cmd_edit_category(): No category id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        parent_category = repository.find_category(category.get_parent_id())
        if parent_category is None:
            parent_category = repository.find_category(constants.VCATEGORY_ADDONROOT_ID)
        
        options = collections.OrderedDict()
        options['CATEGORY_EDIT_METADATA'] = kodi.translate(40853)
        options['CATEGORY_EDIT_ASSETS'] = kodi.translate(40854)
        options['CATEGORY_EDIT_DEFAULT_ASSETS'] = kodi.translate(40859)
        options['EDIT_PARENT_CATEGORY'] = kodi.translate(42040).format(parent_category.get_name())
        options['CATEGORY_STATUS'] = f'{kodi.translate(40860)} {kodi.translate(category.get_finished_str_code())}'
        options['EXPORT_CATEGORY_XML'] = kodi.translate(40861)
        options['DELETE_CATEGORY'] = kodi.translate(40862)
        
        s = f'{kodi.translate(40950)} "{category.get_name()}"'
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
    
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_CATEGORY: Selected None. Closing context menu')
        return

    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_CATEGORY: Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


# --- Submenu command ---
@AppMediator.register('CATEGORY_EDIT_METADATA')
def cmd_edit_metadata_category(args):
    logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() BEGIN')
    category_id = args['category_id'] if 'category_id' in args else None
    selected_option = None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        NFO_FileName = category.get_NFO_name()
        NFO_found_str = kodi.translate(42019) if NFO_FileName.exists() else kodi.translate(42020)
        plot_str = text.limit_string(category.get_plot(), constants.PLOT_STR_MAXSIZE)

        options = collections.OrderedDict()
        options['CATEGORY_EDIT_METADATA_TITLE'] = kodi.translate(40863).format(category.get_name())
        options['CATEGORY_EDIT_METADATA_RELEASEYEAR'] = kodi.translate(40865).format(category.get_releaseyear())
        options['CATEGORY_EDIT_METADATA_GENRE'] = kodi.translate(40867).format(category.get_genre())
        options['CATEGORY_EDIT_METADATA_DEVELOPER'] = kodi.translate(40868).format(category.get_developer())
        options['CATEGORY_EDIT_METADATA_RATING'] = kodi.translate(40869).format(category.get_rating())
        options['CATEGORY_EDIT_METADATA_PLOT'] = kodi.translate(40870).format(plot_str)
        options['CATEGORY_IMPORT_NFO_FILE'] = kodi.translate(40876).format(NFO_found_str)
        options['CATEGORY_IMPORT_NFO_FILE_BROWSE'] = kodi.translate(40877)
        options['CATEGORY_SAVE_NFO_FILE'] = kodi.translate(40878)
            
        s = kodi.translate(41086).format(category.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
    if selected_option is None:
        # >> Return recursively to parent menu.
        logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() Selected NONE')
        AppMediator.sync_cmd('EDIT_CATEGORY', args)
        return
    
    # >> Execute category edit metadata atomic subcommand.
    logger.debug('CATEGORY_EDIT_METADATA: cmd_edit_metadata_category() Selected {0}'.format(selected_option))
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('CATEGORY_EDIT_ASSETS')
def cmd_category_edit_assets(args):
    category_id = args['category_id'] if 'category_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        selected_asset_to_edit = editors.edit_object_assets(category, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.async_cmd('EDIT_CATEGORY', args)
            return
        
        asset = g_assetFactory.get_asset_info(selected_asset_to_edit)
        #  if selected_asset_to_edit == editors.SCRAPE_CMD:
        #    AppMediator.async_cmd('EDIT_CATEGORY_MENU', args)
        #    globals.run_command(scrape_cmd, rom=obj_instance)
        #    edit_object_assets(obj_instance, selected_option)
        #    return True
        
        # >> Execute edit asset menu subcommand. Then, execute recursively this submenu again.
        # >> The menu dialog is instantiated again so it reflects the changes just edited.
        # >> If edit_asset() returns a cmd other than None changes were made.
        if editors.edit_asset(category, asset) is not None:
            repository.update_category(category)
            uow.commit()
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
        
    AppMediator.sync_cmd('CATEGORY_EDIT_ASSETS', {'category_id': category_id, 'selected_asset': asset.id})


@AppMediator.register('CATEGORY_EDIT_DEFAULT_ASSETS')
def cmd_category_edit_default_assets(args):
    category_id = args['category_id'] if 'category_id' in args else None
    preselected_option = args['selected_asset'] if 'selected_asset' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        selected_asset_to_edit = editors.edit_object_default_assets(category, preselected_option)
        if selected_asset_to_edit is None:
            AppMediator.sync_cmd('EDIT_CATEGORY', args)
            return

        if editors.edit_default_asset(category, selected_asset_to_edit):
            repository.update_category(category)
            uow.commit()   
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    
    AppMediator.sync_cmd('CATEGORY_EDIT_DEFAULT_ASSETS', {'category_id': category_id, 'selected_asset': selected_asset_to_edit.id})


@AppMediator.register('CATEGORY_STATUS')
def cmd_category_status(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        category.change_finished_status()
        kodi.dialog_OK(kodi.translate(41146).format(category.get_name(), kodi.translate(category.get_finished_str_code())))
        repository.update_category(category)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', args) 
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.sync_cmd('EDIT_CATEGORY', args)

   
#
# Remove category. Also removes launchers in that category
#
@AppMediator.register('DELETE_CATEGORY')
def cmd_category_delete(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        category_name = category.get_name()
        
        if category.has_items():
            question = kodi.translate(41067).format(category_name, category.num_categories(), category.num_romcollections()) \
                + kodi.translate(41066).format(category_name)
        else:
            question = kodi.translate(41068).format(category_name) + kodi.translate(41066).format(category_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret:
            return
            
        logger.info(f'Deleting category "{category_name}" ID {category.get_id()}')
        repository.delete_category(category_id)
        uow.commit()
        
    kodi.notify(kodi.translate(41037).format(category_name))
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.async_cmd('CLEANUP_VIEWS')
    AppMediator.sync_cmd('EDIT_CATEGORY', args)


# -------------------------------------------------------------------------------------------------
# Category context menu atomic commands.
# Only Category context menu functions have debug statemets. This debug messages are to
# debug the context menu recursive logic.
# -------------------------------------------------------------------------------------------------
# --- Atomic commands ---
@AppMediator.register('CATEGORY_EDIT_METADATA_TITLE')
def cmd_category_metadata_title(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_field_by_str(category, kodi.translate(40812), category.get_name, category.set_name):
            repository.update_category(category)
            uow.commit()
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})            
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)
    

@AppMediator.register('CATEGORY_EDIT_METADATA_RELEASEYEAR')
def cmd_category_metadata_releaseyear(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_field_by_str(category, kodi.translate(40803), category.get_releaseyear, category.set_releaseyear):
            repository.update_category(category)
            uow.commit()
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_EDIT_METADATA_GENRE')
def cmd_category_metadata_genre(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_field_by_str(category, kodi.translate(40801), category.get_genre, category.set_genre):
            repository.update_category(category)
            uow.commit()            
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})            
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)
    

@AppMediator.register('CATEGORY_EDIT_METADATA_DEVELOPER')
def cmd_category_metadata_developer(args):
    category_id = args['category_id'] if 'category_id' in args else None    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_field_by_str(category, kodi.translate(40802), category.get_developer, category.set_developer):
            repository.update_category(category)
            uow.commit()    
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_EDIT_METADATA_RATING')
def cmd_category_metadata_rating(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_rating(category, category.get_rating, category.set_rating):
            repository.update_category(category)
            uow.commit()
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_EDIT_METADATA_PLOT')
def cmd_category_metadata_plot(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if editors.edit_field_by_str(category, kodi.translate(40811), category.get_plot, category.set_plot):
            repository.update_category(category)
            uow.commit()
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_IMPORT_NFO_FILE_DEFAULT')
def cmd_category_import_nfo_file(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        NFO_file = category.get_NFO_name()
        
        if category.import_NFO_file(NFO_file):
            repository.update_category(category)
            uow.commit()
            kodi.notify(kodi.translate(41038).format(NFO_file.getPath()))
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_IMPORT_NFO_FILE_BROWSE')
def cmd_category_browse_import_nfo_file(args):
    category_id = args['category_id'] if 'category_id' in args else None
    
    NFO_file = kodi.browse(text=kodi.translate(41143), mask='.nfo')
    logger.debug('cmd_category_browse_import_nfo_file() Dialog().browse returned "{0}"'.format(NFO_file))
    if not NFO_file:
        return
    NFO_FileName = io.FileName(NFO_file)
    if not NFO_FileName.exists():
        return
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
        if category.import_NFO_file(NFO_FileName):
            repository.update_category(category)
            uow.commit()
            kodi.notify(kodi.translate(41038).format(NFO_FileName.getPath()))
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
            AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_parent_id()})
    
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_SAVE_NFO_FILE')
def cmd_category_save_nfo_file(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
        
    NFO_FileName = category.get_NFO_name()
    # >> Returns False if exception happened. If an Exception happened function notifies
    # >> user, so display nothing to not overwrite error notification.
    try:
        category.export_to_NFO_file(NFO_FileName)
    except:
        kodi.notify_warn(kodi.translate(41042).format(NFO_FileName.getPath()))
        logger.error("cmd_category_save_nfo_file() Exception writing'{0}'".format(NFO_FileName.getPath()))
    else:
        logger.debug("cmd_category_save_nfo_file() Created '{0}'".format(NFO_FileName.getPath()))
        kodi.notify(kodi.translate(41039).format(NFO_FileName.getPath()))
    
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('CATEGORY_EXPORT_CATEGORY_XML')
# --- Export Category XML configuration ---
def cmd_category_export_xml(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    category = None
    with uow:
        repository = CategoryRepository(uow)
        category = repository.find_category(category_id)
    
    category_fn_str = 'Category_' + text.str_to_filename_str(category.get_name()) + '.xml'
    logger.debug('cmd_export_category_xml() Exporting Category configuration')
    logger.debug('cmd_export_category_xml() Name     "{0}"'.format(category.get_name()))
    logger.debug('cmd_export_category_xml() ID       {0}'.format(category.get_id()))
    logger.debug('cmd_export_category_xml() l_fn_str "{0}"'.format(category_fn_str))

    # --- Ask user for a path to export the launcher configuration ---
    dir_path = kodi.browse(type=0, text=kodi.translate(41144))
    if not dir_path: 
        AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)
        return

    # --- If XML exists then warn user about overwriting it ---
    export_FN = io.FileName(dir_path).pjoin(category_fn_str)
    if export_FN.exists():
        ret = kodi.dialog_yesno(kodi.translate(41052).format(export_FN.getPath()))
        if not ret:
            kodi.notify_warn(kodi.translate(41040))
            AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)
            return

    # >> If everything goes all right when exporting then the else clause is executed.
    # >> If there is an error/exception then the exception handler prints a warning message
    # >> inside the function autoconfig_export_category() and the sucess message is never
    # >> printed. This is the standard way of handling error messages in AKL code.
    try:
        category.export_to_file(export_FN)
    except constants.AddonError as E:
        kodi.notify_warn(str(E))
    else:
        kodi.notify(kodi.translate(41041).format(category.get_name()))
    
    AppMediator.sync_cmd('CATEGORY_EDIT_METADATA', args)


@AppMediator.register('EDIT_PARENT_CATEGORY')
def cmd_category_change_parent_category(args):
    category_id = args['category_id'] if 'category_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = CategoryRepository(uow)
        
        category = repository.find_category(category_id)
        previous_category = repository.find_category(category.get_parent_id())
        
        all_categories = repository.find_all_categories()
        root_category = repository.find_category(constants.VCATEGORY_ADDONROOT_ID)
        
        if previous_category is None:
            previous_category = root_category
        
        options = collections.OrderedDict()
        options[root_category] = root_category.get_name()
        options.update({cat: cat.get_name() for cat in all_categories if cat.get_id() != category_id})

        title = kodi.translate(42040).format(previous_category.get_name())
        selected_option = kodi.OrdDictionaryDialog().select(title, options)
        if selected_option is None:
            # >> Return recursively to parent menu.
            logger.debug('cmd_category_change_parent_category(): Selected NONE')
            AppMediator.sync_cmd('EDIT_CATEGORY', args)
            return
        
        selected_category: Category = selected_option
        if not kodi.dialog_yesno(kodi.translate(41065).format(category.get_name(), selected_category.get_name())):
            logger.debug('cmd_category_change_parent_category(): Cancelled')
            AppMediator.sync_cmd('EDIT_ROMCOLLECTION', args)
            return

        logger.debug(f'cmd_category_change_parent_category() Moving category#{category_id} to category#{selected_category.get_id()}')
        repository.update_category_parent(category, selected_category)
        uow.commit()
        
        kodi.notify(kodi.translate(41021))
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': category.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': selected_category.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': previous_category.get_id()})
    AppMediator.sync_cmd('EDIT_CATEGORY', args)
