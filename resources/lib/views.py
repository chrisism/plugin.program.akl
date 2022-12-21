# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher main script file.
#

# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Location of functions within code:
# 1. Functions in views.py have vw_ prefix.
# 2. Functions accessible by routes have vw_route prefix
#
# Views.py contains all methods accessible by URL commands (using routes/paths)
# triggered from Kodi. The methods will only perform operations to render and visualize
# the list items in the containers.
# AKL follows a (sortof) CQRS architecture, meaning that all actions to gather the items 
# or to perform commands are delegated to the queries.py file and different **_commands.py 
# files. Query methods are called directly and the Command methods are called through
# sending notifications to the AKL service (Monitor).
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
from __future__ import annotations

import sys
import abc
import logging

# --- Kodi stuff ---
import xbmc
import xbmcgui
import xbmcplugin

from akl import constants
from akl.utils import kodi

from resources.lib import viewqueries, globals
from resources.lib.commands.mediator import AppMediator
from resources.lib.commands import view_rendering_commands
from resources.lib.globals import router

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------------------------
# This is the plugin entry point.
# ---------------------------------------------------------------------------------------------
def run_plugin(addon_argv):
    # --- Some debug stuff for development ---
    logger.debug('------------ Called Advanced Kodi Launcher run_plugin(addon_argv) ------------')
    logger.debug(f'addon.id         "{globals.addon_id}"')
    logger.debug(f'addon.version    "{globals.addon_version}"')
    for i in range(len(sys.argv)): 
        logger.debug(f'sys.argv[{i}] "{sys.argv[i]}"')

    # --- Bootstrap object instances --- 
    globals.g_bootstrap_instances()
    try:
        router.run()
    except Exception as e:
        logger.error('Exception while executing route', exc_info=e)
        kodi.notify_error('Failed to execute route or command')
        
    logger.debug('Advanced Kodi Launcher run_plugin() exit')

# -------------------------------------------------------------------------------------------------
# LisItem rendering
# -------------------------------------------------------------------------------------------------
@router.route('/')
def vw_route_render_root():
    logger.debug("Executing route: vw_route_render_root")
    container = viewqueries.qry_get_root_items()
    container_context_items = viewqueries.qry_container_context_menu_items(container)

    render_list_items(container, container_context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

@router.route('/category/<view_id>')
@router.route('/collection/<view_id>')
def vw_route_render_collection(view_id: str):
    logger.debug("Executing route: vw_route_render_collection")
    container               = viewqueries.qry_get_view_items(view_id)
    container_context_items = viewqueries.qry_container_context_menu_items(container)
    container_type          = container['obj_type'] if 'obj_type' in container else constants.OBJ_NONE

    filter_type = router.args['filter'][0] if 'filter' in router.args else None
    filter_term = router.args['term'][0] if 'term' in router.args else None
    filter = vw_create_filter(filter_type, filter_term)

    if container is None:
        kodi.notify('Current view is not rendered correctly. Re-render views first.')
    elif len(container['items']) == 0:
        if container_type == constants.OBJ_CATEGORY:
            kodi.notify('Category {} has no items. Add romcollections or categories first.'.format(container['name']))
        if container_type == constants.OBJ_ROMCOLLECTION or container_type == constants.OBJ_COLLECTION_VIRTUAL:
            kodi.notify('Collection {} has no items. Add ROMs'.format(container['name']))
    else:
        render_list_items(container, container_context_items, filter)
        
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)

@router.route('/collection/<view_id>/search')
def vw_route_search_collection(view_id: str):
    logger.debug("Executing route: vw_route_search_collection")
    #vw_route_render_collection(view_id)
    AppMediator.sync_cmd('SEARCH', {'romcollection_id': view_id})
    kodi.refresh_container()

