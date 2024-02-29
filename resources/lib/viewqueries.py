# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: UI query implementations. Getting data for the UI
#

# Copyright (c) Chrisism <crizizz@gmail.com>
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
import typing
from urllib.parse import urlencode

# AKL modules
from akl import constants, settings
from akl.utils import kodi

from resources.lib import globals
from resources.lib.commands.mediator import AppMediator
from resources.lib.commands import view_rendering_commands
from resources.lib.repositories import ViewRepository, UnitOfWork, ROMsRepository, LaunchersRepository, g_assetFactory


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
        kodi.notify(kodi.translate(40959))
        AppMediator.async_cmd('RENDER_VIEWS')
    
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()

    listitem_name = kodi.translate(40914)
    container['items'].append({
        'name': listitem_name,
        'url': globals.router.url_for_path('sources'),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title': listitem_name,
            'plot': kodi.translate(44032),
            'overlay': 4
        },
        'art': {
            'fanart': listitem_fanart,
            'icon': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_icon.png').getPath(),
            'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_poster.png').getPath()
        },
        'properties': {
            'obj_type': constants.OBJ_SOURCE
        }
    })

    listitem_name = kodi.translate(40920)
    container['items'].append({
        'name': listitem_name,
        'url': globals.router.url_for_path('launchers'),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title': listitem_name,
            'plot': kodi.translate(44033),
            'overlay': 4
        },
        'art': {
            'fanart': listitem_fanart,
            'icon': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_icon.png').getPath(),
            'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_poster.png').getPath()
        },
        'properties': {
            'obj_type': constants.OBJ_LAUNCHER
        }
    })
    
    if not settings.getSettingAsBool('display_hide_utilities'):
        listitem_name = kodi.translate(40897)
        container['items'].append({
            'name': listitem_name,
            'url': globals.router.url_for_path('utilities'),
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': listitem_name,
                'plot': kodi.translate(44001),
                'overlay': 4
            },
            'art': {
                'fanart': listitem_fanart,
                'icon': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath(),
                'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
            },
            'properties': {
                'obj_type': constants.OBJ_NONE
            }
        })
        
    if not settings.getSettingAsBool('display_hide_g_reports'):
        listitem_name = kodi.translate(40898)
        container['items'].append({
            'name': listitem_name,
            'url': globals.router.url_for_path('globalreports'),  # SHOW_GLOBALREPORTS_VLAUNCHERS'
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': listitem_name,
                'plot': kodi.translate(44002),
                'overlay': 4
            },
            'art': {
                'fanart': listitem_fanart,
                'icon': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath(),
                'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath()
            },
            'properties': {
                'obj_type': constants.OBJ_NONE
            }
        })
    
    return container


#
# View pre-rendered items.
#
def qry_get_view_items(view_id: str, obj_type: int):
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_items(view_id, obj_type)
    return container


#
# DB based items
#
def qry_get_view_item(rom_id: str):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    container = None
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)

        item = view_rendering_commands.render_rom_listitem(rom)
        container = {
            'id': rom_id,
            'name': rom.get_name(),
            'obj_type': constants.OBJ_ROM,
            'items': [item]
        }

    return container


