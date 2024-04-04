# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (Precompiling the view data)
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
import typing
import time

from datetime import datetime
from datetime import timedelta
from datetime import date

from akl import constants, settings
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, CategoryRepository, ROMCollectionRepository, ROMsRepository
from resources.lib.repositories import SourcesRepository, ViewRepository

from resources.lib.domain import ROM, ROMCollection, Category, Source
from resources.lib.domain import VirtualCollectionFactory, VirtualCategoryFactory

logger = logging.getLogger(__name__)


@AppMediator.register('RENDER_VIEWS')
def cmd_render_views_data(args):
    kodi.notify(kodi.translate(40968))
    force = args['force'] if 'force' in args else False
    changed_since_date = args['changed_since_date'] if 'changed_since_date' in args else None
    if changed_since_date is None:
        changed_since_date = datetime.combine(datetime.today() - timedelta(days=7), datetime.min.time())
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        sources_repository = SourcesRepository(uow)
                
        _render_root_view(categories_repository, romcollections_repository, roms_repository,
                          sources_repository, views_repository, render_sub_views=True, force_rendering=force,
                          changed_since_date=changed_since_date)
    
        # backwards compatibility
        views_repository.cleanup_obsolete_views()
    
    kodi.notify(kodi.translate(40969))
    kodi.refresh_container()


@AppMediator.register('RENDER_CATEGORY_VIEW')
def cmd_render_view_data(args):
    if 'name' in args:
        render_selection = kodi.ListDialog().select(kodi.translate(40923), [
            kodi.translate(40893).format(args['name']),
            kodi.translate(40856)
        ])
        if render_selection is None:
            return
        if render_selection > 0:
            AppMediator.sync_cmd('RENDER_VIEWS', args)
            return
        
    kodi.notify(kodi.translate(40967))
    category_id = args['category_id'] if 'category_id' in args else None
    render_recursive = args['render_recursive'] if 'render_recursive' in args else False
    force = args['force'] if 'force' in args else False
    changed_since_date = args['changed_since_date'] if 'changed_since_date' in args else None
    if changed_since_date is None:
        changed_since_date = datetime.combine(datetime.today() - timedelta(days=7), datetime.min.time())
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        sources_repository = SourcesRepository(uow)
                
        if category_id is None or category_id == constants.VCATEGORY_ADDONROOT_ID:
            _render_root_view(categories_repository, romcollections_repository, roms_repository, sources_repository,
                              views_repository, render_recursive, force_rendering=force)
        else:
            category = categories_repository.find_category(category_id)
            _render_category_view(category, categories_repository, romcollections_repository, roms_repository,
                                  views_repository, render_recursive, force_rendering=force, changed_since_date=changed_since_date)
    
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    if do_notification:
        kodi.notify(kodi.translate(40966))
    kodi.refresh_container()


@AppMediator.register('RENDER_VIRTUAL_VIEWS')
def cmd_render_virtual_views(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        # cleanup first
        views_repository.cleanup_all_virtual_category_views()
                
        root_vcategory = VirtualCategoryFactory.create(constants.VCATEGORY_ROOT_ID)
        logger.debug('Processing root virtual category')
        _render_category_view(root_vcategory, categories_repository, romcollections_repository,
                              roms_repository, views_repository, True, force_rendering=True)

        for vcollection_id in constants.VCOLLECTIONS:
            vcollection = VirtualCollectionFactory.create(vcollection_id)
            logger.debug(f'Processing virtual collection "{vcollection.get_name()}"')
            collection_view_data = _render_romcollection_view(vcollection, roms_repository)
            views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)
        
        for vcategory_id in constants.VCATEGORIES:
            vcategory = VirtualCategoryFactory.create(vcategory_id)
                        
            if do_notification:
                kodi.notify(kodi.translate(40970).format(vcategory.get_name()))
            _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository)
   
    if do_notification:
        kodi.notify(kodi.translate(40965))
    kodi.refresh_container()


@AppMediator.register('RENDER_VCATEGORY_VIEWS')
def cmd_render_vcategories(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        # cleanup first
        views_repository.cleanup_all_virtual_category_views()
        
        for vcategory_id in constants.VCATEGORIES:
            vcategory = VirtualCategoryFactory.create(vcategory_id)

            if do_notification:
                kodi.notify(kodi.translate(40970).format(vcategory.get_name()))
            _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository,
                                  force_rendering=True)
        
            if do_notification:
                kodi.notify(kodi.translate(40971).format(vcategory.get_name()))
    kodi.refresh_container()

    
