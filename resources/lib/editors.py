# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: metadata editor actions
#

# Copyright (c) Chrisism <crizizz@gmail.com>
# Portions (c) Wintermute0110 <wintermute0110@gmail.com> 
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
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import collections

import xbmcgui

from akl.utils import kodi, io, text
from akl import constants, settings

from resources.lib.domain import MetaDataItemABC, AssetInfo, g_assetFactory

logger = logging.getLogger(__name__)

# Edits an object field which is a Unicode string.
#
# Example call:
#   edit_field_by_str(collection, 'Title', collection.get_title, collection.set_title)
#
def edit_field_by_str(obj_instance: MetaDataItemABC, metadata_name, get_method, set_method) -> bool:
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    s = kodi.translate(41137).format(object_name, old_value, metadata_name)
    new_value = kodi.dialog_keyboard(s, old_value)
    if new_value is None:
        return False

    if old_value == new_value:
        kodi.notify(kodi.translate(40987).format(object_name, metadata_name))
        return False
    set_method(new_value)
    kodi.notify(kodi.translate(40986).format(object_name, metadata_name, new_value))
    return True

# Edits an object field which is an integer.
#
# Example call:
#   edit_field_by_int(collection, 'Title', collection.get_number_of_players, collection.get_number_of_players)
#
def edit_field_by_int(obj_instance: MetaDataItemABC, metadata_name, get_method, set_method) -> bool:
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    s = kodi.translate(41137).format(object_name, old_value, metadata_name)
    new_value = kodi.dialog_numeric(s, old_value)
    if new_value is None: return False

    if old_value == new_value:
        kodi.notify(kodi.translate(40987).format(object_name, metadata_name))
        return False
    set_method(new_value)
    kodi.notify(kodi.translate(40986).format(object_name, metadata_name, new_value))
    return True

#
# The values of str_list are supposed to be unique.
#
# Example call:
# edit_field_by_list('Launcher', 'Platform', AEL_platform_list,
#                          launcher.get_platform, launcher.set_platform)
#
def edit_field_by_list(obj_instance: MetaDataItemABC, metadata_name:str, str_list: list, get_method, set_method) -> bool:
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    if old_value in str_list:
        preselect_idx = str_list.index(old_value)
    else:
        preselect_idx = 0
    dialog_title = kodi.translate(41075).format(object_name, metadata_name)
    selected = kodi.ListDialog().select(dialog_title, str_list, preselect_idx)
    if selected is None:
        return
    new_value = str_list[selected]
    if old_value == new_value:
        kodi.notify(kodi.translate(40987).format(object_name, metadata_name))
        return False

    set_method(new_value)
    kodi.notify(kodi.translate(40986).format(object_name, metadata_name, new_value))
    return True

#
# Rating 'Not set' is stored as an empty string.
# Rating from 0 to 10 is stored as a string, '0', '1', ..., '10'
# Returns True if the rating value was changed.
# Returns Flase if the rating value was NOT changed.
# Example call:
#   edit_rating('ROM Collection', collection.get_rating, collection.set_rating)
#
def edit_rating(obj_instance: MetaDataItemABC, get_method, set_method):
    options_list = [
        kodi.translate(42001),
        kodi.translate(42002).format('0'),
        kodi.translate(42002).format('1'),
        kodi.translate(42002).format('2'),
        kodi.translate(42002).format('3'),
        kodi.translate(42002).format('4'),
        kodi.translate(42002).format('5'),
        kodi.translate(42002).format('6'),
        kodi.translate(42002).format('7'),
        kodi.translate(42002).format('8'),
        kodi.translate(42002).format('9'),
        kodi.translate(42002).format('10')
    ]
    object_name = obj_instance.get_object_name()
    current_rating_str = get_method()
    if not current_rating_str:
        preselected_value = 0
    else:
        preselected_value = int(current_rating_str) + 1
    sel_value = kodi.ListDialog().select(kodi.translate(41079).format(object_name),
                                        options_list, preselect_idx = preselected_value)
    if sel_value is None: return
    if sel_value == preselected_value:
        kodi.notify(kodi.translate(40988).format(object_name))
        return False

    if sel_value == 0:
        current_rating_str = ''
    elif sel_value >= 1 and sel_value <= 11:
        current_rating_str = '{0}'.format(sel_value - 1)
    elif sel_value < 0:
        kodi.notify(kodi.translate(40988).format(object_name))
        return False

    set_method(current_rating_str)
    kodi.notify(kodi.translate(40989).format(object_name, current_rating_str))
    return True