def qry_get_view_metadata(rom_id: str):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    container = None
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)

        items = []
        items.append({
            'id': 40801, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_GENRE_ID}/items?value={rom.get_genre()}'),
            'name': kodi.translate(40801), 'name2': rom.get_genre(),
            'info': {}, 'art': {}, 'properties': {'field': 'genre'}})
        items.append({
            'id': 40803, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_YEARS_ID}/items?value={rom.get_releaseyear()}'),
            'name': kodi.translate(40803), 'name2': rom.get_releaseyear(),
            'info': {}, 'art': {}, 'properties': {'field': 'releaseyear'}})
        items.append({
            'id': 40802, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_DEVELOPER_ID}/items?value={rom.get_developer()}'),
            'name': kodi.translate(40802), 'name2': rom.get_developer(),
            'info': {}, 'art': {}, 'properties': {'field': 'developer'}})
        items.append({
            'id': 40806, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_RATING_ID}/items?value={rom.get_rating()}'),
            'name': kodi.translate(40806), 'name2': str(rom.get_rating()),
            'info': {}, 'art': {}, 'properties': {'field': 'rating'}})
        items.append({
            'id': 40804, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_ESRB_ID}/items?value={rom.get_esrb_rating()}'),
            'name': kodi.translate(40804), 'name2': rom.get_esrb_rating(),
            'info': {}, 'art': {}, 'properties': {'field': 'esrb'}})
        items.append({
            'id': 40805, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_PEGI_ID}/items?value={rom.get_pegi_rating()}'),
            'name': kodi.translate(40805), 'name2': rom.get_pegi_rating(),
            'info': {}, 'art': {}, 'properties': {'field': 'pegi'}})
        items.append({
            'id': 40808, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/{constants.VCATEGORY_NPLAYERS_ID}/items?value={rom.get_number_of_players()}'),
            'name': kodi.translate(40808), 'name2': str(rom.get_number_of_players()),
            'info': {}, 'art': {}, 'properties': {'field': 'nplayers'}})
        items.append({
            'id': 40809, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path('execute/command/reset_database'),
            'name': kodi.translate(40809), 'name2': str(rom.get_number_of_players_online()),
            'info': {}, 'art': {}, 'properties': {'field': 'nplayers_online'}})
        items.append({
            'id': 40810, 'is_folder': False, 'type': 'game',
            'url': globals.router.url_for_path(
                f'/collection/virtual/items?value={rom.get_genre()}'),
            'name': kodi.translate(40810), 'name2': ','.join(rom.get_tags()),
            'info': {}, 'art': {}, 'properties': {'field': 'tags'}})

        container = {
            'id': rom_id,
            'name': rom.get_name(),
            'obj_type': constants.OBJ_ROM,
            'items': items
        }

    return container


def qry_get_view_assets(rom_id: str):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    container = None
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)

        assigned_assets = rom.get_assets()
        asset_ids = rom.get_asset_ids_list()
        items = []
        for asset_id in asset_ids:
            asset = next((a for a in assigned_assets if a.get_asset_info_id() == asset_id), None)
            asset_info = asset.asset_info if asset else g_assetFactory.get_asset_info(asset_id)
            items.append({
                'id': asset_id,
                'is_folder': False,
                'type': 'pictures',
                'name': kodi.translate(asset_info.name_id),
                'name2': asset.get_path() if asset else None,
                'url': asset.get_path() if asset else globals.router.url_for_path(
                    f'/execute/command/rom_edit_assets/?rom_id={rom_id}&selected_asset={asset_id}'),
                'info': {
                    'title': kodi.translate(asset_info.name_id),
                    'picturepath': asset.get_path() if asset else None,
                },
                'art': {
                    'thumb': asset.get_path() if asset else 'DefaultAddonImages.png'
                },
                'properties': {
                    'is_set': str(asset and asset.is_assigned()),
                    'assetid': asset_id
                }
            })

        container = {
            'name': rom.get_name(),
            'id': rom_id,
            'obj_type': constants.OBJ_NONE,
            'items': items
        }

    return container


def qry_get_view_scanned_data(rom_id: str):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    container = None
    with uow:
        roms_repository = ROMsRepository(uow)
        rom = roms_repository.find_rom(rom_id)
        scanned_data = rom.get_scanned_data()
        items = []
        for key, value in scanned_data.items():
            items.append({
                'is_folder': False, 'type': 'game',
                'name': key, 'name2': value,
                'url': globals.router.url_for_path(
                    f'/rom/{rom.get_id()}/view/scanneddata?field={key}'),
                'info': {}, 'art': {}, 'properties': {}})
        container = {
            'id': rom_id,
            'name': rom.get_name(),
            'obj_type': constants.OBJ_ROM,
            'items': items
        }

    return container