@AppMediator.register('RENDER_VCATEGORY_VIEW')
def cmd_render_vcategory(args):
    if 'name' in args:
        render_selection = kodi.ListDialog().select(kodi.translate(40923), [
            kodi.translate(40893).format(args['name']),
            kodi.translate(40856)
        ])
        if render_selection is None:
            return
        if render_selection > 0:
            AppMediator.sync_cmd('RENDER_VIEWS')
            return
        
    vcategory_id = args['vcategory_id'] if 'vcategory_id' in args else None
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        vcategory = VirtualCategoryFactory.create(vcategory_id)
        
        if vcategory is None:
            kodi.notify_warn(kodi.translate(40972).format(vcategory_id))
            return
        
        # cleanup first
        views_repository.cleanup_virtual_category_views(vcategory.get_id())
        
        if do_notification:
            kodi.notify(kodi.translate(40970).format(vcategory.get_name()))
        _render_category_view(vcategory, categories_repository, romcollections_repository, roms_repository, views_repository,
                              force_rendering=True)
    
        if do_notification:
            kodi.notify(kodi.translate(40971).format(vcategory.get_name()))
    kodi.refresh_container()


@AppMediator.register('RENDER_ROMCOLLECTION_VIEW')
def cmd_render_romcollection_view_data(args):
    if 'name' in args:
        render_selection = kodi.ListDialog().select(kodi.translate(40923), [
            kodi.translate(40893).format(args['name']),
            kodi.translate(40856)
        ])
        if render_selection is None:
            return
        if render_selection > 0:
            AppMediator.sync_cmd('RENDER_VIEWS', args)
            return
        
    romcollection_id = args['romcollection_id'] if 'romcollection_id' in args else None
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    if do_notification:
        kodi.notify(kodi.translate(40974))
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollections_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
             
        romcollection = romcollections_repository.find_romcollection(romcollection_id)
        collection_view_data = _render_romcollection_view(romcollection, roms_repository)
        views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)
    
    if do_notification:
        kodi.notify(kodi.translate(40966))
    kodi.refresh_container()


@AppMediator.register('RENDER_SOURCES_VIEW')
def cmd_render_sources_view_data(args):
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    if do_notification:
        kodi.notify(kodi.translate(41161))
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        sources_repository = SourcesRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
             
        sources = sources_repository.find_all()
        sources_view_data = _render_sources_view(sources, roms_repository)
        views_repository.store_sources_view(sources_view_data)
    
    if do_notification:
        kodi.notify(kodi.translate(40966))
    kodi.refresh_container()


@AppMediator.register('RENDER_SOURCE_VIEW')
def cmd_render_source_view_data(args):
    if 'name' in args:
        render_selection = kodi.ListDialog().select(kodi.translate(40923), [
            kodi.translate(40893).format(args['name']),
            kodi.translate(40856)
        ])
        if render_selection is None:
            return
        if render_selection > 0:
            AppMediator.sync_cmd('RENDER_VIEWS', args)
            return
     
    source_id = args['source_id'] if 'source_id' in args else None
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    if do_notification:
        kodi.notify(kodi.translate(41161))
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        source_repository = SourcesRepository(uow)
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
             
        source = source_repository.find(source_id)
        source_view_data = _render_source_view(source, roms_repository)
        views_repository.store_view(source.get_id(), source.get_type(), source_view_data)
    
    if do_notification:
        kodi.notify(kodi.translate(40966))
    kodi.refresh_container()


@AppMediator.register('RENDER_VCOLLECTION_VIEW')
def cmd_render_vcollection(args):
    if 'name' in args:
        render_selection = kodi.ListDialog().select(kodi.translate(40923), [
            kodi.translate(40893).format(args['name']),
            kodi.translate(40856)
        ])
        if render_selection is None:
            return
        if render_selection > 0:
            AppMediator.sync_cmd('RENDER_VIEWS', args)
            return
        
    vcollection_id = args['vcollection_id'] if 'vcollection_id' in args else None
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        vcollection = VirtualCollectionFactory.create(vcollection_id)
            
        if do_notification:
            kodi.notify(kodi.translate(40973).format(vcollection.get_name()))
        collection_view_data = _render_romcollection_view(vcollection, roms_repository)
        views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)
    
        if do_notification:
            kodi.notify(kodi.translate(40971).format(vcollection.get_name()))
    kodi.refresh_container()