@router.route('/category/virtual/<view_id>')
@router.route('/collection/virtual/<view_id>')
def vw_route_render_virtual_view(view_id: str):
    container               = viewqueries.qry_get_view_items(view_id, is_virtual_view=True)
    container_context_items = viewqueries.qry_container_context_menu_items(container)
    container_type          = container['obj_type'] if 'obj_type' in container else constants.OBJ_NONE

    filter_type = router.args['filter'][0] if 'filter' in router.args else None
    filter_term = router.args['term'][0] if 'term' in router.args else None
    filter = vw_create_filter(filter_type, filter_term)
    
    if container is None:
        kodi.notify('Current view is not rendered correctly. Re-render views first.')
    elif len(container['items']) == 0:
        if container_type == constants.OBJ_CATEGORY_VIRTUAL:
            if kodi.dialog_yesno(f"Virtual category '{container['name']}'' has no items. Regenerate the views now?"):
                AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': container['id']})
        if container_type == constants.OBJ_COLLECTION_VIRTUAL:
            if kodi.dialog_yesno(f"Virtual collection {container['name']} has no items. Regenerate the views now?"):
                AppMediator.async_cmd('RENDER_VCATEGORY_VIEW', {'vcategory_id': container['parent_id']})
    else:
        render_list_items(container, container_context_items, filter)
        
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)
    
@router.route('/collection/virtual/<category_id>/items')
def vw_route_render_virtual_items_view(category_id: str):
    collection_value = router.args["value"][0]
    container = view_rendering_commands.cmd_render_virtual_collection(category_id, collection_value)
    container_context_items = viewqueries.qry_container_context_menu_items(container)

    filter_type = router.args['filter'][0] if 'filter' in router.args else None
    filter_term = router.args['term'][0] if 'term' in router.args else None
    filter = vw_create_filter(filter_type, filter_term)
    
    render_list_items(container, container_context_items, filter)
        
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)
       
# -------------------------------------------------------------------------------------------------
# Utilities and Global reports
# -------------------------------------------------------------------------------------------------
@router.route('/utilities')
def vw_route_render_utilities():
    container = viewqueries.qry_get_utilities_items()
    container_context_items = viewqueries.qry_container_context_menu_items(container)

    render_list_items(container, container_context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)
    
@router.route('/globalreports')
def vw_route_render_globalreports():
    container = viewqueries.qry_get_globalreport_items()
    container_context_items = viewqueries.qry_container_context_menu_items(container)

    render_list_items(container, container_context_items)
    xbmcplugin.endOfDirectory(handle = router.handle, succeeded = True, cacheToDisc = False)    

# -------------------------------------------------------------------------------------------------
# Command execution
# -------------------------------------------------------------------------------------------------
@router.route('/execute/command/<cmd>')
def vw_execute_cmd(cmd: str):    
    cmd_args = { arg: router.args[arg][0] for arg in router.args }
    AppMediator.async_cmd(cmd.capitalize(), cmd_args)

@router.route('/categories/add')
@router.route('/categories/add/<category_id>')
@router.route('/categories/add/<category_id>/in')
@router.route('/categories/add/<category_id>/in/<parent_category_id>')
def vw_add_category(category_id: str = None, parent_category_id: str = None):
    AppMediator.async_cmd('ADD_CATEGORY', {'category_id': category_id, 'parent_category_id': parent_category_id})

@router.route('/categories/edit/<category_id>')
def vw_edit_category(category_id: str):
    AppMediator.async_cmd('EDIT_CATEGORY', {'category_id': category_id })

@router.route('/categories/addrom/<category_id>')
@router.route('/categories/addrom/<category_id>/in')
@router.route('/categories/addrom/<category_id>/in/<parent_category_id>')
def vw_add_rom_to_category(category_id: str = None, parent_category_id: str = None):
    AppMediator.async_cmd('ADD_STANDALONE_ROM', {'category_id': category_id,  'parent_category_id': parent_category_id})

@router.route('/romcollection/add')
@router.route('/romcollection/add/<category_id>')
@router.route('/romcollection/add/<category_id>/in')
@router.route('/romcollection/add/<category_id>/in/<parent_category_id>')
def vw_add_romcollection(category_id: str = None, parent_category_id: str = None):
    AppMediator.async_cmd('ADD_ROMCOLLECTION', {'category_id': category_id, 'parent_category_id': parent_category_id})

@router.route('/romcollection/view/<romcollection_id>')
def vw_view_romcollection(romcollection_id: str):
    #todo
    pass

@router.route('/romcollection/edit/<romcollection_id>')
def vw_edit_romcollection(romcollection_id: str):
    AppMediator.async_cmd('EDIT_ROMCOLLECTION', {'romcollection_id': romcollection_id })

