# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (source roms management)
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
import typing

import xbmcgui

from akl import constants, platforms
from akl.utils import kodi, io

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals, editors
from resources.lib.repositories import UnitOfWork, SourcesRepository, ROMsRepository, ROMsJsonFileRepository
from resources.lib.repositories import AelAddonRepository, LaunchersRepository
from resources.lib.domain import ROM, Source, AelAddon, AssetInfo, g_assetFactory, ROMLauncherAddonFactory

logger = logging.getLogger(__name__)


# --- Main menu commands ---
@AppMediator.register('ADD_SOURCE')
def cmd_add_source(args):
    logger.debug('cmd_add_source() BEGIN')
    
    options = collections.OrderedDict()
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        addon_repository = AelAddonRepository(uow)
        source_repository = SourcesRepository(uow)
        
        addons = addon_repository.find_all_scanner_addons()
        for addon in addons:
            options[addon] = addon.get_name()
        options['STANDALONE_SOURCE'] = kodi.translate(40890)
    
        s = kodi.translate(41107)
        selected_option: AelAddon = kodi.OrdDictionaryDialog().select(s, options)

        if selected_option is None:
            # >> Exits context menu
            logger.debug('ADD_SOURCE: cmd_add_source() Selected None. Closing context menu')
            return
        
        if selected_option == "STANDALONE_SOURCE":
            logger.debug(f'ADD_SOURCE: Selected {selected_option}')
            AppMediator.sync_cmd(selected_option, args)
            return
        
        logger.debug(f'ADD_SOURCE: Selected {selected_option.get_id()}')
        source = Source(None, selected_option)
        
        wizard = kodi.WizardDialog_Selection(None, 'platform', kodi.translate(41099), platforms.AKL_platform_list)
        wizard = kodi.WizardDialog_Dummy(wizard, 'name', '', _get_name_from_platform)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'name', kodi.translate(41166))
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'assets_path', kodi.translate(42038), 0, '')
        
        source = Source(None, selected_option)
        entity_data = source.get_data_dic()
        entity_data = wizard.runWizard(entity_data)
        if entity_data is None:
            return
        
        source.import_data_dic(entity_data)
        
        # --- create assets directory ---
        assets_path = entity_data['assets_path']
        assets_path_FN = io.FileName(assets_path)
        source.set_assets_root_path(assets_path_FN, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=True)
                
        # --- Determine box size based on platform --
        platform = platforms.get_AKL_platform(entity_data['platform'])
        source.set_box_sizing(platform.default_box_size)
        
        source_repository.insert_source(source)
        uow.commit()
        
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        selected_option.get_addon_id(),
        source.get_configure_command())