@AppMediator.register('RENDER_ROM_VIEWS')
def cmd_render_rom_views(args):
    rom_id = args['rom_id'] if 'rom_id' in args else None
    do_notification = not settings.getSettingAsBool("display_hide_rendering_notifications")
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        roms_repository = ROMsRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        sources_repository = SourcesRepository(uow)
        categories_repository = CategoryRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)

        rom_obj = roms_repository.find_rom(rom_id)
        if do_notification:
            kodi.notify(kodi.translate(40975).format(rom_obj.get_rom_identifier()))
        
        source = sources_repository.find(rom_obj.get_scanned_by())
        if source is not None:
            source_view_data = _render_source_view(source, roms_repository)
            views_repository.store_view(source.get_id(), source.get_type(), source_view_data)

        romcollections = romcollections_repository.find_romcollections_by_rom(rom_id)
        for romcollection in romcollections:
            collection_view_data = _render_romcollection_view(romcollection, roms_repository)
            views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)
    
        for vcollection_id in constants.VCOLLECTIONS:
            vcollection = VirtualCollectionFactory.create(vcollection_id)
            collection_view_data = _render_romcollection_view(vcollection, roms_repository)
            views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)
    
        categories = categories_repository.find_categories_by_rom(rom_obj.get_id())
        for category in categories:
            collection_view_data = _render_category_view(category, categories_repository, romcollections_repository,
                                                         roms_repository, views_repository, render_sub_views=False,
                                                         force_rendering=True)
            views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)
    
    if do_notification:
        kodi.notify(kodi.translate(40964))
    kodi.refresh_container()
    

@AppMediator.register('CLEANUP_VIEWS')
def cmd_cleanup_views(args):
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        romcollections_repository = ROMCollectionRepository(uow)
        sources_repository = SourcesRepository(uow)
        views_repository = ViewRepository(globals.g_PATHS)
        
        categories = categories_repository.find_all_categories()
        romcollections = romcollections_repository.find_all_romcollections()
        sources = sources_repository.find_all()
        
        category_ids = list(c.get_id() for c in categories)
        romcollection_ids = list(r.get_id() for r in romcollections)
        source_ids = list(src.get_id() for src in sources)
       
        views_repository.cleanup_views(category_ids + romcollection_ids + source_ids)


def cmd_render_virtual_collection(vcategory_id: str, collection_value: str) -> dict:
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    viewdata = None
    with uow:
        roms_repository = ROMsRepository(uow)
        
        vcollection = VirtualCollectionFactory.create_by_category(vcategory_id, collection_value)
        viewdata = _render_romcollection_view(vcollection, roms_repository)
    return viewdata