@router.route('/rom/<rom_id>/view')
def vw_view_rom(rom_id):

    rom_view_data = view_rendering_commands.cmd_render_rom_details(rom_id)
    rom_list_item = render_list_item(rom_view_data)

    assets_model = []
    for asset_key, asset_val in rom_view_data['art'].items():
        list_item = xbmcgui.ListItem(asset_key)
        list_item.setLabel2(asset_val)
        list_item.setArt({'thumb': asset_val})
        assets_model.append(list_item)

    # collections_data = view_rendering_commands.cmd_render_romcollection_view_data()
    ui = ViewRomGUI('script-akl-romdetails.xml', globals.addon_path, 'default', '1080i', True, 
                    rom_model=[rom_list_item], assets_model=assets_model)
    ui.doModal()
    del ui

@router.route('/rom/edit/<rom_id>')
def vw_edit_rom(rom_id: str):
    AppMediator.async_cmd('EDIT_ROM', {'rom_id': rom_id })

# -------------------------------------------------------------------------------------------------
# ROM execution
# -------------------------------------------------------------------------------------------------    
@router.route('/execute/rom/<rom_id>')
def vw_route_execute_rom(rom_id):
    AppMediator.async_cmd("EXECUTE_ROM", {'rom_id': rom_id} )

# -------------------------------------------------------------------------------------------------
# UI render methods
# -------------------------------------------------------------------------------------------------
#
# Renders items for a view.
#
def render_list_items(container_data:dict, container_context_items = [], filter_method:ListFilter = None):
    vw_misc_set_all_sorting_methods()
    vw_misc_set_AEL_Content(container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE)
    vw_misc_clear_AEL_Launcher_Content()

    # Container Properties
    if 'properties' in container_data:
        for property, value in container_data['properties'].items():
            xbmcplugin.setProperty(router.handle, property, value)

    for list_item_data in container_data['items']:
        if filter_method and not filter_method.is_valid(list_item_data):
            continue
        
        list_item = render_list_item(list_item_data)
        url_str = list_item_data['url']
        folder_flag = list_item_data['is_folder']

        if xbmc.getCondVisibility("!Skin.HasSetting(KioskMode.Enabled)"):
            item_context_items = viewqueries.qry_listitem_context_menu_items(list_item_data, container_data)
            list_item.addContextMenuItems(item_context_items + container_context_items)

        xbmcplugin.addDirectoryItem(handle = router.handle, url = url_str, listitem = list_item, isFolder = folder_flag)

def render_list_item(list_item_data: dict) -> xbmcgui.ListItem:
    name        = list_item_data['name']
    item_type   = list_item_data['type']

    list_item = xbmcgui.ListItem(name)
    list_item.setInfo(item_type, list_item_data['info'])
    list_item.setArt(list_item_data['art'])
    list_item.setProperties(list_item_data['properties'])

    return list_item

# -------------------------------------------------------------------------------------------------
# UI helper methods
# -------------------------------------------------------------------------------------------------
#
#
#
def vw_misc_set_all_sorting_methods():
    # >> This must be called only if router.handle > 0, otherwise Kodi will complain in the log.
    if router.handle < 0:
        return
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(handle = router.handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

#
# Set the AEL content type.
# It is a Window(10000) property used by skins to know if AEL is rendering
# a Window that has categories/launchers or ROMs.
#
def vw_misc_set_AEL_Content(AEL_Content_Value):
    if AEL_Content_Value == constants.AKL_CONTENT_VALUE_LAUNCHERS:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(constants.AKL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_LAUNCHERS))
        xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_LAUNCHERS)
        
    elif AEL_Content_Value == constants.AKL_CONTENT_VALUE_CATEGORY:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(constants.AKL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_CATEGORY))
        xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_CATEGORY)        
    elif AEL_Content_Value == constants.AKL_CONTENT_VALUE_ROMS:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(constants.AKL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_ROMS))
        xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_ROMS)
    elif AEL_Content_Value == constants.AKL_CONTENT_VALUE_NONE:
        logger.debug('vw_misc_set_AEL_Content() Setting Window({0}) '.format(constants.AKL_CONTENT_WINDOW_ID) +
                  'property "{0}" = "{1}"'.format(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_NONE))
        xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_CONTENT_LABEL, constants.AKL_CONTENT_VALUE_NONE)
    else:
        logger.error('vw_misc_set_AEL_Content() Invalid AEL_Content_Value "{0}"'.format(AEL_Content_Value))