#
# Source items
#
def qry_get_sources():
    views_repository = ViewRepository(globals.g_PATHS)
    container = views_repository.find_sources_items()
    
    if container is None:
        container = {
            'id': '',
            'name': kodi.translate(constants.OBJ_SOURCE),
            'obj_type': constants.OBJ_SOURCE,
            'items': []
        }
    return container


#
# Launcher items
#
def qry_get_launchers():
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    container = None
    with uow:
        repository = LaunchersRepository(uow)
        launchers = repository.find_all()
        
        container = {
            'id': '',
            'name': kodi.translate(constants.OBJ_LAUNCHER),
            'obj_type': constants.OBJ_LAUNCHER,
            'items': []
        }
        
        listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()

        for launcher in launchers:
            listitem_name = launcher.get_name()
            container['items'].append({
                'id': launcher.get_id(),
                'name': listitem_name,
                'url': globals.router.url_for_path(f'/launcher/edit/{launcher.get_id()}'),
                'is_folder': False,
                'type': 'video',
                'info': {
                    'title': listitem_name,
                    'plot': f'Launcher of type {launcher.addon.get_addon_type()}',
                    'overlay': 4
                },
                'art': {
                    'fanart': listitem_fanart,
                    'icon': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_icon.png').getPath(),
                    'poster': globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Sources_poster.png').getPath()
                },
                'properties': {
                    'obj_type': constants.OBJ_LAUNCHER
                }
            })
        
        return container

     