#
# Reads a text file with category/launcher plot. 
# Checks file size to avoid importing binary files!
#
def import_TXT_file(text_file: io.FileName):
    # Warn user in case he chose a binary file or a very big one. Avoid categories.xml corruption.
    logger.debug('import_TXT_file() Importing plot from "{0}"'.format(text_file.getPath()))
    statinfo = text_file.stat()
    file_size = statinfo.st_size
    logger.debug('import_TXT_file() File size is {0}'.format(file_size))
    if file_size > 16384:
        ret = kodi.dialog_yesno(kodi.translate(41070).format(text_file.getPath(), file_size))
        if not ret: return ''

    # Import file
    logger.debug('import_TXT_file() Importing description from "{0}"'.format(text_file.getPath()))
    file_data = text_file.readAll()

    return file_data

SCRAPE_CMD = 'SCRAPE_ROM_ASSETS'

def edit_object_assets(obj_instance:MetaDataItemABC, preselected_asset = None) -> str:
    logger.debug('edit_object_assets() obj_instance {0}'.format(obj_instance.__class__.__name__))
    logger.debug('edit_object_assets() preselected_asset {0}'.format(preselected_asset if preselected_asset is not None else 'NONE'))

    # --- Build options list ---
    assets = obj_instance.get_available_assets()
    options = collections.OrderedDict()
    for asset in assets:
        asset_info_obj = asset.get_asset_info()
        asset_fname_str = asset.get_path()
        
        # --- Create ListItems ---
        # >> Label1 is the asset name (Icon, Fanart, etc.)
        # >> Label2 is the asset filename str as in the database or 'Not set'
        # >> setArt('icon') is the asset picture.
        label1_str = kodi.translate(42003).format(asset_info_obj.name)
        label2_stt = asset_fname_str if asset_fname_str else 'Not set'
        list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_stt)
        if asset_fname_str:
            item_path = io.FileName(asset_fname_str)
            if item_path.isVideoFile():
                item_img = 'DefaultAddonVideo.png'
            elif item_path.isManualFile():
                item_img = 'DefaultAddonInfoProvider.png'
            else:
                item_img = asset_fname_str
        else:
            item_img = 'DefaultAddonNone.png'
        list_item.setArt({'icon' : item_img})
        # --- Append to list of ListItems ---
        options[asset_info_obj.id] = list_item

    # if ROM then add scrape option
    if obj_instance.get_object_name() == 'ROM':
        options[SCRAPE_CMD] = kodi.translate(41120)
    
    # --- Customize function for each object type ---
    dialog_title_str = kodi.translate(41076). format(obj_instance.get_object_name())
    dialog = kodi.OrdDictionaryDialog()
    selected_option = dialog.select(dialog_title_str, options, preselect = preselected_asset, use_details = True)

    if selected_option is None:
        # >> Return to parent menu.
        logger.debug('edit_object_assets() Selected NONE. Returning to parent menu.')
        return selected_option
    
    logger.debug('edit_object_assets() select() returned {0}'.format(selected_option))
    return selected_option
    
