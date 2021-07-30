# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file.
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
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
#
# Viewqueries.py contains all methods that collect items to be shown
# in the UI containers. It combines custom data from repositories
# with static/predefined data.
# All methods have the prefix 'qry_'.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
from resources.lib.commands.mediator import AppMediator
import typing
from urllib.parse import urlencode

from ael import constants, settings
from ael.utils import kodi
from resources.lib import globals
from resources.lib.repositories import ViewRepository

logger = logging.getLogger(__name__)

#
# Root view items
#
def qry_get_root_items():
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_root_items()
    
    if container is None:
        container = {
            'id': '',
            'name': 'root',
            'obj_type': constants.OBJ_CATEGORY,
            'items': []
        }
        kodi.notify('Building initial views')
        AppMediator.async_cmd('RENDER_VIEWS')
    
    vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
    vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
    art = { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster': vcategory_poster }
    
    if not settings.getSettingAsBool('display_hide_utilities'): 
        vcategory_name   = 'Utilities'
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('utilities'),
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
                'overlay': 4
            },
            'art': art,
            'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_CATEGORY, 'obj_type': constants.OBJ_NONE }
        })
        
    if not settings.getSettingAsBool('display_hide_g_reports'): 
        vcategory_name   = 'Global Reports'
        vcategory_icon   = globals.g_PATHS.ICON_FILE_PATH.getPath()
        vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
        container['items'].append({
            'name': vcategory_name,
            'url': globals.router.url_for_path('globalreports'), #SHOW_GLOBALREPORTS_VLAUNCHERS'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': vcategory_name,
                'plot': 'Generate and view [COLOR orange]Global Reports[/COLOR].',
                'overlay': 4
            },
            'art': art,
            'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_CATEGORY, 'obj_type': constants.OBJ_NONE }
        })
    
    return container

#
# Collection items.
#
def qry_get_collection_items(collection_id: str):
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_items(collection_id)
    return container