#
# Utilities items
#
def qry_get_utilities_items():
    # --- Common artwork for all Utilities VLaunchers ---
    listitem_icon = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_icon.png').getPath()
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    listitem_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Utilities_poster.png').getPath()
    
    container = {
        'id': '',
        'name': kodi.translate(40897),
        'obj_type': constants.OBJ_NONE,
        'items': []
    }

    # Deprecated commands:
    # EXECUTE_UTILS_CHECK_LAUNCHER_SYNC_STATUS -> todo: execute per collection, add report command to scanners
    # EXECUTE_UTILS_CHECK_DATABASE -> Substituted by db constraints and migration scripts.

    container['items'].append({
        'name': kodi.translate(40899),
        'url': globals.router.url_for_path('execute/command/reset_database'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40899),
            'plot': kodi.translate(44003),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40856),
        'url': globals.router.url_for_path('execute/command/render_views'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40856),
            'plot': kodi.translate(44004),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40900),
        'url': globals.router.url_for_path('execute/command/render_virtual_views'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40900),
            'plot': kodi.translate(44018),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40901),
        'url': globals.router.url_for_path('execute/command/scan_for_addons'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40901),
            'plot': kodi.translate(44019),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40902),
        'url': globals.router.url_for_path('execute/command/show_addons'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40902),
            'plot': kodi.translate(44020),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40903),
        'url': globals.router.url_for_path('execute/command/manage_rom_tags'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40903),
            'plot': kodi.translate(44021),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40904),
        'url': globals.router.url_for_path('execute/command/import_launchers'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40904),
            'plot': kodi.translate(44022),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40905),
        'url': globals.router.url_for_path('execute/command/export_to_legacy_xml'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40905),
            'plot': kodi.translate(44023),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40906),
        'url': globals.router.url_for_path('execute/command/check_collections'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40906),
            'plot': kodi.translate(44024),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40907),
        'url': globals.router.url_for_path('execute/command/check_rom_artwork_integrity'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40907),
            'plot': kodi.translate(44025),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40908),
        'url': globals.router.url_for_path('execute/command/delete_redundant_rom_artwork'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40908),
            'plot': kodi.translate(44026),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    container['items'].append({
        'name': kodi.translate(40909),
        'url': globals.router.url_for_path('execute/command/EXECUTE_UTILS_SHOW_DETECTED_DATS'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40909),
            'plot': kodi.translate(44027),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    
    return container


#
# Global Reports items
#
def qry_get_globalreport_items():
    # --- Common artwork for all Utilities VLaunchers ---
    listitem_icon = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_icon.png').getPath()
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()
    listitem_poster = globals.g_PATHS.ADDON_CODE_DIR.pjoin('media/theme/Global_Reports_poster.png').getPath()
    
    container = {
        'id': '',
        'name': 'globalreports',
        'obj_type': constants.OBJ_NONE,
        'items': []
    }

    # --- Global ROM statistics ---
    container['items'].append({
        'name': kodi.translate(40910),
        'url': globals.router.url_for_path('execute/command/global_rom_stats'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40910),
            'plot': kodi.translate(44028),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    
    # --- Global ROM Audit statistics  ---
    container['items'].append({
        'name': kodi.translate(40911),
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_ALL'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40911),
            'plot': kodi.translate(44029),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    
    container['items'].append({
        'name': kodi.translate(40912),
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_NOINTRO'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40912),
            'plot': kodi.translate(44030),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    
    container['items'].append({
        'name': kodi.translate(40913),
        'url': globals.router.url_for_path('execute/command/EXECUTE_GLOBAL_AUDIT_STATS_REDUMP'),
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': kodi.translate(40913),
            'plot': kodi.translate(44031),
            'overlay': 4
        },
        'art': {'icon': listitem_icon, 'fanart': listitem_fanart, 'poster': listitem_poster},
        'properties': {
            'obj_type': constants.OBJ_NONE
        }
    })
    return container


#
# Default context menu items for the whole container.
#
def qry_container_context_menu_items(container_data) -> typing.List[typing.Tuple[str, str]]:
    if container_data is None:
        return []
    # --- Create context menu items to be applied to each item in this container ---
    container_type = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    container_name = container_data['name'] if 'name' in container_data else 'Unknown'
    container_id = container_data['id'] if 'id' in container_data else ''
    container_parentid = container_data['parent_id'] if 'parent_id' in container_data else ''
    
    is_root: bool = container_data['id'] == ''
    
    commands = []
    if container_type == constants.OBJ_CATEGORY:
        commands.append((kodi.translate(40893).format(container_name),
                        _context_menu_url_for('execute/command/render_category_view', {'category_id': container_id})))
       
    if container_type == constants.OBJ_SOURCE and is_root:
        commands.append((kodi.translate(40916), _context_menu_url_for('/execute/command/add_source')))
        
    if container_type == constants.OBJ_LAUNCHER and is_root:
        commands.append((kodi.translate(40917), _context_menu_url_for('/execute/command/add_launcher')))
        
    if container_type == constants.OBJ_ROMCOLLECTION:
        commands.append((kodi.translate(40894), _context_menu_url_for(f'/collection/{container_id}/search')))
        commands.append((kodi.translate(40893).format(container_name),
                         _context_menu_url_for('execute/command/render_romcollection_view', {'romcollection_id': container_id})))
    if container_type == constants.OBJ_CATEGORY_VIRTUAL and not is_root:
        commands.append((kodi.translate(40893).format(container_name),
                        _context_menu_url_for('execute/command/render_vcategory_view', {'vcategory_id': container_id})))
    if container_type == constants.OBJ_COLLECTION_VIRTUAL:
        commands.append((kodi.translate(40893).format(container_name),
                        _context_menu_url_for('execute/command/render_vcategory_view', {'vcategory_id': container_parentid})))
    
    commands.append((kodi.translate(40856), _context_menu_url_for('execute/command/render_views')))
    commands.append((kodi.translate(40895), 'ActivateWindow(filemanager)'))
    commands.append((kodi.translate(40896), 'Addon.OpenSettings({0})'.format(globals.addon_id)))

    return commands


#
# ListItem specific context menu items.
#
def qry_listitem_context_menu_items(list_item_data, container_data) -> typing.List[typing.Tuple[str, str]]:
    if container_data is None or list_item_data is None:
        return []
    # --- Create context menu items only applicable on this item ---
    properties = list_item_data['properties'] if 'properties' in list_item_data else {}
    item_type = properties['obj_type'] if 'obj_type' in properties else constants.OBJ_NONE
    item_name = list_item_data['name'] if 'name' in list_item_data else 'Unknown'
    item_id = list_item_data['id'] if 'id' in list_item_data else ''
    
    container_id = container_data['id'] if 'id' in container_data else ''
    container_type = container_data['obj_type'] if 'obj_type' in container_data else constants.OBJ_NONE
    
    container_is_category: bool = container_type == constants.OBJ_CATEGORY
    
    is_category: bool = item_type == constants.OBJ_CATEGORY
    is_source: bool = item_type == constants.OBJ_SOURCE
    is_launcher: bool = item_type == constants.OBJ_LAUNCHER
    is_romcollection: bool = item_type == constants.OBJ_ROMCOLLECTION
    is_virtual_category: bool = item_type == constants.OBJ_CATEGORY_VIRTUAL
    is_rom: bool = item_type == constants.OBJ_ROM
    
    commands = []
    if is_rom:
        commands.append((kodi.translate(40882), _context_menu_url_for(f'/rom/view/{item_id}')))
        commands.append((kodi.translate(40883), _context_menu_url_for(f'/rom/edit/{item_id}')))
        commands.append((kodi.translate(40884), _context_menu_url_for('/execute/command/link_rom', {'rom_id': item_id})))
        commands.append((kodi.translate(40885), _context_menu_url_for('/execute/command/add_rom_to_favourites', {'rom_id': item_id})))
        
    if is_category:
        commands.append((kodi.translate(40886), _context_menu_url_for(f'/categories/view/{item_id}')))
        commands.append((kodi.translate(40887), _context_menu_url_for(f'/categories/edit/{item_id}')))
        commands.append((kodi.translate(40888), _context_menu_url_for(f'/categories/add/{item_id}/in/{container_id}')))
        commands.append((kodi.translate(40889), _context_menu_url_for(f'/romcollection/add/{item_id}/in/{container_id}')))
        
    if is_romcollection:
        commands.append((kodi.translate(40891), _context_menu_url_for(f'/romcollection/view/{item_id}')))
        commands.append((kodi.translate(40892), _context_menu_url_for(f'/romcollection/edit/{item_id}')))
    
    if is_source:
        if not item_id or len(item_id) == 0:
            commands.append((kodi.translate(40916), _context_menu_url_for('/execute/command/add_library')))
        if item_id and len(item_id) > 0:
            commands.append((kodi.translate(40915), _context_menu_url_for(f'/source/edit/{item_id}')))
        
    if is_launcher:
        if not item_id or len(item_id) == 0:
            commands.append((kodi.translate(40917), _context_menu_url_for('/execute/command/add_launcher')))
        if item_id and len(item_id) > 0:
            commands.append((kodi.translate(40918), _context_menu_url_for(f'/launcher/edit/{item_id}')))
            commands.append((kodi.translate(40919), _context_menu_url_for(f'/launcher/delete/{item_id}')))
        
    if not is_category and container_is_category:
        commands.append((kodi.translate(40888), _context_menu_url_for(f'/categories/add/{container_id}')))
        commands.append((kodi.translate(40889), _context_menu_url_for(f'/romcollection/add/{container_id}')))
        
    if is_virtual_category:
        commands.append((kodi.translate(40893).format(item_name), _context_menu_url_for('execute/command/render_vcategory_view', {
            'vcategory_id': item_id})))
                
    return commands


def _context_menu_url_for(url: str, params: dict = None) -> str:
    if params is not None:
        url = '{}?{}'.format(url, urlencode(params))
    url = globals.router.url_for_path(url)
    return f'RunPlugin({url})'