#
# Edit category/collection/launcher/ROM asset.
# asset_info is a AssetInfo() object instance.
#
# NOTE Caller is responsible for saving the Categories/Launchers/ROMs.
# NOTE If image is changed container should be updated so the user sees new image instantly.
# NOTE obj_instance is edited by assigment.
#
# Returns:
#   Command   The cmd that was executed. (SCRAPE_ASSET cmd will not be executed directly)
#   None      No changes were made. No necessary to refresh container
#
def edit_asset(obj_instance: MetaDataItemABC, asset_info: AssetInfo) -> str:
    # --- Get asset object information ---
    assets_directory = obj_instance.get_assets_root_path()        
    if not assets_directory:
        if kodi.dialog_yesno(kodi.translate(41047)):
            path_str = kodi.dialog_get_directory(kodi.translate(41138).format(obj_instance.get_name()))
            assets_directory = io.FileName(path_str, True)
            obj_instance.set_assets_root_path(assets_directory, None, create_default_subdirectories=True)
        else:
            if obj_instance.get_assets_kind() == constants.KIND_ASSET_CATEGORY:
                assets_directory = io.FileName(settings.getSetting('categories_asset_dir'), isdir = True)
                obj_instance.set_assets_root_path(assets_directory, None, create_default_subdirectories=True)
            elif obj_instance.get_assets_kind() == constants.KIND_ASSET_COLLECTION:
                assets_directory = io.FileName(settings.getSetting('collections_asset_dir'), isdir = True)
                obj_instance.set_assets_root_path(assets_directory, None, create_default_subdirectories=True)
            elif obj_instance.get_assets_kind() == constants.KIND_ASSET_LAUNCHER:
                assets_directory = io.FileName(settings.getSetting('launchers_asset_dir'), isdir = True)
                obj_instance.set_assets_root_path(assets_directory, None, create_default_subdirectories=True)
            elif obj_instance.get_assets_kind() == constants.KIND_ASSET_ROM:
                assets_directory = io.FileName(settings.getSetting('launchers_asset_dir'), isdir = True)
                obj_instance.set_assets_root_path(assets_directory, None, create_default_subdirectories=True)
            else:
                kodi.dialog_OK(kodi.translate(41140).format(obj_instance.get_assets_kind()))
                return None

    asset_type_directory = obj_instance.get_asset_path(asset_info, False)    

    logger.info(f'edit_asset() Editing {obj_instance.get_object_name()} {asset_info.name}')
    logger.info(f'edit_asset() Object ID {obj_instance.get_id()}')
    logger.debug(f'edit_asset() assets_directory "{assets_directory.getPath()}"')
    logger.debug(f'edit_asset() asset_type_directory "{asset_type_directory.getPath() if asset_type_directory else "None"}"')

    if not assets_directory.exists():
        logger.error(f'Directory not found "{assets_directory.getPath()}"')
        kodi.dialog_OK(kodi.translate(41139))
        return None

    dialog_title = kodi.translate(41074).format(obj_instance.get_name(), asset_info.name)
    
    # --- Show image editing options ---
    options = collections.OrderedDict()
    options['LINK_LOCAL'] = kodi.translate(42004).format(asset_info.name)
    options['IMPORT_LOCAL'] = kodi.translate(42005).format(asset_info.name)
    options['UNSET'] = kodi.translate(42006)
    if obj_instance.get_assets_kind() == constants.KIND_ASSET_ROM:
        options['SCRAPE_ASSET'] = kodi.translate(42007).format(asset_info.name)
        
    selected_option = kodi.OrdDictionaryDialog().select(dialog_title, options)
    
    # >> User canceled select box
    if selected_option is None:
        return None

    # --- Manual scrape asset ---
    if selected_option == 'SCRAPE':
        return selected_option
    
    # --- Link to a local image ---
    if selected_option == 'LINK_LOCAL':
        current_image_file = obj_instance.get_asset_FN(asset_info)
        if current_image_file is None:
            current_image_dir = obj_instance.get_asset_path(asset_info)
            if current_image_dir is None or not assets_directory.exists():
                current_image_dir = obj_instance.get_assets_root_path()
        else: 
            current_image_dir = io.FileName(current_image_file.getDir(), isdir = True)
        
        if current_image_dir is None:
            current_image_dir = io.FileName('/')
        
        logger.debug(f'edit_asset() Asset initial dir "{current_image_dir.getPath()}"')
        title_str = kodi.translate(41141).format(obj_instance.get_object_name(), kodi.translate(asset_info.name_id))
        ext_list = asset_info.exts_dialog
        if asset_info.id == constants.ASSET_MANUAL_ID or asset_info.id == constants.ASSET_TRAILER_ID:
            new_asset_file = kodi.browse(text=title_str, mask=ext_list, preselected_path=current_image_dir.getPath())
        else:
            new_asset_file = kodi.browse(type=2, text=title_str, mask=ext_list, preselected_path=current_image_dir.getPath())
        
        if not new_asset_file or new_asset_file == current_image_dir.getPath():
            return None
        # --- Check if image exists ---
        new_asset_FN = io.FileName(new_asset_file)
        if not new_asset_FN.exists():
            return None

        # --- Update object ---
        obj_instance.set_asset(asset_info, new_asset_FN)
        logger.debug(f'edit_asset() Asset id "{asset_info.id}"')
        logger.debug('edit_asset() Linked {0} {1} to "{2}"'.format(
            obj_instance.get_object_name(), asset_info.name, new_asset_FN.getPath())
        )

        # --- Update Kodi image cache ---
        # Addons cannot manipulate Kodi cache. If the timestamp of a file is updated then
        # Kodi must update the cache immediately.
        # kodi_update_image_cache(new_asset_FN)

        # --- Notify user ---
        kodi.notify(kodi.translate(40990).format(obj_instance.get_object_name(), asset_info.name))

    # --- Import an image ---
    # >> Copy and rename a local image into asset directory
    elif selected_option == 'IMPORT_LOCAL':
        current_image_dir = asset_type_directory
        if not current_image_dir:
            logger.info("No local asset type path configured. Reverting to root.")
            current_image_dir = obj_instance.get_assets_root_path()
        
        title_str = kodi.translate(41141).format(obj_instance.get_object_name(), kodi.translate(asset_info.name_id))
        ext_list = asset_info.exts_dialog
        if asset_info.id == constants.ASSET_MANUAL_ID or asset_info.id == constants.ASSET_TRAILER_ID:
            new_asset_file_str = kodi.browse(text=title_str, mask=ext_list, preselected_path=current_image_dir.getPath())
        else:
            new_asset_file_str = kodi.browse(type=2, text=title_str, mask=ext_list, preselected_path=current_image_dir.getPath())
            
        if not new_asset_file_str:
            return None

        # >> Determine image extension and dest filename. Check for errors.
        new_asset_file = io.FileName(new_asset_file_str)
        obj_identifier = text.str_to_filename_str(obj_instance.get_name())
        
        asset_path_noext = asset_type_directory.pjoin(obj_identifier)
        dest_asset_file = asset_path_noext.append(new_asset_file.getExt())
        logger.debug(f'edit_asset() new_asset_file     "{new_asset_file.getPath()}"')
        logger.debug(f'edit_asset() new_asset_file ext "{new_asset_file.getExt()}"')
        logger.debug(f'edit_asset() dest_asset_file    "{dest_asset_file.getPath()}"')
        if new_asset_file.getPath() == dest_asset_file.getPath():
            logger.info('edit_asset() new_asset_file and dest_asset_file are the same. Returning.')
            kodi.notify_warn(kodi.translate(40991))
            return None

        # --- Kodi image cache ---
        # The Kodi image cache cannot be manipulated by addons directly.
        # If seems that changing the atime and mtime does not force an update of the Kodi cache
        # when a new image is copied over an existing image. Copying a new image into an old
        # one does not change the ctime.
        # SOLUTION if the destination images exists, delete it before copying the new one. the
        #          ctime if the new image will be updated.
        # NOTE deleting the destination image before copying does not work to force a cache
        #      update.
        # if dest_asset_file.exists():
        #     logger.debug('edit_asset() Deleting image "{0}"'.format(dest_asset_file.getPath()))
        #     dest_asset_file.unlink()

        # --- Copy image file ---
        try:
            # fs_encoding = get_fs_encoding()
            # shutil.copy(new_asset_file.getPath().decode(fs_encoding), dest_asset_file.getPath().decode(fs_encoding))
            new_asset_file.copy(dest_asset_file)
        except constants.AddonError:
            logger.error('edit_asset() AddonException exception copying image')
            kodi.notify_warn(kodi.translate(40992))
            return None

        # --- Update object ---
        # >> Always store original/raw paths in database.
        obj_instance.set_asset(asset_info, dest_asset_file)
        logger.debug(f'edit_asset() Asset ID "{asset_info.id}"')
        logger.debug(f'edit_asset() Copied file  "{new_asset_file.getPath()}"')
        logger.debug(f'edit_asset() Into         "{dest_asset_file.getPath()}"')
        logger.debug('edit_asset() Linked {0} {1} to "{2}"'.format(
            obj_instance.get_object_name(), asset_info.name, dest_asset_file.getPath())
        )

        # --- DEBUG code to investigate Kodi image cache ---
        # logger.debug('current_image_file atime {0}'.format(time.ctime(os.path.getatime(current_image_file.getPath()))))
        # logger.debug('current_image_file mtime {0}'.format(time.ctime(os.path.getmtime(current_image_file.getPath()))))
        # logger.debug('current_image_file ctime {0}'.format(time.ctime(os.path.getctime(current_image_file.getPath()))))
        # logger.debug('new_asset_file  atime {0}'.format(time.ctime(os.path.getatime(new_asset_file.getPath()))))
        # logger.debug('new_asset_file  mtime {0}'.format(time.ctime(os.path.getmtime(new_asset_file.getPath()))))
        # logger.debug('new_asset_file  ctime {0}'.format(time.ctime(os.path.getctime(new_asset_file.getPath()))))
        # logger.debug('dest_asset_file atime {0}'.format(time.ctime(os.path.getatime(dest_asset_file.getPath()))))
        # logger.debug('dest_asset_file mtime {0}'.format(time.ctime(os.path.getmtime(dest_asset_file.getPath()))))
        # logger.debug('dest_asset_file ctime {0}'.format(time.ctime(os.path.getctime(dest_asset_file.getPath()))))

        # >> Copying a file updates atime and mtime but not ctime. ctime of the new file is the
        # >> ctime of the old file (tested on Windows).
        # logger.debug('m_gui_edit_asset() Updating destination file atime and mtime')
        # os.utime(dest_asset_file.getPath(), (time.time(), time.time()))
        # logger.debug('dest_asset_file  atime {0}'.format(time.ctime(os.path.getatime(dest_asset_file.getPath()))))
        # logger.debug('dest_asset_file  mtime {0}'.format(time.ctime(os.path.getmtime(dest_asset_file.getPath()))))
        # logger.debug('dest_asset_file  ctime {0}'.format(time.ctime(os.path.getctime(dest_asset_file.getPath()))))

        # --- Delete cached image to force a cache update ---
        try:
            kodi.delete_cache_texture(dest_asset_file.getPath())
            kodi.print_texture_info(dest_asset_file.getPath())
        except Exception:
            logger.exception("Failed to delete cache")

        # --- Notify user ---
        kodi.notify(kodi.translate(40994).format(obj_instance.get_object_name(), asset_info.name))

    # --- Unset asset ---
    elif selected_option == 'UNSET':
        obj_instance.set_asset(asset_info, io.FileName(''))
        logger.info('edit_asset() Unset {0} {1}'.format(obj_instance.get_object_name(), asset_info.name))
        kodi.notify(kodi.translate(40993).format(obj_instance.get_object_name(), asset_info.name))
    
    return selected_option