# -------------------------------------------------------------------------------------------------
# Rendering of views (containers)
# -------------------------------------------------------------------------------------------------
def _render_root_view(categories_repository: CategoryRepository, romcollections_repository: ROMCollectionRepository,
                      roms_repository: ROMsRepository, sources_repository: SourcesRepository,
                      views_repository: ViewRepository, render_sub_views=False, force_rendering=False,
                      changed_since_date: datetime = None):
    
    root_categories = categories_repository.find_root_categories()
    root_romcollections = romcollections_repository.find_root_romcollections()
    sources = [*sources_repository.find_all()]
    root_roms = roms_repository.find_root_roms()

    root_data = {
        'id': constants.VCATEGORY_ADDONROOT_ID,
        'name': 'Root',
        'obj_type': constants.OBJ_CATEGORY,
        'items': []
    }
    root_items = []
    start = time.time()
    for root_category in root_categories:
        logger.debug(f'Processing category "{root_category.get_name()}"')
        rendered_item = _render_category_listitem(root_category)
        if rendered_item:
            root_items.append(rendered_item)
        if render_sub_views:
            _render_category_view(root_category, categories_repository, romcollections_repository,
                                  roms_repository, views_repository, render_sub_views, force_rendering,
                                  changed_since_date)
    end = time.time()
    logger.debug(f"Rendered all categories in {end - start}ms")
    
    start = time.time()
    for root_romcollection in root_romcollections:
        logger.debug(f'Processing romcollection "{root_romcollection.get_name()}"')
        rendered_item = _render_romcollection_listitem(root_romcollection)
        if rendered_item:
            root_items.append(rendered_item)
        if render_sub_views:
            collection_view_data = _render_romcollection_view(root_romcollection, roms_repository)
            views_repository.store_view(root_romcollection.get_id(), root_romcollection.get_type(), collection_view_data)
    end = time.time()
    logger.debug(f"Rendered all romcollections in {end - start}ms")
    
    if render_sub_views:
        logger.debug('Processing sources')
        sources_view_data = _render_sources_view(sources, roms_repository)
        views_repository.store_sources_view(sources_view_data)
        
        start = time.time()
        for source in sources:
            logger.debug(f'Processing source "{source.get_name()}"')
            source_view_data = _render_source_view(source, roms_repository)
            views_repository.store_view(source.get_id(), source.get_type(), source_view_data)
        end = time.time()
        logger.debug(f"Rendered sources in {end - start}ms")
        
    for rom in root_roms:
        try:
            root_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM '{rom.get_name()}'")

    root_vcategory = VirtualCategoryFactory.create(constants.VCATEGORY_ROOT_ID)
    logger.debug('Processing root virtual category')
    start = time.time()
    rendered_item = _render_category_listitem(root_vcategory)
    if rendered_item:
        root_items.append(rendered_item)
    if render_sub_views:
        _render_category_view(root_vcategory, categories_repository, romcollections_repository,
                              roms_repository, views_repository, render_sub_views, force_rendering=force_rendering,
                              changed_since_date=changed_since_date)
    end = time.time()
    logger.debug(f"Rendered virtual categories in {end - start}ms")
    
    start = time.time()
    for vcollection_id in constants.VCOLLECTIONS:
        vcollection = VirtualCollectionFactory.create(vcollection_id)
        logger.debug(f'Processing virtual collection "{vcollection.get_name()}"')
        rendered_item = _render_romcollection_listitem(vcollection)
        if rendered_item:
            root_items.append(rendered_item)
        collection_view_data = _render_romcollection_view(vcollection, roms_repository)
        views_repository.store_view(vcollection.get_id(), vcollection.get_type(), collection_view_data)
    end = time.time()
    logger.debug(f"Rendered virtual collections in {end - start}ms")
    
    logger.debug(f'Storing {len(root_items)} items in root view.')
    root_data['items'] = root_items
    views_repository.store_root_view(root_data)


def _render_category_view(category_obj: Category, categories_repository: CategoryRepository,
                          romcollections_repository: ROMCollectionRepository, roms_repository: ROMsRepository,
                          views_repository: ViewRepository, render_sub_views=False, force_rendering=False,
                          changed_since_date: datetime = None):
    if changed_since_date is None:
        changed_since_date = datetime.combine(datetime.today() - timedelta(days=7), datetime.min.time())
                                                       
    start = time.time()
    sub_categories = categories_repository.find_categories_by_parent(category_obj.get_id())
    romcollections = romcollections_repository.find_romcollections_by_parent(category_obj.get_id())
    
    view_data = {
        'id': category_obj.get_id(),
        'parent_id': category_obj.get_parent_id(),
        'name': category_obj.get_name(),
        'obj_type': category_obj.get_type(),
        'items': []
    }
    view_items = []
    for sub_category in sub_categories:
        if sub_category is None:
            continue
        logger.debug(f'Processing category "{sub_category.get_name()}", part of "{category_obj.get_name()}"')
        rendered_item = _render_category_listitem(sub_category)
        if rendered_item:
            view_items.append(rendered_item)
        if render_sub_views:
            _render_category_view(sub_category, categories_repository, romcollections_repository, roms_repository,
                                  views_repository, render_sub_views)
    
    for romcollection in romcollections:
        logger.debug(f"Processing romcollection '{romcollection.get_name()}'")
        if not force_rendering and romcollection.get_last_change_timestamp() < changed_since_date:
            logger.debug(f"Processed romcollection {romcollection.get_name()}. Skipped generation due to no new changes.")
            continue
         
        try:
            rendered_item = _render_romcollection_listitem(romcollection)
            if rendered_item:
                view_items.append(rendered_item)
        except Exception:
            logger.exception(f"Exception while rendering list item ROM Collection '{romcollection.get_name()}'")
            kodi.notify_error(kodi.translate(40976).format(romcollection.get_name()))
        if render_sub_views and not category_obj.get_type() == constants.OBJ_CATEGORY_VIRTUAL:
            collection_view_data = _render_romcollection_view(romcollection, roms_repository)
            views_repository.store_view(romcollection.get_id(), romcollection.get_type(), collection_view_data)

    if not force_rendering and category_obj.get_last_change_timestamp() < changed_since_date:
        logger.debug(f"Processed category {category_obj.get_name()}. Skipped generation due to no new changes.")
        return

    roms = roms_repository.find_roms_by_category(category_obj)
    for rom in roms:
        try:
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM '{rom.get_name()}'")
                  
    logger.debug(f'Storing {len(view_items)} items for category "{category_obj.get_name()}" view.')
    view_data['items'] = view_items
    views_repository.store_view(category_obj.get_id(), category_obj.get_type(), view_data)
    end = time.time()
    logger.debug(f"Processed category {category_obj.get_name()} in {end - start}ms")