@AppMediator.register('EDIT_SOURCE')
def cmd_edit_source(args):
    logger.debug('EDIT_SOURCE: cmd_edit_source() BEGIN')
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    if source_id is None:
        logger.warning('cmd_edit_source(): No source_id id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)

    options = collections.OrderedDict()
    options['SOURCE_EDIT_TITLE'] = kodi.translate(40863).format(source.get_name())
    options['SOURCE_EDIT_PLATFORM'] = kodi.translate(40864).format(source.get_platform())
    options['SOURCE_EDIT_BOXSIZE'] = kodi.translate(40875).format(source.get_box_sizing())
    options['SOURCE_EDIT_SCANNER'] = kodi.translate(42081)
    if source.has_launchers():
        options['EDIT_SOURCE_LAUNCHERS'] = kodi.translate(42016)
    else:
        options['ADD_SOURCE_LAUNCHER'] = kodi.translate(42026)
    options['SOURCE_MANAGE_ROMS'] = kodi.translate(42039)
    options['DELETE_SOURCE'] = kodi.translate(42085)

    s = kodi.translate(41167).format(source.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('EDIT_SOURCE: cmd_edit_source() Selected None. Closing context menu')
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'EDIT_SOURCE: cmd_edit_source() Selected {selected_option}')
    AppMediator.sync_cmd(selected_option, args)


@AppMediator.register('SOURCE_EDIT_TITLE')
def cmd_source_title(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
        
        s = kodi.translate(41137).format(
            kodi.translate(constants.OBJ_SOURCE),
            source.get_name(),
            kodi.translate(40812))
        new_value = kodi.dialog_keyboard(s, source.get_name())
        if new_value is not None and source.get_name() != new_value:
            source.set_name(new_value)
            kodi.notify(kodi.translate(40986).format(
                kodi.translate(constants.OBJ_SOURCE),
                kodi.translate(40812),
                new_value))
        
            repository.update_source(source)
            uow.commit()
            AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
            AppMediator.async_cmd('RENDER_SOURCES_VIEW')
        else:
            kodi.notify(kodi.translate(40987).format(
                kodi.translate(constants.OBJ_SOURCE),
                kodi.translate(40812)))
    AppMediator.sync_cmd('EDIT_SOURCE', args)


@AppMediator.register('SOURCE_EDIT_PLATFORM')
def cmd_source_metadata_platform(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
    
        if editors.edit_field_by_list(source, kodi.translate(40807), platforms.AKL_platform_list,
                                      source.get_platform, source.set_platform):
            repository.update_source(source)
            update_roms_too = kodi.dialog_yesno(kodi.translate(40982))
            
            if update_roms_too:
                roms_repository = ROMsRepository(uow)
                roms_to_update = roms_repository.find_roms_by_source(source)
                platform_to_apply = source.get_platform()
                for rom in roms_to_update:
                    rom.set_platform(platform_to_apply)
                    roms_repository.update_rom(rom)

            uow.commit()
            AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
            AppMediator.async_cmd('RENDER_SOURCES_VIEW')
    AppMediator.sync_cmd('EDIT_SOURCE', args)


@AppMediator.register('SOURCE_EDIT_BOXSIZE')
def cmd_source_boxsize(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)

        if editors.edit_field_by_list(source, kodi.translate(40816), constants.BOX_SIZES,
                                      source.get_box_sizing, source.set_box_sizing):
            repository.update_source(source)
            uow.commit()
            AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
            AppMediator.async_cmd('RENDER_SOURCES_VIEW')
    AppMediator.sync_cmd('EDIT_SOURCE', args)


@AppMediator.register('SOURCE_EDIT_SCANNER')
def cmd_edit_source_scanner(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
     
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        source.addon.get_addon_id(),
        source.get_configure_command())
       

@AppMediator.register('DELETE_SOURCE')
def cmd_source_delete(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
        source_name = source.get_name()
        collection_ids = repository.find_romcollection_ids_by_source(source_id)
        
        if source.num_roms() > 0:
            question = kodi.translate(41169).format(source_name, source.num_roms()) + \
                kodi.translate(41066).format(source_name)
        else:
            question = kodi.translate(41066).format(source_name)
    
        ret = kodi.dialog_yesno(question)
        if not ret:
            return
            
        logger.info(f'Deleting source "{source_name}" ID {source.get_id()}')
        repository.delete_source(source.get_id())
        uow.commit()
        AppMediator.async_cmd('RENDER_SOURCES_VIEW')
        
    kodi.notify(kodi.translate(41170).format(source_name))
    for collection_id in collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
    AppMediator.async_cmd('CLEANUP_VIEWS')


# -------------------------------------------------------------------------------------------------
# ROM ADD
# -------------------------------------------------------------------------------------------------
@AppMediator.register('STANDALONE_SOURCE')
def cmd_add_standalone_source(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        addons_repository = AelAddonRepository(uow)
        launchers_repository = LaunchersRepository(uow)
        
        launchers = launchers_repository.find_all()

        file_path = kodi.dialog_get_file(kodi.translate(40953))
        if file_path is not None:
            path = io.FileName(file_path)
            rom_name = path.getBaseNoExt()
            
        rom_name = kodi.dialog_keyboard(kodi.translate(40815), rom_name)
        if rom_name is None:
            return
        
        dialog = kodi.ListDialog()
        selected_idx = dialog.select(kodi.translate(41099), platforms.AKL_platform_list)
        platform = platforms.AKL_platform_list[selected_idx]
        
        rom_obj = ROM()
        rom_obj.set_name(rom_name)
        rom_obj.set_platform(platform)
        if file_path:
            rom_obj.set_scanned_data_element("file", file_path)
    
        options = collections.OrderedDict()
        options["LAUNCH_DIRECTLY"] = kodi.translate(40952)
        for launcher in launchers:
            options[launcher] = launcher.get_name()
    
        s = kodi.translate(41106)
        selected_option = kodi.OrdDictionaryDialog().select(s, options)
        
        if selected_option == "LAUNCH_DIRECTLY":
            addon_id = "script.akl.defaults"
            addon = addons_repository.find_by_addon_id(addon_id, constants.AddonType.LAUNCHER)
            launcher = ROMLauncherAddonFactory.create(addon, None)
            launcher.set_settings({
                "name": f"Standalone File Launcher: {rom_name}",
                "application": file_path,
                "args": "",
                "secname": path.getBase()
            })
            launchers_repository.insert_launcher(launcher)
            selected_option = launcher
        
        rom_obj.add_launcher(selected_option, is_default=True)
        roms_repository.insert_rom(rom_obj)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_SOURCES_VIEW')
    kodi.notify(kodi.translate(41035).format(rom_name))
    kodi.refresh_container()


# -------------------------------------------------------------------------------------------------
# Source ROM management.
# -------------------------------------------------------------------------------------------------
# --- Submenu menu command ---
@AppMediator.register('SOURCE_MANAGE_ROMS')
def cmd_manage_source_roms(args):
    logger.debug('SOURCE_MANAGE_ROMS: cmd_manage_source_roms() SHOW MENU')
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    if source_id is None:
        logger.warning('cmd_manage_source_roms(): No source id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)

    options = collections.OrderedDict()
    options['SET_ROMS_ASSET_DIRS'] = kodi.translate(42045)
    options['SCAN_ROMS'] = kodi.translate(42046)
    options['SOURCE_IMPORT_ROMS'] = kodi.translate(42050)
    options['REMOVE_DEAD_ROMS'] = kodi.translate(42047)
    options['EXPORT_ROMS'] = kodi.translate(42051)
    options['SCRAPE_SOURCE_ROMS'] = kodi.translate(42052)
    options['DELETE_ROMS_NFO'] = kodi.translate(42053)
    options['CLEAR_SOURCE_ROMS'] = kodi.translate(42080)

    s = kodi.translate(41162).format(source.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('SOURCE_MANAGE_ROMS: cmd_manage_source_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args:
            del args['scraper_settings']
        AppMediator.async_cmd('EDIT_SOURCE', args)
        return
    
    logger.debug(f'SOURCE_MANAGE_ROMS: cmd_manage_source_roms() Selected {selected_option}')
    AppMediator.async_cmd(selected_option, args)


@AppMediator.register('SET_ROMS_ASSET_DIRS')
def cmd_set_rom_asset_dirs(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    list_items = collections.OrderedDict()
    assets = g_assetFactory.get_assets_for_type(constants.OBJ_ROM)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)
        
        root_path = source.get_assets_root_path()
        root_path_str = root_path.getPath() if root_path else kodi.translate(41158)
        
        gui_listitem = xbmcgui.ListItem(label=kodi.translate(42083), label2=root_path_str)
        gui_listitem.setArt({'icon': 'DefaultFolder.png'})
        list_items[AssetInfo()] = gui_listitem
        for asset_info in assets:
            path = source.get_asset_path(asset_info)
            if path:
                gui_listitem = xbmcgui.ListItem(label=kodi.translate(42084).format(asset_info.plural), label2=path.getPath())
                gui_listitem.setArt({'icon': 'DefaultFolder.png'})
                list_items[asset_info] = gui_listitem

        dialog = kodi.OrdDictionaryDialog()
        selected_asset: AssetInfo = dialog.select(kodi.translate(41129), list_items, use_details=True)

        if selected_asset is None:
            AppMediator.sync_cmd('SOURCE_MANAGE_ROMS', args)
            return

        # rootpath?
        if selected_asset.id == '':
            dir_path = kodi.browse(type=0, text=kodi.translate(41159), preselected_path=root_path.getPath() if root_path else None)
            if not dir_path or (root_path is not None and dir_path == root_path.getPath()):
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            
            root_path = io.FileName(dir_path)
            apply_to_all = kodi.dialog_yesno(kodi.translate(41062))
            source.set_assets_root_path(root_path, constants.ROM_ASSET_ID_LIST, create_default_subdirectories=apply_to_all)
        else:
            selected_asset_path = source.get_asset_path(selected_asset)
            dir_path = kodi.browse(type=0, text=kodi.translate(41160).format(selected_asset.plural),
                                   preselected_path=selected_asset_path.getPath())
            if not dir_path or dir_path == selected_asset_path.getPath():
                AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)
                return
            source.set_asset_path(selected_asset, dir_path)
            
        repository.update_source(source)
        uow.commit()
                
    # >> Check for duplicate paths and warn user.
    AppMediator.async_cmd('CHECK_DUPLICATE_ASSET_DIRS', args)

    kodi.notify(kodi.translate(40984).format(selected_asset.name, dir_path))
    AppMediator.sync_cmd('SET_ROMS_ASSET_DIRS', args)


@AppMediator.register('REMOVE_DEAD_ROMS')
def cmd_remove_dead_roms(args):
    # source_id: str = args['source_id'] if 'source_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('EXPORT_ROMS')
def cmd_export_roms(args):
    # source_id: str = args['source_id'] if 'source_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('DELETE_ROMS_NFO')
def cmd_delete_rom_nfos(args):
    # source_id: str = args['source_id'] if 'source_id' in args else None
    kodi.notify("Not implemented yet")


@AppMediator.register('CLEAR_SOURCE_ROMS')
def cmd_clear_source_roms(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        roms_repository = ROMsRepository(uow)
        
        source = source_repository.find(source_id)
        roms = roms_repository.find_roms_by_source(source)
        
        # If source is empty (no ROMs) do nothing
        num_roms = len([*roms])
        if num_roms == 0:
            kodi.dialog_OK(kodi.translate(41163))
            return

        # Confirm user wants to delete ROMs
        ret = kodi.dialog_yesno(kodi.translate(41164).format(source.get_name(), num_roms))
        if not ret:
            return

        # --- If there is a No-Intro XML DAT configured remove it ---
        # TODO fix
        # romcollection.reset_nointro_xmldata()
        
        collection_ids = source_repository.find_romcollection_ids_by_source(source_id)
        source_repository.remove_all_roms_in_source(source_id)
        uow.commit()
    
    AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
    for collection_id in collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
    kodi.notify(kodi.translate(41165))


# -------------------------------------------------------------------------------------------------
# Source Scanner executing
# -------------------------------------------------------------------------------------------------
@AppMediator.register('SCAN_ROMS')
def cmd_execute_rom_scanner(args):
    source_id: str = args['source_id'] if 'source_id' in args else None

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        sources_repository = SourcesRepository(uow)
        source = sources_repository.find(source_id)

    logger.info(f'SCAN_ROMS: scanner for source "{source.get_name()}"')
    kodi.notify(kodi.translate(40980))
    kodi.run_script(
        source.addon.get_addon_id(),
        source.get_scan_command())


def _get_name_from_platform(input, item_key, entity_data):
    title = entity_data['platform']
    return title


@AppMediator.register('SOURCE_IMPORT_ROMS')
def cmd_source_import_roms(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = SourcesRepository(uow)
        source = repository.find(source_id)

    options = collections.OrderedDict()
    options['SOURCE_IMPORT_ROMS_NFO'] = kodi.translate(42056)
    options['SOURCE_MPORT_ROMS_JSON'] = kodi.translate(42057)

    s = kodi.translate(41130).format(source.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('SOURCE_IMPORT_ROMS: Selected None. Closing context menu')
        AppMediator.async_cmd('SOURCE_MANAGE_ROMS', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug(f'SOURCE_IMPORT_ROMS: Selected {selected_option}')
    AppMediator.async_cmd(selected_option, args)


# --- Import ROM metadata from NFO files ---
@AppMediator.register('SOURCE_IMPORT_ROMS_NFO')
def cmd_import_roms_nfo(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
        
    # >> Load ROMs, iterate and import NFO files
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        src_repository = SourcesRepository(uow)
        
        source = src_repository.find(source_id)
        roms = repository.find_roms_by_source(source)
    
        pDialog = kodi.ProgressDialog()
        pDialog.startProgress(kodi.translate(41153), num_steps=len(roms))
        num_read_NFO_files = 0

        step = 0
        for rom in roms:
            step = step + 1
            nfo_filepath = rom.get_nfo_file()
            pDialog.updateProgress(step)
            if rom.update_with_nfo_file(nfo_filepath, verbose=False):
                num_read_NFO_files += 1
                repository.update_rom(rom)
                
        # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
        pDialog.updateProgress(len(roms), kodi.translate(41154))
        uow.commit()
        pDialog.close()
        
    kodi.notify(kodi.translate(40985).format(num_read_NFO_files))
    AppMediator.async_cmd('SOURCE_IMPORT_ROMS', args)


# --- Import ROM metadata from json config file ---
@AppMediator.register('IMPORT_ROMS_JSON')
def cmd_import_roms_json(args):
    source_id: str = args['source_id'] if 'source_id' in args else None
    file_list = kodi.browse(text=kodi.translate(41155), mask='.json', multiple=True)
    collection_ids = []

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMsRepository(uow)
        src_repository = SourcesRepository(uow)
        
        source = src_repository.find(source_id)
        collection_ids = src_repository.find_romcollection_ids_by_source(source_id)
        
        existing_roms = [*repository.find_roms_by_source(source)]
        existing_rom_ids = map(lambda r: r.get_id(), existing_roms)
        existing_rom_names = map(lambda r: r.get_name(), existing_roms)

        roms_to_insert: typing.List[ROM] = []
        roms_to_update: typing.List[ROM] = []

        # >> Process file by file
        for json_file in file_list:
            logger.debug(f'Importing "{json_file}"')
            import_FN = io.FileName(json_file)
            if not import_FN.exists():
                continue

            json_file_repository = ROMsJsonFileRepository(import_FN)
            imported_roms = json_file_repository.load_ROMs()
            logger.debug(f"Loaded {len(imported_roms)} roms")
    
            for imported_rom in imported_roms:
                if imported_rom.get_id() in existing_rom_ids:
                    # >> ROM exists (by id). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno(kodi.translate(41063).format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                elif imported_rom.get_name() in existing_rom_names:
                    # >> ROM exists (by name). Overwrite?
                    logger.debug('ROM found. Edit existing category.')
                    if kodi.dialog_yesno(kodi.translate(41063).format(imported_rom.get_name())):
                        roms_to_update.append(imported_rom)
                else:
                    logger.debug(f'Add new ROM {imported_rom.get_name()}')
                    imported_rom.set_platform(source.get_platform())
                    roms_to_insert.append(imported_rom)
                        
        for rom_to_insert in roms_to_insert:
            rom_to_insert.scanned_by(source.get_id())
            repository.insert_rom(rom_to_insert)

        for rom_to_update in roms_to_update:
            rom_to_update.scanned_by(source.get_id())
            repository.update_rom(rom_to_update)
            
        uow.commit()
        
    AppMediator.async_cmd('RENDER_SOURCE_VIEW', {'source_id': source_id})
    for collection_id in collection_ids:
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': collection_id})
    kodi.notify(kodi.translate(40978))