#
# Generic function to edit the Object default assets for 
# icon/fanart/banner/poster/clearlogo context submenu.
# Argument obj is an object instance of class Category, CollectionLauncher, etc.
#
def edit_object_default_assets(obj_instance: MetaDataItemABC, preselected_asset_id = None) -> AssetInfo:
    logger.debug('edit_object_default_assets() obj {0}'.format(obj_instance.__class__.__name__))
    logger.debug('edit_object_default_assets() preselected_asset_id {0}'.format(preselected_asset_id))
    
    pre_select_idx = 0
    dialog_title_str = kodi.translate(41077).format(obj_instance.get_object_name())

    # --- Build Dialog.select() list ---
    default_assets_list = obj_instance.get_mappable_asset_list()
    list_items = []
    # >> List to easily pick the selected AssetInfo() object
    asset_info_list = []
    counter = 0
    for default_asset_info in default_assets_list:
        # >> Label 1 is the string 'Choose asset for XXXX (currently YYYYY)'
        # >> Label 2 is the fname string of the current mapped asset or 'Not set'
        # >> icon is the fname string of the current mapped asset.
        mapped_asset_info = obj_instance.get_asset_mapping(default_asset_info)
        mapped_asset_str = obj_instance.get_asset_str(mapped_asset_info)
        label1_str = kodi.translate(42055).format(
            kodi.translate(default_asset_info.name_id), 
            kodi.translate(mapped_asset_info.name_id))
        label2_str = mapped_asset_str
        list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_str)
        if mapped_asset_str:
            item_path = io.FileName(mapped_asset_str)
            if item_path.isVideoFile():
                item_img = 'DefaultAddonVideo.png'
            elif item_path.isManualFile():
                item_img = 'DefaultAddonInfoProvider.png'
            else:
                item_img = mapped_asset_str
        else:
            item_img = 'DefaultAddonNone.png'
        list_item.setArt({'icon' : item_img})
        # --- Append to list of ListItems ---
        list_items.append(list_item)
        asset_info_list.append(default_asset_info)
        
        if default_asset_info.id == preselected_asset_id:
            pre_select_idx = counter
        counter += 1

    selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True, preselect = pre_select_idx)
    logger.debug(f'edit_object_default_assets() Main select() returned {selected_option}')
    if selected_option < 0:
        # >> Return to parent menu.
        logger.debug('edit_object_default_assets() Main selected NONE. Returning to parent menu.')
        return None
        
    # >> Execute edit default asset submenu. Then, execute recursively this submenu again.
    # >> The menu dialog is instantiated again so it reflects the changes just edited.
    logger.debug('edit_object_default_assets() Executing mappable asset select() dialog.')
    selected_asset_info:AssetInfo = asset_info_list[selected_option]
    logger.debug(f'edit_object_default_assets() Main selected {selected_asset_info.name}.')
    return selected_asset_info            