def vw_misc_clear_AEL_Launcher_Content():
    xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_LAUNCHER_NAME_LABEL, '')
    xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_LAUNCHER_ICON_LABEL, '')
    xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_LAUNCHER_CLEARLOGO_LABEL, '')
    xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_LAUNCHER_PLATFORM_LABEL, '')
    xbmcgui.Window(constants.AKL_CONTENT_WINDOW_ID).setProperty(constants.AKL_LAUNCHER_BOXSIZE_LABEL, '')
    
def vw_create_filter(filter_on_type:str, filter_on_value:str) -> ListFilter:
    if filter_on_type is None:
        return None
    if filter_on_value == 'UNDEFINED':
        filter_on_value = ''
    
    if filter_on_type == constants.META_TITLE_ID:
        return OnTitleFilter(filter_on_value)    
    if filter_on_type == constants.META_DEVELOPER_ID:
        return OnDeveloperFilter(filter_on_value)
    if filter_on_type == constants.META_GENRE_ID:
        return OnGenreFilter(filter_on_value)
    if filter_on_type == constants.META_YEAR_ID:
        return OnReleaseYearFilter(filter_on_value)
    if filter_on_type == constants.META_RATING_ID:
        return OnRatingFilter(filter_on_value)    
    if filter_on_type == constants.META_ESRB_ID:
        return OnESRBFilter(filter_on_value)
    if filter_on_type == constants.META_PEGI_ID:
        return OnPEGIFilter(filter_on_value)
    if filter_on_type == constants.META_NPLAYERS_ID:
        return OnNumberOfPlayersFilter(filter_on_value)
    if filter_on_type == 'platform':
        return OnPlatformFilter(filter_on_value)
    
    logger.debug(f'Filter called without proper filter type. "{filter_on_type}"')
    return None

class ListFilter(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, filter_value:str):
        self.filter_value = filter_value

    @abc.abstractmethod        
    def is_valid(self, subject:dict) -> bool:
        return True
    
class OnTitleFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'name' in subject and subject['name'].lower().find(self.filter_value) > -1
    
class OnDeveloperFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'info' in subject and 'studio' in subject['info'] and subject['info']['studio'] == self.filter_value  

class OnGenreFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'info' in subject and 'genre' in subject['info'] and subject['info']['genre'] == self.filter_value  

class OnReleaseYearFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'info' in subject and 'year' in subject['info'] and subject['info']['year'] == self.filter_on_value    

class OnRatingFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'info' in subject and 'rating' in subject['info'] and subject['info']['rating'] == self.filter_on_value    
    
class OnESRBFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'properties' in subject and 'esrb' in subject['properties'] and subject['properties']['esrb'] == self.filter_on_value   
    
class OnPEGIFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'properties' in subject and 'pegi' in subject['properties'] and subject['properties']['pegi'] == self.filter_on_value   
    
class OnNumberOfPlayersFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'properties' in subject and 'nplayers' in subject['properties'] and subject['properties']['nplayers'] == self.filter_on_value  
    
class OnPlatformFilter(ListFilter):
    def is_valid(self, subject: dict) -> bool:
        return 'properties' in subject and 'platform' in subject['properties'] and subject['properties']['platform'] == self.filter_on_value


class ViewRomGUI(xbmcgui.WindowXML):

    def __init__(self, *args, **kwargs):
        self.first_load = True
        self.rom_model = kwargs['rom_model']
        self.assets_model = kwargs['assets_model']

    def onInit(self):
        if self.first_load:
            self.render_items()

    def render_items(self):
        self.first_load = False
        index = 19801
        lists = [self.rom_model, self.assets_model]

        self.clearList()
        for items in lists:
            try:
                cntrl = self.getControl(index)
                cntrl.addItems(items)
            except RuntimeError as error:
                logger.error(f'Control with id {index} cannot be filled. Error: {error}')
                pass
            index += 1
        
        xbmc.sleep(100)
        self.setFocusId(self.getCurrentContainerId())