#
# Utilities items
#
def qry_get_utilities_items():
    # --- Common artwork for all Utilities VLaunchers ---
    vcategory_icon   = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
    vcategory_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    vcategory_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
    
    container = {
        'id': '',
        'name': 'utilities',
        'obj_type': constants.OBJ_NONE,
        'items': []
    }

    container['items'].append({
        'name': 'Reset database',
        'url': globals.router.url_for_path('execute/command/reset_database'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Reset database',
            'plot': 'Reset the AEL database. You will loose all data.',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Rebuild views',
        'url': globals.router.url_for_path('execute/command/render_views'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Rebuild views',
            'plot': 'Rebuild all the container views in the application',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Scan for plugin-addons',
        'url': globals.router.url_for_path('execute/command/scan_for_addons'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Scan for plugin-addons',
            'plot': 'Scan for addons that can be used by AEL (launchers, scrapers etc.)',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Import category/launcher XML configuration file',
        'url': globals.router.url_for_path('execute/command/import_launchers'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Import category/launcher XML configuration file',
            'plot': 'Execute several [COLOR orange]Utilities[/COLOR].',
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Export category/launcher XML configuration file',
        'url': globals.router.url_for_path('utilities/export_launchers'), #EXECUTE_UTILS_EXPORT_LAUNCHERS
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Export category/launcher XML configuration file',
            'plot': (
                'Exports all AEL categories and launchers into an XML configuration file. '
                'You can later reimport this XML file.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check/Update all databases',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_DATABASE'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check/Update all databases',
            'plot': (
                'Exports all AEL categories and launchers into an XML configuration file. '
                'You can later reimport this XML file.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check Launchers',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_LAUNCHERS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check Launchers',
            'plot':  ('Check all Launchers for missing executables, missing artwork, '
                    'wrong platform names, ROM path existence, etc.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check Launcher ROMs sync status',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check Launcher ROMs sync status',
            'plot': ('For all ROM Launchers, check if all the ROMs in the ROM path are in AEL '
                    'database. If any Launcher is out of sync because you were changing your ROM files, use '
                    'the [COLOR=orange]ROM Scanner[/COLOR] to add and scrape the missing ROMs and remove '
                    'any dead ROMs.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Check ROMs artwork image integrity',
        'url': globals.router.url_for_path('EXECUTE_UTILS_CHECK_ROM_ARTWORK_INTEGRITY'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Check ROMs artwork image integrity',
            'plot': ('Scans existing [COLOR=orange]ROMs artwork images[/COLOR] in ROM Launchers '
                    'and verifies that the images have correct extension '
                    'and size is greater than 0. You can delete corrupted images to be rescraped later.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    container['items'].append({
        'name': 'Delete ROMs redundant artwork',
        'url': globals.router.url_for_path('EXECUTE_UTILS_DELETE_ROM_REDUNDANT_ARTWORK'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': 'Delete ROMs redundant artwork',
            'plot': ('Scans all ROM Launchers and finds '
                    '[COLOR orange]redundant ROMs artwork[/COLOR]. You may delete this unneeded images.'),
            'overlay': 4
        },
        'art': { 'icon' : vcategory_icon, 'fanart' : vcategory_fanart, 'poster' : vcategory_poster  },
        'properties': { constants.AEL_CONTENT_LABEL: constants.AEL_CONTENT_VALUE_NONE, 'obj_type': constants.OBJ_NONE }
    })
    
    return container

#
# Default context menu items for the whole container.
#
def qry_container_context_menu_items(container_data) -> typing.List[typing.Tuple[str,str]]:
    if container_data is None:
        return []
    # --- Create context menu items to be applied to each item in this container ---
    container_type    = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    container_name    = container_data['name'] if 'name' in container_data else 'Unknown'
    container_id      = container_data['id'] if 'id' in container_data else ''
    
    is_category: bool = container_type == constants.OBJ_CATEGORY
    is_romcollection: bool   = container_type == constants.OBJ_ROMCOLLECTION
    is_root: bool     = container_data['id'] == ''
    
    commands = []
    if is_category: 
        commands.append(('Rebuild {} view'.format(container_name),
                        _context_menu_url_for('execute/command/render_view',{'category_id':container_id})))    
    if is_romcollection:
        commands.append(('Search ROM in collection', _context_menu_url_for('/search/{}'.format(container_id))))
        commands.append(('Rebuild {} view'.format(container_name),
                         _context_menu_url_for('execute/command/render_romcollection_view', {'romcollection_id':container_id})))    
    
    commands.append(('Rebuild all views', _context_menu_url_for('execute/command/render_views')))
    commands.append(('Open Kodi file manager', 'ActivateWindow(filemanager)'))
    commands.append(('AEL addon settings', 'Addon.OpenSettings({0})'.format(globals.addon_id)))

    return commands

#
# ListItem specific context menu items.
#
def qry_listitem_context_menu_items(list_item_data, container_data)-> typing.List[typing.Tuple[str,str]]:
    if container_data is None or list_item_data is None:
        return []
    # --- Create context menu items only applicable on this item ---
    properties   = list_item_data['properties'] if 'properties' in list_item_data else {}
    item_type    = properties['obj_type'] if 'obj_type' in properties else constants.OBJ_NONE
    item_name    = list_item_data['name'] if 'name' in list_item_data else 'Unknown'
    item_id      = list_item_data['id'] if 'id' in list_item_data else ''
    
    container_id    = container_data['id'] if 'id' in container_data else constants.VCATEGORY_ADDONROOT_ID
    container_type  = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    container_is_category: bool = container_type == constants.OBJ_CATEGORY
    if container_id == '': container_id = constants.VCATEGORY_ADDONROOT_ID
    
    is_category: bool = item_type == constants.OBJ_CATEGORY 
    is_romcollection: bool   = item_type == constants.OBJ_ROMCOLLECTION
    is_rom: bool      = item_type == constants.OBJ_ROM
    
    commands = []
    if is_rom: 
        commands.append(('View ROM', _context_menu_url_for('/rom/{}/view'.format(item_id))))
        commands.append(('Edit ROM', _context_menu_url_for('/rom/edit/{}'.format(item_id))))
        commands.append(('Link ROM in other collection', _context_menu_url_for('/execute/command/link_rom',{'rom_id':item_id})))
        commands.append(('Add ROM to AEL Favourites', _context_menu_url_for('/execute/command/add_rom_to_favourites',{'rom_id':item_id})))
    if is_category: 
        commands.append(('View Category', _context_menu_url_for('/categories/view/{}'.format(item_id))))
        commands.append(('Edit Category', _context_menu_url_for('/categories/edit/{}'.format(item_id))))
        commands.append(('Add new Category',_context_menu_url_for('/categories/add/{}/in/{}'.format(item_id, container_id))))
        commands.append(('Add new ROM Collection', _context_menu_url_for('/romcollection/add/{}/in/{}'.format(item_id, container_id))))
        
    if is_romcollection: 
        commands.append(('View ROM Collection', _context_menu_url_for('/romcollection/view/{}'.format(item_id))))
        commands.append(('Edit ROM Collection', _context_menu_url_for('/romcollection/edit/{}'.format(item_id))))
    
    if not is_category and container_is_category:
        commands.append(('Add new Category',_context_menu_url_for('/categories/add/{}'.format(container_id))))
        commands.append(('Add new ROM Collection', _context_menu_url_for('/romcollection/add/{}'.format(container_id))))
    
    return commands

def _context_menu_url_for(url: str, params: dict = None) -> str:
    if params is not None:
        url = '{}?{}'.format(url, urlencode(params))
    url = globals.router.url_for_path(url)
    return 'RunPlugin({})'.format(url)