def edit_default_asset(obj_instance: MetaDataItemABC, asset_info: AssetInfo) -> bool:
    selectable_asset_ids = obj_instance.get_asset_ids_list()
    mappable_asset_list = g_assetFactory.get_asset_list_by_IDs(selectable_asset_ids, 'image')
    list_items = []
    asset_info_list = []
    secondary_pre_select_idx = 0
    counter = 0
    for mappable_asset_info in mappable_asset_list:
        # --- Create ListItems ---
        # >> Label1 is the asset name (Icon, Fanart, etc.)
        # >> Label2 is the asset filename str as in the database or 'Not set'
        # >> setArt('icon') is the asset picture.
        mapped_asset_str = obj_instance.get_asset_str(mappable_asset_info)
        label1_str = mappable_asset_info.name
        label2_str = mapped_asset_str if mapped_asset_str else kodi.translate(42001)
        list_item = xbmcgui.ListItem(label = label1_str, label2 = label2_str)
        if mapped_asset_str:
            item_path = io.FileName(mapped_asset_str)
            if item_path.isVideoFile():
                item_img = 'DefaultAddonVideo.png'
            elif item_path.isManualFile():
                item_img = 'DefaultAddonInfoProvider.png'
            else:
                item_img = mapped_asset_str
        else:
            item_img = 'DefaultAddonNone.png'
        list_item.setArt({'icon' : item_img})
        # --- Append to list of ListItems ---
        list_items.append(list_item)
        asset_info_list.append(mappable_asset_info)
        if mappable_asset_info == asset_info:
            secondary_pre_select_idx = counter
        counter += 1
    
    dialog_title_str = kodi.translate(41078).format(obj_instance.get_object_name(), asset_info.name)
    secondary_selected_option = xbmcgui.Dialog().select(
            dialog_title_str, list = list_items, useDetails = True, preselect = secondary_pre_select_idx)
    logger.debug('edit_default_asset() Mapable select() returned {0}'.format(secondary_selected_option))
    if secondary_selected_option < 0:
        # >> Return to parent menu.
        logger.debug('edit_default_asset() Mapable selected NONE. Returning to parent menu.')
        return False
        
    new_selected_asset_info = asset_info_list[secondary_selected_option]
    logger.debug(f'edit_default_asset() Mapable selected {new_selected_asset_info.name}.')
    obj_instance.set_mapped_asset(asset_info, new_selected_asset_info)
    kodi.notify(kodi.translate(40983).format(
        obj_instance.get_object_name(), asset_info.name, new_selected_asset_info.name
    ))
    return True