def _render_romcollection_view(romcollection_obj: ROMCollection, roms_repository: ROMsRepository) -> dict:
    start = time.time()
    roms = roms_repository.find_roms_by_romcollection(romcollection_obj)
    view_data = {
        'id': romcollection_obj.get_id(),
        'parent_id': romcollection_obj.get_parent_id(),
        'name': romcollection_obj.get_name(),
        'properties': {
            'platform': romcollection_obj.get_platform(),
            'boxsize': romcollection_obj.get_box_sizing()
        },
        'obj_type': romcollection_obj.get_type(),
        'items': []
    }
    view_items = []
    for rom in roms:
        try:
            rom.apply_romcollection_asset_mapping(romcollection_obj)
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f'Exception while rendering list item ROM "{rom.get_name()}"')
        
    logger.debug(f'Found {len(view_items)} items for romcollection "{romcollection_obj.get_name()}" view.')
    view_data['items'] = view_items
    
    end = time.time()
    logger.debug(f"Processed collection {romcollection_obj.get_name()} in {end - start}ms")
    return view_data


def _render_sources_view(sources: typing.List[Source], roms_repository: ROMsRepository) -> dict:
    standalone_roms = roms_repository.find_standalone_roms()
    view_data = {
        'id': '',
        'name': kodi.translate(constants.OBJ_SOURCE),
        'obj_type': constants.OBJ_SOURCE,
        'items': []
    }
    view_items = []
    
    listitem_fanart = globals.g_PATHS.FANART_FILE_PATH.getPath()

    for source in sources:
        listitem_name = source.get_name()
        view_items.append({
            'id': source.get_id(),
            'name': listitem_name,
            'url': globals.router.url_for_path(f'source/{source.get_id()}'),
            'is_folder': True,
            'type': 'video',
            'info': {
                'title': listitem_name,
                'plot': f'Source of type {source.addon.get_addon_type()}',
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
        
    for rom in standalone_roms:
        try:
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f"Exception while rendering list item ROM '{rom.get_name()}'")
    
    logger.debug(f'Storing {len(view_items)} items for Sources view.')
    view_data['items'] = view_items
    return view_data
         

def _render_source_view(source: Source, roms_repository: ROMsRepository) -> dict:
    roms = roms_repository.find_roms_by_source(source)
    view_data = {
        'id': source.get_id(),
        'name': source.get_name(),
        'properties': {
            'boxsize': source.get_box_sizing()
        },
        'obj_type': source.get_type(),
        'items': []
    }
    view_items = []
    for rom in roms:
        try:
            view_items.append(render_rom_listitem(rom))
        except Exception:
            logger.exception(f'Exception while rendering list item ROM "{rom.get_name()}"')
        
    logger.debug(f'Found {len(view_items)} items for source "{source.get_name()}" view.')
    view_data['items'] = view_items
    return view_data


# -------------------------------------------------------------------------------------------------
# Rendering of list items per view
# -------------------------------------------------------------------------------------------------
def _render_category_listitem(category_obj: Category) -> dict:
    # --- Do not render row if category finished ---
    if category_obj.is_finished() and \
            (category_obj.get_type() in constants.OBJ_VIRTUAL_TYPES or settings.getSettingAsBool('display_hide_finished')):
        return None

    category_name = category_obj.get_name()
    ICON_OVERLAY = 5 if category_obj.is_finished() else 4
    assets = category_obj.get_view_assets()

    url_prefix = 'category'
    if category_obj.get_type() == constants.OBJ_CATEGORY_VIRTUAL:
        url_prefix = 'category/virtual'
        
    return {
        'id': category_obj.get_id(),
        'name': category_name,
        'url': globals.router.url_for_path('{}/{}'.format(url_prefix, category_obj.get_id())),
        'is_folder': True,
        'type': 'video',
        'info': {
            'title': category_name,
            'year': category_obj.get_releaseyear(),
            'genre': category_obj.get_genre(),
            'studio': category_obj.get_developer(),
            'rating': category_obj.get_rating(),
            'plot': category_obj.get_plot(),
            'trailer': category_obj.get_trailer(),
            'overlay': ICON_OVERLAY
        },
        'art': assets,
        'properties': {
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_CATEGORY,
            'obj_type': category_obj.get_type(),
            'num_romcollections': category_obj.num_romcollections()
        }
    }


def _render_romcollection_listitem(romcollection_obj: ROMCollection) -> dict:
    # --- Do not render row if romcollection finished ---
    if romcollection_obj.is_finished() and \
            (romcollection_obj.get_type() in constants.OBJ_VIRTUAL_TYPES or \
             settings.getSettingAsBool('display_hide_finished')):
        return None

    romcollection_name = romcollection_obj.get_name()
    ICON_OVERLAY = 5 if romcollection_obj.is_finished() else 4
    assets = romcollection_obj.get_view_assets()
    
    if romcollection_obj.get_type() == constants.OBJ_COLLECTION_VIRTUAL:
        if romcollection_obj.get_parent_id() is None:
            url = globals.router.url_for_path(f'collection/virtual/{romcollection_obj.get_id()}')
        else:
            collection_value = romcollection_obj.get_custom_attribute("collection_value")
            url = globals.router.url_for_path(f'collection/virtual/{romcollection_obj.get_parent_id()}/items?value={collection_value}')
    else:
        url = globals.router.url_for_path(f'collection/{romcollection_obj.get_id()}')

    return { 
        'id': romcollection_obj.get_id(),
        'name': romcollection_name,
        'url': url,
        'is_folder': True,
        'type': 'video',
        'info': {
            'title': romcollection_name,
            'year': romcollection_obj.get_releaseyear(),
            'genre': romcollection_obj.get_genre(),
            'studio': romcollection_obj.get_developer(),
            'rating': romcollection_obj.get_rating(),
            'plot': romcollection_obj.get_plot(),
            'trailer': romcollection_obj.get_trailer(),
            'overlay': ICON_OVERLAY
        },
        'art': assets,
        'properties': {
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_ROMCOLLECTION,
            'platform': romcollection_obj.get_platform(),
            'boxsize': romcollection_obj.get_box_sizing(),
            'obj_type': romcollection_obj.get_type()
        }
    }

    # --- AKL Collections special category ---
    #if not settings.getSettingAsBool('display_hide_collections'): render_vcategory_collections_row()
    # --- AKL Virtual Categories ---
    #if not settings.getSettingAsBool('display_hide_vlaunchers'): render_vcategory_Browse_by_row()
    # --- Browse Offline Scraper database ---
    #if not settings.getSettingAsBool('display_hide_AKL_scraper'): render_vcategory_AKL_offline_scraper_row()
    #if not settings.getSettingAsBool('display_hide_LB_scraper'):  render_vcategory_LB_offline_scraper_row()


def render_rom_listitem(rom_obj: ROM) -> dict:
    # --- Do not render row if romcollection finished ---
    if rom_obj.is_finished() and settings.getSettingAsBool('display_hide_finished'):
        return

    ICON_OVERLAY = 5 if rom_obj.is_finished() else 4
    assets = rom_obj.get_view_assets()

    # --- Default values for flags ---
    AKL_InFav_bool_value = constants.AKL_INFAV_BOOL_VALUE_FALSE
    AKL_MultiDisc_bool_value = constants.AKL_MULTIDISC_BOOL_VALUE_FALSE
    AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_NONE
    AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_NONE
    AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_NONE

    rom_status = rom_obj.get_rom_status()
    if rom_status == 'OK':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_OK
    elif rom_status == 'Unlinked ROM':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_UNLINKED_ROM
    elif rom_status == 'Unlinked Launcher':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
    elif rom_status == 'Broken':
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_BROKEN
    else:
        AKL_Fav_stat_value = constants.AKL_FAV_STAT_VALUE_NONE

    # --- NoIntro status flag ---
    nstat = rom_obj.get_nointro_status()
    if nstat == constants.AUDIT_STATUS_HAVE:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_HAVE
    elif nstat == constants.AUDIT_STATUS_MISS:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_MISS
    elif nstat == constants.AUDIT_STATUS_UNKNOWN:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_UNKNOWN
    elif nstat == constants.AUDIT_STATUS_NONE:
        AKL_NoIntro_stat_value = constants.AKL_NOINTRO_STAT_VALUE_NONE

    # --- Mark clone ROMs ---
    pclone_status = rom_obj.get_pclone_status()
    if pclone_status == constants.PCLONE_STATUS_PARENT:
        AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_PARENT
    elif pclone_status == constants.PCLONE_STATUS_CLONE:
        AKL_PClone_stat_value = constants.AKL_PCLONE_STAT_VALUE_CLONE
    
    rom_in_fav = rom_obj.is_favourite()
    if rom_in_fav:
        AKL_InFav_bool_value = constants.AKL_INFAV_BOOL_VALUE_TRUE

    # --- Set common flags to all launchers---
    if rom_obj.has_multiple_disks():
        AKL_MultiDisc_bool_value = constants.AKL_MULTIDISC_BOOL_VALUE_TRUE

    list_name = rom_obj.get_name()
    sub_label = rom_obj.get_rom_identifier()
    if list_name is None or list_name == '':
        list_name = sub_label
    if list_name == sub_label:
        sub_label = None

    if settings.getSettingAsBool("display_execute_rom_by_default"):
        item_url = globals.router.url_for_path(f'execute/rom/{rom_obj.get_id()}')
    else:
        item_url = globals.router.url_for_path(f'rom/view/{rom_obj.get_id()}')

    return {
        'id': rom_obj.get_id(),
        'name': list_name,
        'name2': sub_label,
        'url': item_url,
        'is_folder': False,
        'type': 'video',
        'info': {
            'title': rom_obj.get_name(),
            'year': rom_obj.get_releaseyear(),
            'genre': rom_obj.get_genre(),
            'studio': rom_obj.get_developer(),
            'rating': rom_obj.get_rating(),
            'plot': rom_obj.get_plot(),
            'trailer': rom_obj.get_trailer(),
            'overlay': ICON_OVERLAY
        },
        'art': assets,
        'properties': {
            'entityid': rom_obj.get_id(),
            'identifier': rom_obj.get_rom_identifier(),
            'platform': rom_obj.get_platform(),
            'nplayers': rom_obj.get_number_of_players(),
            'nplayers_online': rom_obj.get_number_of_players_online(),
            'esrb': rom_obj.get_esrb_rating(),
            'pegi': rom_obj.get_pegi_rating(),
            'boxsize': rom_obj.get_box_sizing(),
            'tags': ','.join(rom_obj.get_tags()),
            'obj_type': constants.OBJ_ROM,
            # --- ROM flags (Skins will use these flags to render icons) ---
            constants.AKL_CONTENT_LABEL: constants.AKL_CONTENT_VALUE_ROM,
            constants.AKL_INFAV_BOOL_LABEL: AKL_InFav_bool_value,
            constants.AKL_MULTIDISC_BOOL_LABEL: AKL_MultiDisc_bool_value,
            constants.AKL_FAV_STAT_LABEL: AKL_Fav_stat_value,
            constants.AKL_NOINTRO_STAT_LABEL: AKL_NoIntro_stat_value,
            constants.AKL_PCLONE_STAT_LABEL: AKL_PClone_stat_value
        }
    }
