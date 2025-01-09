# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Default scraper implementation
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

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging

# --- AKL packages ---
from akl import constants, settings
from akl.scrapers import Scraper
from akl.api import ROMObj

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------------------------
# Local files scraper.
# ------------------------------------------------------------------------------------------------
class LocalFilesScraper(Scraper):
    
    supported_metadata_list = [
        constants.META_TITLE_ID,
        constants.META_YEAR_ID,
        constants.META_GENRE_ID,
        constants.META_DEVELOPER_ID,
        constants.META_NPLAYERS_ID,
        constants.META_ESRB_ID,
        constants.META_PLOT_ID,
    ]
     
    # --- Constructor ----------------------------------------------------------------------------
    def __init__(self):
        cache_dir = settings.getSettingAsFilePath('scraper_cache_dir')
        super(LocalFilesScraper, self).__init__(cache_dir)

    # --- Base class abstract methods ------------------------------------------------------------
    def get_name(self):
        return 'Local files scraper'

    def get_filename(self):
        return 'Local_files'

    def supports_disk_cache(self):
        return False

    def supports_search_string(self):
        return False

    def supports_metadata_ID(self, metadata_ID):
        return metadata_ID in LocalFilesScraper.supported_metadata_list

    def supports_metadata(self):
        return True

    def supports_asset_ID(self, asset_ID):
        return True

    def supports_assets(self):
        return True

    def check_before_scraping(self, status_dic):
        return status_dic

    def get_candidates(self, search_term, rom: ROMObj, platform, status_dic):
        return []

    def get_metadata(self, status_dic):
        return self._new_gamedata_dic()

    def get_assets(self, asset_info, status_dic):
        return []

    def resolve_asset_URL(self, selected_asset, status_dic):
        pass

    def resolve_asset_URL_extension(self, selected_asset, image_url, status_dic):
        pass
