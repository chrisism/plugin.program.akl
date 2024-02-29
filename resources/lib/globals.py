# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Globals
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
#
# Globals to be used by the addon

import routing
# --- Kodi stuff ---
import xbmcaddon

from akl.utils import io

# --- Addon object (used to access settings) ---
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_name = addon.getAddonInfo('name')
addon_version = addon.getAddonInfo('version')
addon_author = addon.getAddonInfo('author')
addon_profile = addon.getAddonInfo('profile')
addon_type = addon.getAddonInfo('type')
addon_path = addon.getAddonInfo('path')


# --- Addon paths and constant definition ---
# _PATH is a filename | _DIR is a directory.
class AKL_Paths(object):
    def __init__(self, addon_id):
        # --- Base paths ---
        self.HOME_DIR = io.FileName('special://home')
        self.PROFILE_DIR = io.FileName('special://profile')
        self.ADDONS_DATA_DIR = io.FileName('special://profile/addon_data')
        #  self.DATABASE_DIR     = io.FileName('special://database')
        
        self.ADDON_DATA_DIR = self.ADDONS_DATA_DIR.pjoin(addon_id)
        self.ADDONS_CODE_DIR = self.HOME_DIR.pjoin('addons', True)
        self.ADDON_CODE_DIR = self.ADDONS_CODE_DIR.pjoin(addon_id)
        self.ICON_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/icon.png')
        self.FANART_FILE_PATH = self.ADDON_CODE_DIR.pjoin('media/fanart.jpg')
        self.DATABASE_SCHEMA_PATH = self.ADDON_CODE_DIR.pjoin('resources/schema.sql')
        self.DATABASE_MIGRATIONS_PATH = self.ADDON_CODE_DIR.pjoin('resources/migrations', True)

        # -- Root data file
        self.ROOT_PATH = self.ADDON_DATA_DIR.pjoin('root.json')
        # --- Databases and reports ---
        self.DATABASE_FILE_PATH = self.ADDON_DATA_DIR.pjoin('akl.db')
        # --- datetime peek file for automatic scanning ---
        self.SCAN_INDICATOR_FILE = self.ADDON_DATA_DIR.pjoin('auto_scan.txt')

        # --- Offline scraper databases ---
        self.GAMEDB_INFO_DIR = self.ADDON_CODE_DIR.pjoin('data-AOS')
        self.GAMEDB_JSON_BASE_NOEXT = 'AOS_GameDB_info'
        # self.LAUNCHBOX_INFO_DIR        = self.ADDON_CODE_DIR.pjoin('LaunchBox')
        # self.LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'

        # --- Online scraper on-disk cache ---
        self.SCRAPER_CACHE_DIR = self.ADDON_DATA_DIR.pjoin('ScraperCache')

        # --- Artwork and NFO for Categories and Launchers ---
        self.DEFAULT_CAT_ASSET_DIR = self.ADDON_DATA_DIR.pjoin('asset-categories')
        self.DEFAULT_COL_ASSET_DIR = self.ADDON_DATA_DIR.pjoin('asset-collections')
        self.DEFAULT_ROM_ASSET_DIR = self.ADDON_DATA_DIR.pjoin('asset-roms')
        self.DEFAULT_FAV_ASSET_DIR = self.ADDON_DATA_DIR.pjoin('asset-favourites')
        
        # --- Rendered views (normal and virtuals/generated) ---
        self.SOURCES_VIEW_PATH = self.ADDON_DATA_DIR.pjoin('sources.json')
        self.GENERATED_VIEWS_DIR = self.ADDON_DATA_DIR.pjoin('db_generated_views')
        self.VIEWS_DIR = self.ADDON_DATA_DIR.pjoin('db_views')
        
        # Reports
        self.REPORTS_DIR = self.ADDON_DATA_DIR.pjoin('reports')
        self.BIOS_REPORT_FILE_PATH = self.REPORTS_DIR.pjoin('report_BIOS.txt')
        self.COLLECTIONS_REPORT_FILE_PATH = self.REPORTS_DIR.pjoin('report_collections.txt')
        self.ROM_SYNC_REPORT_FILE_PATH = self.REPORTS_DIR.pjoin('report_ROM_sync_status.txt')
        self.ROM_ART_INTEGRITY_REPORT_FILE_PATH = self.REPORTS_DIR.pjoin('report_ROM_artwork_integrity.txt')
        self.ROM_REDUNDANT_FILES_REPORT_FILE_PATH = self.REPORTS_DIR.pjoin('report_ROM_redundant_files.txt')

    def build(self):
        # --- Addon data paths creation ---
        if not self.ADDON_DATA_DIR.exists():
            self.ADDON_DATA_DIR.makedirs()
        if not self.SCRAPER_CACHE_DIR.exists():
            self.SCRAPER_CACHE_DIR.makedirs()
        if not self.REPORTS_DIR.exists():
            self.REPORTS_DIR.makedirs()
        
        if not self.DEFAULT_CAT_ASSET_DIR.exists():
            self.DEFAULT_CAT_ASSET_DIR.makedirs()
        if not self.DEFAULT_COL_ASSET_DIR.exists():
            self.DEFAULT_COL_ASSET_DIR.makedirs()
        if not self.DEFAULT_ROM_ASSET_DIR.exists():
            self.DEFAULT_ROM_ASSET_DIR.makedirs()
        if not self.DEFAULT_FAV_ASSET_DIR.exists():
            self.DEFAULT_FAV_ASSET_DIR.makedirs()
        
        if not self.GENERATED_VIEWS_DIR.exists():
            self.GENERATED_VIEWS_DIR.makedirs()
        if not self.VIEWS_DIR.exists():
            self.VIEWS_DIR.makedirs()

        return self


router: routing.Plugin = routing.Plugin()
g_PATHS: AKL_Paths

WEBSERVER_HOST = '127.0.0.1'
WEBSERVER_PORT = 57300


#
# Bootstrap factory object instances.
#
def g_bootstrap_instances():
    global g_PATHS    
    g_PATHS = AKL_Paths(addon_id).build()
