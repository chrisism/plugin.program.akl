# -*- coding: utf-8 -*-
import logging
import typing

import json
import datetime
from distutils.version import LooseVersion

import sqlite3
from sqlite3.dbapi2 import Cursor

from akl.utils import text, io, kodi
from akl import constants

from resources.lib import globals
from resources.lib import queries as qry
from resources.lib.domain import MetaDataItemABC, Category, ROMCollection, ROM, VirtualCollection, RuleSet, Rule
from resources.lib.domain import Asset, AssetPath, AssetMapping, RomAssetMapping
from resources.lib.domain import VirtualCategoryFactory, VirtualCollectionFactory, ROMLauncherAddonFactory, g_assetFactory
from resources.lib.domain import Source, ROMLauncherAddon, AklAddon


# #################################################################################################
# #################################################################################################
# Data storage objects.
# #################################################################################################
# #################################################################################################
#
# * Repository class for creating and retrieveing Container/Categories/Launchers/ROM Collection objects.
#

#
# ViewRepository works with json files that contain pre-generated data
# to be shown in list containers.
#
class ViewRepository(object):

    def __init__(self, paths: globals.AKL_Paths):
        self.paths = paths
        self.logger = logging.getLogger(__name__)

    def find_root_items(self):
        repository_file = self.paths.ROOT_PATH
        self.logger.debug(f'find_root_items(): Loading path data from file {repository_file.getPath()}')
        if not repository_file.exists():
            self.logger.debug(f'find_root_items(): Path does not exist {repository_file.getPath()}')
            return None

        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            self.logger.error('find_root_items(): ValueError exception in file.readJson() function', exc_info=ex)
            self.logger.error('find_root_items(): Dir  {}'.format(repository_file.getPath()))
            self.logger.error('find_root_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def find_sources_items(self):
        repository_file = self.paths.SOURCES_VIEW_PATH
        self.logger.debug(f'find_sources_items(): Loading path data from file {repository_file.getPath()}')
        if not repository_file.exists():
            self.logger.debug(f'find_sources_items(): Path does not exist {repository_file.getPath()}')
            return None

        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            self.logger.error('find_sources_items(): ValueError exception in file.readJson() function', exc_info=ex)
            self.logger.error('find_sources_items(): Dir  {}'.format(repository_file.getPath()))
            self.logger.error('find_sources_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data

    def find_items(self, view_id, obj_type: int) -> typing.Any:
        
        repository_file = self._assemble_view_file_name(view_id, obj_type)
        self.logger.debug('find_items(): Loading path data from file {}'.format(repository_file.getPath()))
        try:
            item_data = repository_file.readJson()
        except ValueError as ex:
            statinfo = repository_file.stat()
            self.logger.error('find_items(): ValueError exception in file.readJson() function', exc_info=ex)
            self.logger.error('find_items(): Dir  {}'.format(repository_file.getPath()))
            self.logger.error('find_items(): Size {}'.format(statinfo.st_size))
            return None
        
        return item_data
    
    def store_root_view(self, view_data):
        repository_file = self.paths.ROOT_PATH
        self.logger.debug(f'store_root_view(): Storing data in file {repository_file.getPath()}')
        repository_file.writeJson(view_data)

    def store_sources_view(self, view_data):
        repository_file = self.paths.SOURCES_VIEW_PATH
        self.logger.debug(f'store_sources_view(): Storing data in file {repository_file.getPath()}')
        repository_file.writeJson(view_data)

    def store_view(self, view_id: str, object_type: int, view_data):        
        repository_file = self._assemble_view_file_name(view_id, object_type)
        if view_data is None:
            if repository_file.exists():
                self.logger.debug(f'store_view(): No data for file {repository_file.getPath()}. Removing file')
                repository_file.unlink()
            return

        self.logger.debug(f'store_view(): Storing data in file {repository_file.getPath()}')
        repository_file.writeJson(view_data)

    def cleanup_views(self, view_ids_to_keep: typing.List[str]):
        view_files = self.paths.VIEWS_DIR.scanFilesInPath('*.json')
        for view_file in view_files:
            view_id = view_file.getBaseNoExt().replace('collection_', '').replace('category_', '').replace('source_', '')
            if view_id not in view_ids_to_keep:
                self.logger.info(f'Removing file for view "{view_id}"')
                view_file.unlink()

    def cleanup_obsolete_views(self):
        view_files = self.paths.VIEWS_DIR.scanFilesInPath('view*.json')
        for view_file in view_files:
            self.logger.info(f'Removing file: "{view_file}"')
            view_file.unlink()

    def cleanup_virtual_category_views(self, view_id):
        view_files = self.paths.GENERATED_VIEWS_DIR.scanFilesInPath(f'category_{view_id}_*.json')
        self.logger.info(f'Removing {len(view_files)} files for virtual category "{view_id}"')
        for view_file in view_files:
            view_file.unlink()
 
    def cleanup_all_virtual_category_views(self):
        view_files = self.paths.GENERATED_VIEWS_DIR.scanFilesInPath('category_*.json')
        self.logger.info(f'Removing {len(view_files)} files for all virtual categories')
        for view_file in view_files:
            view_file.unlink()
            
    def _assemble_view_file_name(self, view_id, obj_type):
        
        if obj_type == constants.OBJ_CATEGORY:
            return self.paths.VIEWS_DIR.pjoin(f'category_{view_id}.json')
        elif obj_type == constants.OBJ_ROMCOLLECTION:
            return self.paths.VIEWS_DIR.pjoin(f'collection_{view_id}.json')
        elif obj_type == constants.OBJ_SOURCE:
            return self.paths.VIEWS_DIR.pjoin(f'source_{view_id}.json')
        elif obj_type == constants.OBJ_CATEGORY_VIRTUAL:
            return self.paths.GENERATED_VIEWS_DIR.pjoin(f'category_{view_id}.json')
        elif obj_type == constants.OBJ_COLLECTION_VIRTUAL:
            return self.paths.GENERATED_VIEWS_DIR.pjoin(f'collection_{view_id}.json')
        
        return self.paths.VIEWS_DIR.pjoin(f'view_{view_id}.json')
    
        
#
# XmlConfigurationRepository works with original XML configuration files, which contained the 
# categories and launchers. This repository is to read these files and migrate to current solution.
#
class XmlConfigurationRepository(object):

    def __init__(self, file_path: io.FileName, debug=False):
        self.file_path = file_path
        self.debug = debug
        self.logger = logging.getLogger(__name__)

    def get_categories(self) -> typing.Iterator[Category]:
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
        self.logger.debug('XmlRepository.get_categories() Loading {0}'.format(self.file_path.getPath()))

        xml_root = self.file_path.readXml()
        if xml_root is None:
            return None

        # >> Process tags in XML configuration file
        for root_element in xml_root:
            if self.debug: 
                self.logger.debug('>>> Root child tag <{0}>'.format(root_element.tag))

            if not root_element.tag == 'category':
                continue

            assets = []
            category_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: 
                    self.logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                category_temp[xml_tag] = text_XML_line
                                
                if xml_tag.startswith('s_'):
                    asset_info = g_assetFactory.get_asset_info(xml_tag[2:])
                    asset_data = { 'filepath': text_XML_line, 'asset_type': asset_info.id }
                    assets.append(Asset(asset_data))
                
            # --- Add category to categories dictionary ---
            self.logger.debug('Adding category "{0}" to import list'.format(category_temp['m_name']))
            yield Category(category_temp, assets)

    def get_launchers(self) -> typing.Iterator[ROMCollection]:    
        # --- Parse using cElementTree ---
        # >> If there are issues in the XML file (for example, invalid XML chars) ET.parse will fail
        self.logger.debug('XmlRepository.get_launchers() Loading {0}'.format(self.file_path.getPath()))

        xml_root = self.file_path.readXml()
        if xml_root is None:
            return None
            
        # >> Process tags in XML configuration file
        for root_element in xml_root:
            if self.debug: 
                self.logger.debug('>>> Root child tag <{0}>'.format(root_element.tag))

            if not root_element.tag == 'launcher':
                continue
            
            assets = []
            asset_paths = []
            launcher_temp = {}
            for root_child in root_element:
                # >> By default read strings
                text_XML_line = root_child.text if root_child.text is not None else ''
                text_XML_line = text.unescape_XML(text_XML_line)
                xml_tag  = root_child.tag
                if self.debug: 
                    self.logger.debug('>>> "{0:<11s}" --> "{1}"'.format(xml_tag, text_XML_line))
                if xml_tag == 'categoryID': xml_tag = 'parent_id'                
                launcher_temp[xml_tag] = text_XML_line
                
                if xml_tag.startswith('s_'):
                    asset_info = g_assetFactory.get_asset_info(xml_tag[2:])
                    asset_data = { 'filepath': text_XML_line, 'asset_type': asset_info.id }
                    assets.append(Asset(asset_data))
                    
                if xml_tag.startswith('path_'):
                    asset_info = g_assetFactory.get_asset_info_by_pathkey(xml_tag)
                    asset_path_data = { 'path': text_XML_line, 'asset_type': asset_info.id }
                    asset_paths.append(AssetPath(asset_path_data))
                    
            # --- Add launcher to launchers collection ---
            self.logger.debug('Adding launcher "{0}" to import list'.format(launcher_temp['m_name']))
            yield ROMCollection(launcher_temp, assets, asset_paths, [], [])


# -------------------------------------------------------------------------------------------------
# --- Repository class for ROM set objects of Standard ROM Launchers (legacy json files) ---
# Arranges retrieving and storing of roms belonging to a particular standard ROM launcher.
#
# NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
#      a dictionary. Convert the Collection list into an ordered dictionary and then
#      converted back the ordered dictionary into a list before saving the collection.
# -------------------------------------------------------------------------------------------------
class ROMsJsonFileRepository(object):

    def __init__(self, file_path: io.FileName, debug=False):
        self.file_path = file_path
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
    #
    # Loads ROM databases from disk
    #
    def load_ROMs(self) -> typing.List[ROM]:
        self.logger.debug('ROMsJsonFileRepository::load_ROMs() Starting ...')
        if not self.file_path.exists():
            self.logger.warning('Launcher JSON not found "{0}"'.format(self.file_path.getPath()))
            return []

        roms_data = []
        # --- Parse using json module ---
        # >> On Github issue #8 a user had an empty JSON file for ROMs. This raises
        #    exception exceptions.ValueError and launcher cannot be deleted. Deal
        #    with this exception so at least launcher can be rescanned.
        self.logger.debug('ROMsJsonFileRepository.find_by_launcher(): Loading roms from file {0}'.format(self.file_path.getPath()))
        try:
            roms_data = self.file_path.readJson()
        except ValueError:
            statinfo = self.file_path.stat()
            self.logger.error('ROMsJsonFileRepository.find_by_launcher(): ValueError exception in json.load() function')
            self.logger.error('ROMsJsonFileRepository.find_by_launcher(): Dir  {0}'.format(self.file_path.getPath()))
            self.logger.error('ROMsJsonFileRepository.find_by_launcher(): Size {0}'.format(statinfo.st_size))
            return None

        # --- Extract roms from JSON data structure and ensure version is correct ---
        if roms_data and isinstance(roms_data, list) and 'control' in roms_data[0]:
            control_str = roms_data[0]['control']
            version_int = roms_data[0]['version']
            roms_data = roms_data[1]

        roms = []
        if isinstance(roms_data, list):
            for rom_data in roms_data:
                assets = self._get_assets_from_romdata(rom_data)
                compatible_rom_data = self._alter_dictionary_for_compatibility(rom_data)
                scanned_data = self._get_scanned_data_from_romdata(rom_data)
                r = ROM(rom_data, assets, scanned_data=scanned_data)
                key = r.get_id()
                roms.append(r)
        else:
            for key in roms_data:
                assets = self._get_assets_from_romdata(roms_data[key])
                compatible_rom_data = self._alter_dictionary_for_compatibility(roms_data[key])
                scanned_data = self._get_scanned_data_from_romdata(roms_data[key])
                r = ROM(compatible_rom_data, assets, scanned_data=scanned_data)
                roms.append(r)

        return roms
    
    def _get_assets_from_romdata(self, rom_data: dict) -> typing.List[Asset]:
        assets = []
        for key, value in rom_data.items():
            if key.startswith('s_'):
                asset_info = g_assetFactory.get_asset_info(key[2:])
                asset_data = { 'filepath': value, 'asset_type': asset_info.id }
                assets.append(Asset(asset_data))
        return assets

    def _get_scanned_data_from_romdata(self, rom_data: dict) -> dict:
        scanned_data = { 'file': rom_data['filepath'] }
        return scanned_data
 
    def _alter_dictionary_for_compatibility(self, rom_data: dict) -> dict:
        rom_data['rom_status'] = rom_data['fav_status'] if 'fav_status' in rom_data else None
        return rom_data


#
# UnitOfWork to be used with sqlite repositories.
# Can be used to create database scopes/sessions (unit of work pattern).
#
class UnitOfWork(object):
    VERBOSE = False

    def __init__(self, db_path: io.FileName):
        self._db_path = db_path
        self._commit = False
        self.logger = logging.getLogger(__name__)
    
    def check_database(self) -> bool:
        if not self._db_path.exists():
            self.logger.warning("UnitOfWork.check_database(): Database '%s' missing" % self._db_path)
            return False

        self.open_session()
        self.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.result_set()

        if not len(tables) or len(tables) == 0:
            self.logger.warning("UnitOfWork.check_database(): Database: '%s' no tables" % self._db_path)
            self.close_session()
            return False
        
        self.close_session()
        return len(tables) > 1

    def get_database_version(self) -> str:
        self.open_session()
        
        self.execute(f"SELECT version FROM akl_version WHERE app='{globals.addon_id}';")
        sql_version = self.single_result()
        
        db_version = sql_version['version'] if sql_version else None
        
        self.close_session()
        return db_version

    def create_empty_database(self, schema_file_path: io.FileName):
        self.open_session()
        
        sql_statements = schema_file_path.loadFileToStr()
        self.execute_script(sql_statements)
        self.conn.execute("INSERT INTO akl_version VALUES(?, ?)", [globals.addon_id, globals.addon_version])

        self.commit()
        self.close_session()
        
    def reset_database(self, schema_file_path: io.FileName):
        if self._db_path.exists():
            self._db_path.unlink()
        
        # cleanup collection json files
        if globals.g_PATHS.VIEWS_DIR.exists():
            collection_files = globals.g_PATHS.VIEWS_DIR.scanFilesInPath("view_*.json")
            for collection_file in collection_files:
                collection_file.unlink()
                
        # cleanup root file
        if globals.g_PATHS.ROOT_PATH.exists():
            globals.g_PATHS.ROOT_PATH.unlink()
            
        self.create_empty_database(schema_file_path)

    def migrate_database(self, migration_files: typing.List[io.FileName], new_db_version, skip_scripts_execution=False):
        if not skip_scripts_execution:
            # make copy of existing database file to execute migration on.
            temp_filepath = self._db_path.changeExtension(f".{new_db_version}.db")
            backup_filepath = self._db_path.changeExtension(".db.bak")
            if temp_filepath.exists():
                temp_filepath.unlink()
            else:
                if backup_filepath.exists():
                    backup_filepath.unlink()
                self._db_path.copy(backup_filepath)
            self._db_path.copy(temp_filepath)
        else:
            temp_filepath = self._db_path
            
        check_version = LooseVersion("1.3.99")
        any_failed = False
        for migration_file in migration_files:
            self.logger.info(f'Executing migration script: {migration_file.getPath()}')
            file_version = self.get_version_from_migration_file(migration_file)
            sql_statements = migration_file.loadFileToStr()
            failed = False

            self.open_session(temp_filepath)
            try:
                if not skip_scripts_execution:
                    self.execute_script(sql_statements)
                self.commit()
            except Exception:
                self.logger.exception(f"Failure with database migration '{migration_file.getBase()}'")
                kodi.notify_error(kodi.translate(40954))
                failed = True
                any_failed = True
                self.rollback()
            finally:
                self.close_session()

            if file_version > check_version:
                self.execute_single_session(temp_filepath, qry.AKL_INSERT_MIGRATION, [
                    migration_file.getBase(), str(new_db_version),
                    datetime.datetime.now(), not failed])

        self.logger.info(f'Updating database schema version of app {globals.addon_id} to {new_db_version}')
        self.execute_single_session(temp_filepath, qry.AKL_UPDATE_VERSION, [
            str(new_db_version), globals.addon_id])

        # restore file after migrations
        if not skip_scripts_execution:
            self._db_path.unlink()
            temp_filepath.copy(self._db_path)
            if not any_failed:
                temp_filepath.unlink()

    def get_migrations_history(self):
        self.open_session()
        
        migrations_data_set = []
        try:
            self.execute(qry.AKL_SELECT_MIGRATIONS)
            migrations_data_set = self.result_set()
        except Exception:
            self.logger.error("Failure getting executed migrations")
        finally:
            self.close_session()
        return migrations_data_set

    def get_migration_files(self, db_version):
        if not globals.g_PATHS.DATABASE_MIGRATIONS_PATH.exists():
            globals.g_PATHS.DATABASE_MIGRATIONS_PATH.makedirs()
            
        migrations_files_available = globals.g_PATHS.DATABASE_MIGRATIONS_PATH.scanFilesInPath("*.sql")
        migrations_files_to_execute = []
        for migration_file in migrations_files_available:
            file_version = self.get_version_from_migration_file(migration_file)
            if file_version > db_version:
                migrations_files_to_execute.append(migration_file)

        migrations_files_to_execute.sort(key=lambda f: f.getBaseNoExt())
        return migrations_files_to_execute

    def get_version_from_migration_file(self, file: io.FileName):
        if "_" not in file.getBaseNoExt():
            return LooseVersion(file.getBaseNoExt())
        return LooseVersion(file.getBaseNoExt().split("_")[0])

    def open_session(self, db_path: io.FileName = None):
        if db_path is None:
            db_path = self._db_path
        self.conn = sqlite3.connect(db_path.getPathTranslated())
        self.conn.row_factory = UnitOfWork.dict_factory
        self.cursor = self.conn.cursor()

    def commit(self):
        self._commit = True

    def rollback(self):
        self._commit = False
        self.conn.rollback()

    def close_session(self):
        if self._commit:
            self.conn.commit()

        self.cursor.close()
        self.conn.close()

    def execute(self, sql, *args) -> Cursor:
        if self.VERBOSE:
            self.logger.debug(f'[SQL] {sql}')
            sql_args_str = ','.join(map(str, args))
            self.logger.debug(f'[SQL] ARGS: {sql_args_str}')
        try:
            return self.cursor.execute(sql, args)
        except Exception as ex:
            self.logger.error(f'Error while executing query: {sql}', exc_info=ex)
            sql_args_str = ','.join(map(str, args))
            self.logger.error(f'Used arguments: {sql_args_str}')
            raise

    def execute_single_session(self, db_path, sql, args):
        self.open_session(db_path)
        self.execute(sql, *args)
        self.commit()
        self.close_session()

    def execute_script(self, sql_statements):
        self.conn.executescript(sql_statements)
            
    def single_result(self) -> dict:
        return self.cursor.fetchone()

    def result_set(self) -> typing.List[dict]:
        return self.cursor.fetchall()

    def result_id(self):
        return self.cursor.lastrowid

    def __enter__(self):
        self.open_session()

    def __exit__(self, type, value, traceback):
        if type is not None:
            # errors raised
            self.logger.error("type: %s value: %s", type, value)
        self.close_session()

    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


#
# CategoryRepository -> Category from SQLite DB
#
class CategoryRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def find_category(self, category_id: str) -> Category:
        if category_id == constants.VCATEGORY_ADDONROOT_ID:
            return Category({'m_name': 'Root'})
        
        self._uow.execute(qry.SELECT_CATEGORY, category_id)
        category_data = self._uow.single_result()
                
        self._uow.execute(qry.SELECT_CATEGORY_ASSETS, category_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
        
        self._uow.execute(qry.SELECT_ITEM_ASSET_MAPPINGS, category_data['metadata_id'])
        asset_mappings_result_set = self._uow.result_set()
        asset_mappings = []
        for mapping_data in asset_mappings_result_set:
            asset_mappings.append(AssetMapping(mapping_data))
            
        return Category(category_data, assets, asset_mappings)

    def find_root_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(qry.SELECT_ROOT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROOT_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROOT_CATEGORY_ASSET_MAPPINGS)
        asset_mappings_result_set = self._uow.result_set()
                
        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))

            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == category_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                
            yield Category(category_data, assets, asset_mappings)

    def find_categories_by_parent(self, category_id) -> typing.Iterator[Category]:        
        if category_id == constants.VCATEGORY_ROOT_ID:
            for vcategory_id in constants.VCATEGORIES:
                yield VirtualCategoryFactory.create(vcategory_id)
        
        if category_id in constants.VCATEGORIES:
            return []
        
        self._uow.execute(qry.SELECT_CATEGORIES_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_CATEGORY_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
             
        self._uow.execute(qry.SELECT_CATEGORY_ASSET_MAPPINGS_BY_PARENT, category_id)
        asset_mappings_result_set = self._uow.result_set()

        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
        
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == category_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                        
            yield Category(category_data, assets, asset_mappings)

    def find_all_categories(self) -> typing.Iterator[Category]:
        self._uow.execute(qry.SELECT_CATEGORIES)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ALL_CATEGORY_ASSETS)
        assets_result_set = self._uow.result_set()
                 
        self._uow.execute(qry.SELECT_ALL_CATEGORY_ASSET_MAPPINGS)
        asset_mappings_result_set = self._uow.result_set()

        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
            
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == category_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                
            yield Category(category_data, assets, asset_mappings)
        
    def find_categories_by_rom(self, rom_id: str) -> typing.Iterator[Category]:
        self._uow.execute(qry.SELECT_CATEGORIES_BY_ROM, rom_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_CATEGORIES_ASSETS_BY_ROM, rom_id)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_CATEGORY_ASSET_MAPPINGS_BY_ROM, rom_id)
        asset_mappings_result_set = self._uow.result_set()

        for category_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['category_id'] == category_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
                
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == category_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                
            yield Category(category_data, assets, asset_mappings)          
    
    def insert_category(self, category_obj: Category, parent_obj: Category = None):
        self.logger.info("CategoryRepository.insert_category(): Inserting new category '{}'".format(category_obj.get_name()))
        metadata_id = text.misc_generate_random_SID()
        parent_category_id = parent_obj.get_id() if parent_obj is not None and parent_obj.get_id() != constants.VCATEGORY_ADDONROOT_ID else None
        
        self._uow.execute(qry.INSERT_METADATA,
                          metadata_id,
                          category_obj.get_releaseyear(),
                          category_obj.get_genre(),
                          category_obj.get_developer(),
                          category_obj.get_rating(),
                          category_obj.get_plot(),
                          json.dumps(category_obj.get_extras()),
                          category_obj.is_finished())

        self._uow.execute(qry.INSERT_CATEGORY,
                          category_obj.get_id(),
                          category_obj.get_name(),
                          parent_category_id,
                          metadata_id)

        category_assets = category_obj.get_assets()
        for asset in category_assets: 
            self._insert_asset(asset, category_obj)

        for mapping in category_obj.asset_mappings:
            self._insert_asset_mapping(mapping, category_obj)

    def update_category(self, category_obj: Category):
        self.logger.info(f" Updating category '{category_obj.get_name()}'")
        
        self._uow.execute(qry.UPDATE_METADATA,
                          category_obj.get_releaseyear(),
                          category_obj.get_genre(),
                          category_obj.get_developer(),
                          category_obj.get_rating(),
                          category_obj.get_plot(),
                          json.dumps(category_obj.get_extras()),
                          category_obj.is_finished(),
                          category_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(qry.UPDATE_CATEGORY,
                          category_obj.get_name(),
                          category_obj.get_id())
        
        for asset in category_obj.get_assets():
            if asset.get_id() == '':
                self._insert_asset(asset, category_obj)
            else:
                self._update_asset(asset, category_obj)

        for mapping in category_obj.asset_mappings:
            if mapping.get_id() == '':
                self._insert_asset_mapping(mapping, category_obj)
            else:
                self._update_asset_mapping(mapping, category_obj)

    def delete_category(self, category_id: str):
        self.logger.info("CategoryRepository.delete_category(): Deleting category '{}'".format(category_id))
        self._uow.execute(qry.DELETE_CATEGORY, category_id)

    def add_rom_to_category(self, category_id: str, rom_id: str):
        if category_id is None:
            self._uow.execute(qry.INSERT_ROM_IN_ROOT_CATEGORY, rom_id)
            return
        self._uow.execute(qry.INSERT_ROM_IN_CATEGORY, rom_id, category_id)
            
    def remove_rom_from_category(self, category_id: str, rom_id: str):
        self._uow.execute(qry.REMOVE_ROM_FROM_CATEGORY, rom_id, category_id)
        
    def remove_all_roms_in_category(self, category_id: str):
        self._uow.execute(qry.REMOVE_ROMS_FROM_CATEGORY, category_id)
                
    def _insert_asset(self, asset: Asset, category_obj: Category):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(qry.INSERT_CATEGORY_ASSET, category_obj.get_id(), asset_db_id)   
    
    def _update_asset(self, asset: Asset, category_obj: Category):
        self._uow.execute(qry.UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('category_id') is None:
            self._uow.execute(qry.INSERT_CATEGORY_ASSET, category_obj.get_id(), asset.get_id())   

    def _insert_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if not mapping.is_mapped():
            return
        mapping_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_MAPPING, mapping_db_id, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id)
        self._uow.execute(qry.INSERT_MAPPING_WITH_METADATA, obj.get_metadata_id(), mapping_db_id)   
 
    def _update_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if mapping.is_mapped():
            self._uow.execute(qry.UPDATE_ASSET_MAPPING, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id, mapping.get_id())
            return
        self._uow.execute(qry.DELETE_ASSET_MAPPING, mapping.get_id())   
        

#
# ROMCollectionRepository -> ROM Sets from SQLite DB
#
class ROMCollectionRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def count_collections(self) -> int:
        self._uow.execute(qry.COUNT_ROMCOLLECTIONS)
        count_data = self._uow.single_result()
        
        return int(count_data['count'])

    def find_romcollection(self, romcollection_id: str) -> ROMCollection:
        if romcollection_id is None:
            return None
        self._uow.execute(qry.SELECT_ROMCOLLECTION, romcollection_id)
        romcollection_data = self._uow.single_result()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSETS_BY_SET, romcollection_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
                    
        self._uow.execute(qry.SELECT_ITEM_ASSET_MAPPINGS, romcollection_data['metadata_id'])
        asset_mappings_result_set = self._uow.result_set()
        asset_mappings = []
        for mapping_data in asset_mappings_result_set:
            asset_mappings.append(AssetMapping(mapping_data))
        
        self._uow.execute(qry.SELECT_SPECIFIC_ROMCOLLECTION_ROM_ASSET_MAPPINGS, romcollection_data['id'])
        rom_asset_mappings_result_set = self._uow.result_set()
        rom_asset_mappings = []
        for mapping_data in rom_asset_mappings_result_set:
            rom_asset_mappings.append(RomAssetMapping(mapping_data))
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_LAUNCHERS, romcollection_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AklAddon(launcher_data.copy())
            launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
            launchers.append(launcher)
                    
        return ROMCollection(romcollection_data, assets, asset_mappings, rom_asset_mappings, launchers)
    
    def find_all_romcollections(self) -> typing.Iterator[ROMCollection]:
        self._uow.execute(qry.SELECT_ROMCOLLECTIONS)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSETS)
        assets_result_set = self._uow.result_set()
                
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSET_MAPPINGS)
        asset_mappings_result_set = self._uow.result_set()
                
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ROM_ASSET_MAPPINGS)
        rom_asset_mappings_result_set = self._uow.result_set()

        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
            
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == romcollection_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                    
            rom_asset_mappings = []
            for mapping_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], rom_asset_mappings_result_set):
                rom_asset_mappings.append(RomAssetMapping(mapping_data))
                    
            yield ROMCollection(romcollection_data, assets, asset_mappings=asset_mappings, rom_asset_mappings=rom_asset_mappings)

    def find_root_romcollections(self) -> typing.Iterator[ROMCollection]:
        self._uow.execute(qry.SELECT_ROOT_ROMCOLLECTIONS)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROOT_ROMCOLLECTION_ASSETS)
        assets_result_set = self._uow.result_set()
                
        self._uow.execute(qry.SELECT_ROOT_ROMCOLLECTION_ASSET_MAPPINGS)
        asset_mappings_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROOT_ROMCOLLECTION_ROM_ASSET_MAPPINGS)
        rom_asset_mappings_result_set = self._uow.result_set()
                
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))      
                
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == romcollection_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))

            rom_asset_mappings = []
            for mapping_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], rom_asset_mappings_result_set):
                rom_asset_mappings.append(RomAssetMapping(mapping_data))

            yield ROMCollection(romcollection_data, assets, asset_mappings=asset_mappings, rom_asset_mappings=rom_asset_mappings)

    def find_romcollections_by_parent(self, category_id: str) -> typing.Iterator[ROMCollection]:
        
        if category_id in constants.VCATEGORIES:
            for collection in self.find_virtualcollections_by_category(category_id):
                yield collection
        
        self._uow.execute(qry.SELECT_ROMCOLLECTIONS_BY_PARENT, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTIONS_ASSETS_BY_PARENT, category_id)
        assets_result_set = self._uow.result_set()
                
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSET_MAPPINGS_BY_PARENT, category_id)
        asset_mappings_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROMCOLLECTION_ROM_ASSET_MAPPINGS_BY_PARENT, category_id)
        rom_asset_mappings_result_set = self._uow.result_set()

        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))   

            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == romcollection_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                
            rom_asset_mappings = []
            for mapping_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], rom_asset_mappings_result_set):
                rom_asset_mappings.append(RomAssetMapping(mapping_data))
                
            yield ROMCollection(romcollection_data, assets, asset_mappings=asset_mappings, rom_asset_mappings=rom_asset_mappings)

    def find_virtualcollections_by_category(self, vcategory_id: str) -> typing.Iterator[VirtualCollection]:
        query = self._get_collections_query_by_vcategory_id(vcategory_id)
        if query is None:
            return []
        
        self._uow.execute(query)
        result_set = self._uow.result_set()
        
        for result in result_set:
            option_value = str(result['option_value'])
            if not option_value:
                option_value = 'Undefined'
            yield VirtualCollectionFactory.create_by_category(vcategory_id, option_value)
            
    def find_romcollections_by_rom(self, rom_id: str) -> typing.Iterator[ROMCollection]:
        self._uow.execute(qry.SELECT_ROMCOLLECTIONS_BY_ROM, rom_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSETS_BY_ROM, rom_id)
        assets_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSET_MAPPINGS_BY_ROM, rom_id)
        asset_mappings_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ROM_ASSET_MAPPINGS_BY_ROM, rom_id)
        rom_asset_mappings_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_LAUNCHERS_BY_ROM, rom_id)
        launchers_data = self._uow.result_set()
        
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))
                                    
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == romcollection_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                        
            rom_asset_mappings = []
            for mapping_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], rom_asset_mappings_result_set):
                rom_asset_mappings.append(RomAssetMapping(mapping_data))
                
            launchers = []
            for launcher_data in launchers_data:
                addon = AklAddon(launcher_data.copy())
                launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
                launchers.append(launcher)
                
            yield ROMCollection(romcollection_data, assets, asset_mappings, rom_asset_mappings, launchers)
    
    def find_romcollections_by_source(self, source_id: str) -> typing.Iterator[ROMCollection]:
        self._uow.execute(qry.SELECT_ROMCOLLECTIONS_BY_SOURCE, source_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSETS_BY_SOURCE, source_id)
        assets_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROMCOLLECTION_ASSET_MAPPINGS_BY_SOURCE, source_id)
        asset_mappings_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_ROM_ASSET_MAPPINGS_BY_SOURCE, source_id)
        rom_asset_mappings_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROMCOLLECTION_LAUNCHERS_BY_SOURCE, source_id)
        launchers_data = self._uow.result_set()
        
        for romcollection_data in result_set:
            assets = []
            for asset_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], assets_result_set):
                assets.append(Asset(asset_data))
                                    
            asset_mappings = []
            for mapping_data in filter(lambda a: a['metadata_id'] == romcollection_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(AssetMapping(mapping_data))
                        
            rom_asset_mappings = []
            for mapping_data in filter(lambda a: a['romcollection_id'] == romcollection_data['id'], rom_asset_mappings_result_set):
                rom_asset_mappings.append(RomAssetMapping(mapping_data))
                
            launchers = []
            for launcher_data in launchers_data:
                addon = AklAddon(launcher_data.copy())
                launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
                launchers.append(launcher)
                
            yield ROMCollection(romcollection_data, assets, asset_mappings, rom_asset_mappings, launchers)
        
    def find_import_rules_by_collection(self, romcollection: ROMCollection) -> typing.Iterator[RuleSet]:
        self._uow.execute(qry.SELECT_IMPORT_RULES_BY_COLLECTION, romcollection.get_id())
        result_set = self._uow.result_set()
        rulesets = {}
        for rule_data in result_set:
            rulesets.setdefault(rule_data["ruleset_id"], []).append(rule_data)
        
        for ruleset_data in rulesets.values():
            entity_data = ruleset_data[0]
            entity_data['rules'] = ruleset_data
            yield RuleSet(entity_data)
    
    def find_ruleset(self, romcollection_id, ruleset_id):
        self._uow.execute(qry.SELECT_IMPORT_RULE_BY_COLLECTION, romcollection_id, ruleset_id)
        result_set = self._uow.result_set()

        entity_data = result_set[0]
        entity_data['rules'] = result_set
            
        return RuleSet(entity_data)
    
    def insert_romcollection(self, romcollection_obj: ROMCollection, parent_obj: Category = None):
        self.logger.info(f"ROMCollectionRepository: Inserting new romcollection '{romcollection_obj.get_name()}'")
        metadata_id = text.misc_generate_random_SID()
        parent_category_id = parent_obj.get_id() if parent_obj is not None and parent_obj.get_id() != constants.VCATEGORY_ADDONROOT_ID else None
        
        self._uow.execute(qry.INSERT_METADATA,
                          metadata_id,
                          romcollection_obj.get_releaseyear(),
                          romcollection_obj.get_genre(),
                          romcollection_obj.get_developer(),
                          romcollection_obj.get_rating(),
                          romcollection_obj.get_plot(),
                          json.dumps(romcollection_obj.get_extras()),
                          romcollection_obj.is_finished())

        self._uow.execute(qry.INSERT_ROMCOLLECTION,
                          romcollection_obj.get_id(),
                          romcollection_obj.get_name(),
                          parent_category_id,
                          metadata_id,
                          romcollection_obj.get_platform(),
                          romcollection_obj.get_box_sizing())
        
        romcollection_assets = romcollection_obj.get_assets()
        for asset in romcollection_assets: 
            self._insert_asset(asset, romcollection_obj)
            
        asset_paths = romcollection_obj.get_asset_paths()
        for asset_path in asset_paths:
            self._insert_asset_path(asset_path, romcollection_obj)

        for mapping in romcollection_obj.asset_mappings:
            self._insert_asset_mapping(mapping, romcollection_obj)

        for mapping in romcollection_obj.rom_asset_mappings:
            self._insert_rom_asset_mapping(mapping, romcollection_obj)

        romcollection_launchers = romcollection_obj.get_launchers()
        for romcollection_launcher in romcollection_launchers:
            romcollection_launcher.set_id(text.misc_generate_random_SID())
            self._uow.execute(qry.INSERT_ROMCOLLECTION_LAUNCHER,
                              romcollection_launcher.get_id(),
                              romcollection_obj.get_id(),
                              romcollection_launcher.addon.get_id(),
                              romcollection_launcher.get_settings_str(),
                              romcollection_launcher.is_default())
                      
    def update_romcollection(self, romcollection_obj: ROMCollection):
        self.logger.info(f"ROMCollectionRepository.update_romcollection(): Updating romcollection '{romcollection_obj.get_name()}'")
        
        self._uow.execute(qry.UPDATE_METADATA,
                          romcollection_obj.get_releaseyear(),
                          romcollection_obj.get_genre(),
                          romcollection_obj.get_developer(),
                          romcollection_obj.get_rating(),
                          romcollection_obj.get_plot(),
                          json.dumps(romcollection_obj.get_extras()),
                          romcollection_obj.is_finished(),
                          romcollection_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(qry.UPDATE_ROMCOLLECTION,
                          romcollection_obj.get_name(),
                          romcollection_obj.get_platform(),
                          romcollection_obj.get_box_sizing(),
                          romcollection_obj.get_id())
                     
        romcollection_launchers = romcollection_obj.get_launchers()
        for romcollection_launcher in romcollection_launchers:
            if romcollection_launcher.get_custom_attribute("romcollection_id") is None:
                self._uow.execute(qry.INSERT_ROMCOLLECTION_LAUNCHER,
                                  romcollection_launcher.get_id(),
                                  romcollection_obj.get_id(),
                                  romcollection_launcher.is_default())
            else:
                self._uow.execute(qry.UPDATE_ROMCOLLECTION_LAUNCHER,
                                  romcollection_launcher.is_default(),
                                  romcollection_obj.get_id(),
                                  romcollection_launcher.get_id())
                
        for asset in romcollection_obj.get_assets():
            if asset.get_id() == '':
                self._insert_asset(asset, romcollection_obj)
            else:
                self._update_asset(asset, romcollection_obj)   
                  
        for asset_path in romcollection_obj.get_asset_paths():
            if asset_path.get_id() == '':
                self._insert_asset_path(asset_path, romcollection_obj)
            else:
                self._update_asset_path(asset_path, romcollection_obj)
            
        for mapping in romcollection_obj.asset_mappings:
            if mapping.get_id() == '':
                self._insert_asset_mapping(mapping, romcollection_obj)
            else:
                self._update_asset_mapping(mapping, romcollection_obj)

        for mapping in romcollection_obj.rom_asset_mappings:
            if mapping.get_id() == '':
                self._insert_rom_asset_mapping(mapping, romcollection_obj)
            else:
                self._update_rom_asset_mapping(mapping, romcollection_obj)

    def update_romcollection_parent_reference(self, romcollection_obj: ROMCollection, parent_obj: Category = None):
        self.logger.info(f"ROMCollectionRepository: Updating romcollection '{romcollection_obj.get_name()}'")
        parent_category_id = parent_obj.get_id() if parent_obj is not None and parent_obj.get_id() != constants.VCATEGORY_ADDONROOT_ID else None
        self._uow.execute(qry.UPDATE_ROMCOLLECTION_PARENT, parent_category_id, romcollection_obj.get_id())
            
    def add_rom_to_romcollection(self, romcollection_id: str, rom_id: str):
        self._uow.execute(qry.INSERT_ROM_IN_ROMCOLLECTION, rom_id, romcollection_id)
            
    def remove_rom_from_romcollection(self, romcollection_id: str, rom_id: str):
        self._uow.execute(qry.REMOVE_ROM_FROM_ROMCOLLECTION, rom_id, romcollection_id)
        
    def remove_all_roms_in_launcher(self, romcollection_id: str):
        self._uow.execute(qry.REMOVE_ROMS_FROM_ROMCOLLECTION, romcollection_id)
        
    def delete_romcollection(self, romcollection_id: str):
        self.logger.info("ROMCollectionRepository.delete_romcollection(): Deleting romcollection '{}'".format(romcollection_id))
        self._uow.execute(qry.DELETE_ROMCOLLECTION, romcollection_id)

    def remove_launcher(self, romcollection_id: str, launcher_id: str):
        self._uow.execute(qry.DELETE_ROMCOLLECTION_LAUNCHER, romcollection_id, launcher_id)

    def add_ruleset_to_romcollection(self, romcollection_id: str, ruleset: RuleSet):
        self._uow.execute(qry.INSERT_RULESET_FOR_ROMCOLLECTION,
                          ruleset.get_ruleset_id(),
                          ruleset.get_source_id(),
                          romcollection_id,
                          int(ruleset.get_set_operator()))

    def update_ruleset_in_romcollection(self, romcollection_id: str, ruleset: RuleSet):
        self._uow.execute(qry.UPDATE_RULESET_FOR_ROMCOLLECTION,
                          ruleset.get_source_id(),
                          romcollection_id,
                          int(ruleset.get_set_operator()),
                          ruleset.get_ruleset_id())
        
        for rule in ruleset.get_rules():
            if rule.get_id() == '':
                self._insert_rule(rule, ruleset)
            else:
                self._update_rule(rule, ruleset)

    def delete_all_rules_from_ruleset(self, ruleset: RuleSet):
        self._uow.execute(qry.DELETE_ALL_RULES_FROM_RULESET, ruleset.get_ruleset_id())

    def delete_rule_from_ruleset(self, ruleset: RuleSet, rule: Rule):
        self._uow.execute(qry.DELETE_RULE_FROM_RULESET, rule.get_id(), ruleset.get_ruleset_id())
    
    def _insert_asset(self, asset: Asset, romcollection_obj: ROMCollection):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(qry.INSERT_ROMCOLLECTION_ASSET, romcollection_obj.get_id(), asset_db_id)
    
    def _update_asset(self, asset: Asset, romcollection_obj: ROMCollection):
        self._uow.execute(qry.UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('romcollection_id') is None:
            self._uow.execute(qry.INSERT_ROMCOLLECTION_ASSET, romcollection_obj.get_id(), asset.get_id())
    
    def _insert_asset_path(self, asset_path: AssetPath, romcollection_obj: ROMCollection):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_PATH, asset_db_id, asset_path.get_path(), asset_path.get_asset_info_id())
        self._uow.execute(qry.INSERT_ROMCOLLECTION_ASSET_PATH, romcollection_obj.get_id(), asset_db_id)
        
    def _update_asset_path(self, asset_path: AssetPath, romcollection_obj: ROMCollection):
        self._uow.execute(qry.UPDATE_ASSET_PATH, asset_path.get_path(), asset_path.get_asset_info_id(), asset_path.get_id())
        if asset_path.get_custom_attribute('romcollection_id') is None:
            self._uow.execute(qry.INSERT_ROMCOLLECTION_ASSET_PATH, romcollection_obj.get_id(), asset_path.get_id())

    def _insert_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if not mapping.is_mapped():
            return
        mapping_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_MAPPING, mapping_db_id, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id)
        self._uow.execute(qry.INSERT_MAPPING_WITH_METADATA, obj.get_metadata_id(), mapping_db_id)
 
    def _update_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if mapping.is_mapped():
            self._uow.execute(qry.UPDATE_ASSET_MAPPING, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id, mapping.get_id())
            return
        self._uow.execute(qry.DELETE_ASSET_MAPPING, mapping.get_id())

    def _insert_rom_asset_mapping(self, mapping: RomAssetMapping, obj: ROMCollection):
        if not mapping.is_mapped():
            return
        mapping_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_MAPPING, mapping_db_id, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id)
        self._uow.execute(qry.INSERT_ROMCOLLECTION_ROM_ASSET_MAPPING, obj.get_id(), mapping_db_id)
 
    def _update_rom_asset_mapping(self, mapping: RomAssetMapping, obj: MetaDataItemABC):
        if mapping.is_mapped():
            self._uow.execute(qry.UPDATE_ASSET_MAPPING,
                              mapping.get_asset_info().id,
                              mapping.get_mapped_to_asset_info().id,
                              mapping.get_id())
            return
        self._uow.execute(qry.DELETE_ASSET_MAPPING, mapping.get_id())

    def _insert_rule(self, rule: Rule, ruleset: RuleSet):
        rule_id = text.misc_generate_random_SID()
        rule.set_id(rule_id)
        self._uow.execute(qry.INSERT_RULE, rule.get_id(), ruleset.get_ruleset_id(), 
                          rule.get_property(), rule.get_value(), rule.get_operator())
                 
    def _update_rule(self, rule: Rule, ruleset: RuleSet):
        self._uow.execute(qry.UPDATE_RULE, rule.get_property(), rule.get_value(),
                          rule.get_operator(), rule.get_id())
                 
    def _get_collections_query_by_vcategory_id(self, vcategory_id: str) -> str:
        if vcategory_id == constants.VCATEGORY_TITLE_ID:
            return qry.SELECT_VCOLLECTION_TITLES   
        if vcategory_id == constants.VCATEGORY_GENRE_ID:
            return qry.SELECT_VCOLLECTION_GENRES
        if vcategory_id == constants.VCATEGORY_DEVELOPER_ID:
            return qry.SELECT_VCOLLECTION_DEVELOPER
        if vcategory_id == constants.VCATEGORY_ESRB_ID:
            return qry.SELECT_VCOLLECTION_ESRB
        if vcategory_id == constants.VCATEGORY_PEGI_ID:
            return qry.SELECT_VCOLLECTION_PEGI
        if vcategory_id == constants.VCATEGORY_YEARS_ID:
            return qry.SELECT_VCOLLECTION_YEAR
        if vcategory_id == constants.VCATEGORY_NPLAYERS_ID:
            return qry.SELECT_VCOLLECTION_NPLAYERS
        if vcategory_id == constants.VCATEGORY_RATING_ID:
            return qry.SELECT_VCOLLECTION_RATING

        return None


class ROMsRepository(object):
       
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def find_root_roms(self) -> typing.Iterator[ROM]:
        self._uow.execute(qry.SELECT_ROMS_BY_ROOT_CATEGORY)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETS_BY_ROOT_CATEGORY)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETPATHS_BY_ROOT_CATEGORY)
        asset_paths_result_set = self._uow.result_set()
                    
        self._uow.execute(qry.SELECT_ROM_ASSET_MAPPINGS_BY_ROOT_CATEGORY)
        asset_mappings_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_SCANNED_DATA_BY_ROOT_CATEGORY)
        scanned_data_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROM_TAGS_BY_ROOT_CATEGORY)
        tags_data_set = self._uow.result_set()

        return self._process_roms_data(result_set, assets_result_set, asset_paths_result_set, asset_mappings_result_set, 
                                       scanned_data_result_set, tags_data_set)
 
    def find_roms_by_category(self, category: Category) -> typing.Iterator[ROM]:
        category_id = category.get_id() if category else None
        
        self._uow.execute(qry.SELECT_ROMS_BY_CATEGORY, category_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETS_BY_CATEGORY, category_id)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETPATHS_BY_CATEGORY, category_id)
        asset_paths_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSET_MAPPINGS_BY_CATEGORY, category_id)
        asset_mappings_result_set = self._uow.result_set()
                    
        self._uow.execute(qry.SELECT_ROM_SCANNED_DATA_BY_CATEGORY, category_id)
        scanned_data_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROM_TAGS_BY_CATEGORY, category_id)
        tags_data_set = self._uow.result_set()
     
        return self._process_roms_data(result_set, assets_result_set, asset_paths_result_set, asset_mappings_result_set, 
                                       scanned_data_result_set, tags_data_set)

    def find_roms_by_romcollection(self, romcollection: ROMCollection) -> typing.Iterator[ROM]:
        is_virtual = romcollection.get_type() == constants.OBJ_COLLECTION_VIRTUAL
        romcollection_id = romcollection.get_id()
        
        if is_virtual:
            vcollection: VirtualCollection = romcollection
            query_param = vcollection.get_collection_value()
            roms_query, rom_assets_query = self._get_queries_by_vcollection_type(romcollection)
            
            if query_param is not None:
                self._uow.execute(roms_query, query_param)
                result_set = self._uow.result_set()
                self._uow.execute(rom_assets_query, query_param)
                assets_result_set = self._uow.result_set()
            else: 
                self._uow.execute(roms_query)
                result_set = self._uow.result_set()
                self._uow.execute(rom_assets_query)
                assets_result_set = self._uow.result_set()
                    
            asset_paths_result_set = []
            asset_mappings_result_set = []
            scanned_data_result_set = []
            tags_data_set = {}
        else:
            self._uow.execute(qry.SELECT_ROMS_BY_SET, romcollection_id)
            result_set = self._uow.result_set()
            
            self._uow.execute(qry.SELECT_ROM_ASSETS_BY_SET, romcollection_id)
            assets_result_set = self._uow.result_set()
            
            self._uow.execute(qry.SELECT_ROM_ASSETPATHS_BY_SET, romcollection_id)
            asset_paths_result_set = self._uow.result_set()
                            
            self._uow.execute(qry.SELECT_ROM_ASSET_MAPPINGS_BY_SET, romcollection_id)
            asset_mappings_result_set = self._uow.result_set()

            self._uow.execute(qry.SELECT_ROM_SCANNED_DATA_BY_SET, romcollection_id)
            scanned_data_result_set = self._uow.result_set()

            self._uow.execute(qry.SELECT_ROM_TAGS_BY_SET, romcollection_id)
            tags_data_set = self._uow.result_set()
                        
        return self._process_roms_data(result_set, assets_result_set, asset_paths_result_set, asset_mappings_result_set, 
                                       scanned_data_result_set, tags_data_set)

    def find_roms_by_source(self, source: Source) -> typing.Iterator[ROM]:
        source_id = source.get_id()

        self._uow.execute(qry.SELECT_ROMS_BY_SOURCE, source_id)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETS_BY_SOURCE, source_id)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_ROM_ASSETPATHS_BY_SOURCE, source_id)
        asset_paths_result_set = self._uow.result_set()
                        
        self._uow.execute(qry.SELECT_ROM_ASSET_MAPPINGS_BY_SOURCE, source_id)
        asset_mappings_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROM_SCANNED_DATA_BY_SOURCE, source_id)
        scanned_data_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_ROM_TAGS_BY_SOURCE, source_id)
        tags_data_set = self._uow.result_set()
                        
        return self._process_roms_data(result_set, assets_result_set, asset_paths_result_set, asset_mappings_result_set, 
                                       scanned_data_result_set, tags_data_set)
  
    def find_standalone_roms(self) -> typing.Iterator[ROM]:
        
        self._uow.execute(qry.SELECT_STANDALONE_ROMS)
        result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_STANDALONE_ROM_ASSETS)
        assets_result_set = self._uow.result_set()
        
        self._uow.execute(qry.SELECT_STANDALONE_ROM_ASSETPATHS)
        asset_paths_result_set = self._uow.result_set()
                        
        self._uow.execute(qry.SELECT_STANDALONE_ROM_ASSET_MAPPINGS)
        asset_mappings_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_STANDALONE_ROM_SCANNED_DATA)
        scanned_data_result_set = self._uow.result_set()

        self._uow.execute(qry.SELECT_STANDALONE_ROM_TAGS)
        tags_data_set = self._uow.result_set()
               
        return self._process_roms_data(result_set, assets_result_set, asset_paths_result_set, asset_mappings_result_set, 
                                       scanned_data_result_set, tags_data_set)
        
    def find_rom(self, rom_id: str) -> ROM:
        self._uow.execute(qry.SELECT_ROM, rom_id)
        rom_data = self._uow.single_result()

        self._uow.execute(qry.SELECT_ROM_ASSETS, rom_id)
        assets_result_set = self._uow.result_set()
        assets = []
        for asset_data in assets_result_set:
            assets.append(Asset(asset_data))
                                
        self._uow.execute(qry.SELECT_ROM_ASSETPATHS, rom_id)
        asset_paths_result_set = self._uow.result_set()
        asset_paths = []
        for asset_paths_data in asset_paths_result_set:
            asset_paths.append(AssetPath(asset_paths_data))

        self._uow.execute(qry.SELECT_ITEM_ASSET_MAPPINGS, rom_data['metadata_id'])
        asset_mappings_result_set = self._uow.result_set()
        asset_mappings = []
        for mapping_data in asset_mappings_result_set:
            asset_mappings.append(RomAssetMapping(mapping_data))

        self._uow.execute(qry.SELECT_ROM_SCANNED_DATA, rom_id)
        scanned_data_result_set = self._uow.result_set()
        scanned_data = {entry['data_key']: entry['data_value'] for entry in scanned_data_result_set}
        
        self._uow.execute(qry.SELECT_ROM_LAUNCHERS, rom_id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AklAddon(launcher_data.copy())
            launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
            launchers.append(launcher)

        self._uow.execute(qry.SELECT_ROM_TAGS, rom_id)
        tags_data = self._uow.result_set()
        tags = {}
        for tag_data in tags_data:
            tags[tag_data['tag']] = tag_data['id']
                  
        return ROM(rom_data, tags, assets, asset_paths, asset_mappings, scanned_data, launchers)

    def find_all_tags(self) -> dict:
        self._uow.execute(qry.SELECT_TAGS)
        tag_data = self._uow.result_set()
        tags = {}
        for tag in tag_data:
            tags[tag['tag']] = tag['id']
        return tags

    def insert_rom(self, rom_obj: ROM): 
        self.logger.info(f"Inserting new ROM '{rom_obj.get_rom_identifier()}'")
        metadata_id = text.misc_generate_random_SID()
        
        self._uow.execute(qry.INSERT_METADATA,
                          metadata_id,
                          rom_obj.get_releaseyear(),
                          rom_obj.get_genre(),
                          rom_obj.get_developer(),
                          rom_obj.get_rating(),
                          rom_obj.get_plot(),
                          json.dumps(rom_obj.get_extras()),
                          rom_obj.is_finished())
  
        self._uow.execute(qry.INSERT_ROM,
                          rom_obj.get_id(),
                          metadata_id,
                          rom_obj.get_name(),
                          rom_obj.get_number_of_players(),
                          rom_obj.get_number_of_players_online(),
                          rom_obj.get_esrb_rating(),
                          rom_obj.get_pegi_rating(),
                          rom_obj.get_platform(),
                          rom_obj.get_box_sizing(), 
                          rom_obj.get_nointro_status(),
                          rom_obj.get_clone(),
                          rom_obj.get_rom_status(),
                          rom_obj.get_scanned_by())
        
        rom_assets = rom_obj.get_assets()
        for asset in rom_assets:
            self._insert_asset(asset, rom_obj)
            
        for asset_path in rom_obj.get_asset_paths():
            if not asset_path.get_id():
                self._insert_asset_path(asset_path, rom_obj)
            else:
                self._update_asset_path(asset_path, rom_obj)

        for mapping in rom_obj.asset_mappings:
            self._insert_asset_mapping(mapping, rom_obj)

        tag_data = rom_obj.get_tag_data()
        self._insert_tags(tag_data, metadata_id)

        self._update_scanned_data(rom_obj.get_id(), rom_obj.scanned_data)
        self._update_launchers(rom_obj.get_id(), rom_obj.get_launchers())

    def update_rom(self, rom_obj: ROM):
        self.logger.info(f"Updating ROM '{rom_obj.get_rom_identifier()}'")
        
        self._uow.execute(qry.UPDATE_METADATA,
                          rom_obj.get_releaseyear(),
                          rom_obj.get_genre(),
                          rom_obj.get_developer(),
                          rom_obj.get_rating(),
                          rom_obj.get_plot(),
                          json.dumps(rom_obj.get_extras()),
                          rom_obj.is_finished(),
                          rom_obj.get_custom_attribute('metadata_id'))

        self._uow.execute(qry.UPDATE_ROM,
                          rom_obj.get_name(),
                          rom_obj.get_number_of_players(),
                          rom_obj.get_number_of_players_online(),
                          rom_obj.get_esrb_rating(),
                          rom_obj.get_pegi_rating(),
                          rom_obj.get_platform(),
                          rom_obj.get_box_sizing(),
                          rom_obj.get_nointro_status(),
                          rom_obj.get_clone(),
                          rom_obj.get_rom_status(),
                          rom_obj.get_launch_count(),
                          rom_obj.get_last_launch_date(),
                          rom_obj.is_favourite(),
                          rom_obj.get_scanned_by(),
                          rom_obj.get_id())
        
        for asset in rom_obj.get_assets():
            if not asset.get_id():
                self._insert_asset(asset, rom_obj)
            else:
                self._update_asset(asset, rom_obj)
        
        for asset_path in rom_obj.get_asset_paths():
            if not asset_path.get_id():
                self._insert_asset_path(asset_path, rom_obj)
            else:
                self._update_asset_path(asset_path, rom_obj)
            
        for mapping in rom_obj.asset_mappings:
            if mapping.get_id() == '':
                self._insert_asset_mapping(mapping, rom_obj)
            else:
                self._update_asset_mapping(mapping, rom_obj)

        tag_data = rom_obj.get_tag_data()
        self._update_tags(tag_data, rom_obj.get_custom_attribute('metadata_id'))

        self._update_scanned_data(rom_obj.get_id(), rom_obj.scanned_data)
        self._update_launchers(rom_obj.get_id(), rom_obj.get_launchers())
              
    def delete_rom(self, rom_id: str):
        self.logger.info("ROMsRepository.delete_rom(): Deleting ROM '{}'".format(rom_id))
        self._uow.execute(qry.DELETE_ROM, rom_id)

    def delete_roms_by_romcollection(self, romcollection_id: str):
        self._uow.execute(qry.DELETE_ROMS_BY_COLLECTION, romcollection_id)

    def remove_launcher(self, rom_id: str, launcher_id: str):
        self._uow.execute(qry.DELETE_ROM_LAUNCHER, rom_id, launcher_id)

    def insert_tag(self, tag: str) -> str:
        db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_TAG, db_id, tag)
        return db_id
    
    def delete_tag(self, tag_id: str):
        self._uow.execute(qry.DELETE_TAG, tag_id)

    def _process_roms_data(self, result_set, assets_result_set, asset_paths_result_set,
                           asset_mappings_result_set, scanned_data_result_set, tags_data_set) -> typing.Iterator[ROM]:
         
        for rom_data in result_set:
            assets = []
            asset_paths = []
            asset_mappings = []
            tags = {}
            for asset_data in filter(lambda a: a['rom_id'] == rom_data['id'], assets_result_set):
                assets.append(Asset(asset_data))    
            for asset_paths_data in filter(lambda a: a['rom_id'] == rom_data['id'], asset_paths_result_set):
                asset_paths.append(AssetPath(asset_paths_data))
            for mapping_data in filter(lambda a: a['metadata_id'] == rom_data['metadata_id'], asset_mappings_result_set):
                asset_mappings.append(RomAssetMapping(mapping_data))    
            for tag in filter(lambda t: t['rom_id'] == rom_data['id'], tags_data_set):
                tags[tag['tag']] = tag['id']
                
            scanned_data = {
                entry['data_key']: entry['data_value']
                for entry in filter(lambda s: s['rom_id'] == rom_data['id'], scanned_data_result_set)
            }
            yield ROM(rom_data, tags, assets, asset_paths, asset_mappings, scanned_data) 

    def _insert_asset(self, asset: Asset, rom_obj: ROM):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET, asset_db_id, asset.get_path(), asset.get_asset_info_id())
        self._uow.execute(qry.INSERT_ROM_ASSET, rom_obj.get_id(), asset_db_id)
    
    def _update_asset(self, asset: Asset, rom_obj: ROM):
        self._uow.execute(qry.UPDATE_ASSET, asset.get_path(), asset.get_asset_info_id(), asset.get_id())
        if asset.get_custom_attribute('rom_id') is None:
            self._uow.execute(qry.INSERT_ROM_ASSET, rom_obj.get_id(), asset.get_id())

    def _insert_asset_path(self, asset_path: AssetPath, rom_obj: ROM):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_PATH, asset_db_id, asset_path.get_path(), asset_path.get_asset_info_id())
        self._uow.execute(qry.INSERT_ROM_ASSET_PATH, rom_obj.get_id(), asset_db_id)
        
    def _update_asset_path(self, asset_path: AssetPath, rom_obj: ROM):
        self._uow.execute(qry.UPDATE_ASSET_PATH, asset_path.get_path(), asset_path.get_asset_info_id(), asset_path.get_id())
        if asset_path.get_custom_attribute('rom_id') is None:
            self._uow.execute(qry.INSERT_ROM_ASSET_PATH, rom_obj.get_id(), asset_path.get_id())

    def _insert_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if not mapping.is_mapped():
            return
        mapping_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_MAPPING, mapping_db_id, mapping.get_asset_info().id, mapping.get_mapped_to_asset_info().id)
        self._uow.execute(qry.INSERT_MAPPING_WITH_METADATA, obj.get_metadata_id(), mapping_db_id)
 
    def _update_asset_mapping(self, mapping: AssetMapping, obj: MetaDataItemABC):
        if mapping.is_mapped():
            self._uow.execute(qry.UPDATE_ASSET_MAPPING,
                              mapping.get_asset_info().id,
                              mapping.get_mapped_to_asset_info().id,
                              mapping.get_id())
            return
        self._uow.execute(qry.DELETE_ASSET_MAPPING, mapping.get_id())

    def _update_launchers(self, rom_id: str, rom_launchers: typing.List[ROMLauncherAddon]):
        for rom_launcher in rom_launchers:
            if rom_launcher.get_custom_attribute("rom_id") is None:
                self._uow.execute(qry.INSERT_ROM_LAUNCHER, rom_launcher.get_id(), rom_id, rom_launcher.is_default())
            else:
                self._uow.execute(qry.UPDATE_ROM_LAUNCHER, rom_launcher.is_default(), rom_id, rom_launcher.get_id())
     
    def _update_scanned_data(self, rom_id: str, scanned_data: dict):
        self._uow.execute(qry.DELETE_SCANNED_DATA, rom_id)
        for key, value in scanned_data.items():
            self._uow.execute(qry.INSERT_ROM_SCANNED_DATA, rom_id, key, value)

    def _update_tags(self, tag_data: dict, metadata_id: str):
        self._uow.execute(qry.DELETE_EXISTING_ROM_TAGS, metadata_id)
        self._insert_tags(tag_data, metadata_id)

    def _insert_tags(self, tag_data: dict, metadata_id: str):
        if tag_data is None:
            return

        existing_tags = self.find_all_tags()
        for tag_name, tag_id in tag_data.items():
            if tag_id == '':
                if tag_name not in existing_tags.keys():
                    tag_id = self.insert_tag(tag_name)
                else:
                    tag_id = existing_tags[tag_name]
            self._uow.execute(qry.ADD_TAG_TO_ROM, metadata_id, tag_id)

    def _get_queries_by_vcollection_type(self, vcollection: VirtualCollection) -> typing.Tuple[str, str]:
        
        vcollection_id = vcollection.get_id()
        vcategory_id = vcollection.get_parent_id()
        
        if vcategory_id is not None:
            if vcategory_id == constants.VCATEGORY_TITLE_ID:
                return qry.SELECT_BY_TITLE, qry.SELECT_BY_TITLE_ASSETS
            if vcategory_id == constants.VCATEGORY_GENRE_ID:
                return qry.SELECT_BY_GENRE, qry.SELECT_BY_GENRE_ASSETS
            if vcategory_id == constants.VCATEGORY_DEVELOPER_ID:
                return qry.SELECT_BY_DEVELOPER, qry.SELECT_BY_DEVELOPER_ASSETS
            if vcategory_id == constants.VCATEGORY_ESRB_ID:
                return qry.SELECT_BY_ESRB, qry.SELECT_BY_ESRB_ASSETS
            if vcategory_id == constants.VCATEGORY_PEGI_ID:
                return qry.SELECT_BY_PEGI, qry.SELECT_BY_PEGI_ASSETS
            if vcategory_id == constants.VCATEGORY_YEARS_ID:
                return qry.SELECT_BY_YEAR, qry.SELECT_BY_YEAR_ASSETS
            if vcategory_id == constants.VCATEGORY_NPLAYERS_ID:
                return qry.SELECT_BY_NPLAYERS, qry.SELECT_BY_NPLAYERS_ASSETS
            if vcategory_id == constants.VCATEGORY_RATING_ID:
                return qry.SELECT_BY_RATING, qry.SELECT_BY_RATING_ASSETS
        else:
            if vcollection_id == constants.VCOLLECTION_FAVOURITES_ID:
                return qry.SELECT_MY_FAVOURITES, qry.SELECT_FAVOURITES_ROM_ASSETS
            if vcollection_id == constants.VCOLLECTION_RECENT_ID:
                return qry.SELECT_RECENTLY_PLAYED_ROMS, qry.SELECT_RECENTLY_PLAYED_ROM_ASSETS
            if vcollection_id == constants.VCOLLECTION_MOST_PLAYED_ID:
                return qry.SELECT_MOST_PLAYED_ROMS, qry.SELECT_MOST_PLAYED_ROM_ASSETS
            
        return None, None
              
    def _get_query_by_filter(self, filter: str) -> typing.Tuple[str, str]:
        if filter == constants.META_GENRE_ID:
            return qry.SELECT_GENRES_BY_COLLECTION
        if filter == constants.META_YEAR_ID:
            return qry.SELECT_YEARS_BY_COLLECTION
        if filter == constants.META_DEVELOPER_ID:
            return qry.SELECT_DEVELOPER_BY_COLLECTION
        if filter == constants.META_RATING_ID:
            return qry.SELECT_RATING_BY_COLLECTION
        return None


class AklAddonRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def find(self, id: str) -> AklAddon:
        self._uow.execute(qry.SELECT_ADDON, id)
        result_set = self._uow.single_result()
        return AklAddon(result_set)

    def find_by_addon_id(self, addon_id: str, type: constants.AddonType) -> AklAddon:
        self._uow.execute(qry.SELECT_ADDON_BY_ADDON_ID, addon_id, type.name)
        result_set = self._uow.single_result()
        if result_set is None:
            return None
        return AklAddon(result_set)

    def find_all(self) -> typing.Iterator[AklAddon]:
        self._uow.execute(qry.SELECT_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AklAddon(addon_data)

    def find_all_launcher_addons(self) -> typing.Iterator[AklAddon]:
        self._uow.execute(qry.SELECT_LAUNCHER_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AklAddon(addon_data)

    def find_all_scanner_addons(self) -> typing.Iterator[AklAddon]:
        self._uow.execute(qry.SELECT_SCANNER_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AklAddon(addon_data)

    def find_all_scraper_addons(self) -> typing.Iterator[AklAddon]:
        self._uow.execute(qry.SELECT_SCRAPER_ADDONS)
        result_set = self._uow.result_set()
        for addon_data in result_set:
            yield AklAddon(addon_data)
            
    def insert_addon(self, addon: AklAddon):
        self.logger.info("Saving addon '{}'".format(addon.get_addon_id()))
        self._uow.execute(qry.INSERT_ADDON,
                          addon.get_id(),
                          addon.get_name(),
                          addon.get_addon_id(),
                          addon.get_version(),
                          addon.get_addon_type().name,
                          addon.get_extra_settings_str())
        
    def update_addon(self, addon: AklAddon):
        self.logger.info("Updating addon '{}'".format(addon.get_addon_id()))
        self.logger.info(f"EXTRA SETTINGS: {addon.get_extra_settings_str()}")
        self._uow.execute(qry.UPDATE_ADDON,
                          addon.get_name(),
                          addon.get_addon_id(),
                          addon.get_version(),
                          addon.get_addon_type().name,
                          addon.get_extra_settings_str(),
                          addon.get_id())


class SourcesRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def find(self, id: str) -> Source:
        if id is None or id == '':
            return None
        
        self._uow.execute(qry.SELECT_SOURCE, id)
        result_set = self._uow.single_result()
                
        self._uow.execute(qry.SELECT_SOURCE_ASSET_PATHS, id)
        asset_paths_result_set = self._uow.result_set()
        asset_paths = []
        for asset_paths_data in asset_paths_result_set:
            asset_paths.append(AssetPath(asset_paths_data))
        
        self._uow.execute(qry.SELECT_SOURCE_LAUNCHERS, id)
        launchers_data = self._uow.result_set()
        launchers = []
        for launcher_data in launchers_data:
            addon = AklAddon(launcher_data.copy())
            launcher = ROMLauncherAddonFactory.create(addon, launcher_data)
            launchers.append(launcher)
        
        addon = AklAddon(result_set.copy())
        return Source(result_set, addon, asset_paths, launchers)

    def find_all(self) -> typing.Iterator[Source]:
        self._uow.execute(qry.SELECT_SOURCES)
        result_sets = self._uow.result_set()
        
        for result_set in result_sets:
            addon = AklAddon(result_set.copy())
            yield Source(result_set, addon)

    def find_sources_by_collection(self, romcollection_id) -> typing.Iterator[Source]:
        self._uow.execute(qry.SELECT_SOURCES_BY_ROMCOLLECTION, romcollection_id)
        result_sets = self._uow.result_set()
        
        for result_set in result_sets:
            addon = AklAddon(result_set.copy())
            yield Source(result_set, addon)

    def find_romcollection_ids_by_source(self, source_id):
        self._uow.execute(qry.SELECT_ROMCOLLECTION_IDS_BY_SOURCE, source_id)
        result_sets = self._uow.result_set()
        collection_ids = []
        for result_set in result_sets:
            collection_ids.append(result_set['collection_id'])
        return collection_ids
        
    def insert_source(self, source: Source):
        self.logger.info(f"SourcesRepository.insert_source(): Inserting new source '{source.get_name()}'")
        
        assets_path = source.get_assets_root_path()
        addon = source.get_addon()
        
        self._uow.execute(qry.INSERT_SOURCE,
                          source.get_id(),
                          source.get_name(),
                          source.get_platform(),
                          source.get_box_sizing(),
                          assets_path.getPath() if assets_path is not None else None,
                          source.get_last_scan_timestamp(),
                          source.get_settings_str(),
                          addon.get_id())
                  
        for asset_path in source.get_asset_paths():
            self._insert_asset_path(asset_path, source)
        self._update_launchers(source.get_id(), source.get_launchers())

    def update_source(self, source: Source):
        self.logger.info(f"SourcesRepository.update_source(): Updating source '{source.get_name()}'")
        assets_path = source.get_assets_root_path()
        
        self._uow.execute(qry.UPDATE_SOURCE,
                          source.get_name(),
                          source.get_platform(),
                          source.get_box_sizing(),
                          assets_path.getPath() if assets_path is not None else None,
                          source.get_last_scan_timestamp(),
                          source.get_settings_str(),
                          source.get_id())
                  
        for asset_path in source.get_asset_paths():
            if asset_path.get_id() == '':
                self._insert_asset_path(asset_path, source)
            else:
                self._update_asset_path(asset_path, source)
        self._update_launchers(source.get_id(), source.get_launchers())

    def delete_source(self, source_id: str):
        self.logger.info(f"SourcesRepository.delete_source(): Deleting source '{source_id}'")
        self._uow.execute(qry.DELETE_SOURCE, source_id)

    def remove_all_roms_in_source(self, source_id: str):
        self._uow.execute(qry.REMOVE_ROMS_FROM_SOURCE, source_id)
    
    def remove_launcher(self, source_id: str, launcher_id: str):
        self._uow.execute(qry.DELETE_SOURCE_LAUNCHER, source_id, launcher_id)
     
    def _insert_asset_path(self, asset_path: AssetPath, source: Source):
        asset_db_id = text.misc_generate_random_SID()
        self._uow.execute(qry.INSERT_ASSET_PATH, asset_db_id, asset_path.get_path(), asset_path.get_asset_info_id())
        self._uow.execute(qry.INSERT_SOURCE_ASSET_PATH, source.get_id(), asset_db_id)
        
    def _update_asset_path(self, asset_path: AssetPath, source: Source):
        self._uow.execute(qry.UPDATE_ASSET_PATH, asset_path.get_path(), asset_path.get_asset_info_id(), asset_path.get_id())
        if asset_path.get_custom_attribute('source_id') is None:
            self._uow.execute(qry.INSERT_SOURCE_ASSET_PATH, source.get_id(), asset_path.get_id())

    def _update_launchers(self, source_id: str, rom_launchers: typing.List[ROMLauncherAddon]):
        for rom_launcher in rom_launchers:
            if rom_launcher.get_custom_attribute("source_id") is None:
                self._uow.execute(qry.INSERT_SOURCE_LAUNCHER, rom_launcher.get_id(), source_id, rom_launcher.is_default())
            else:
                self._uow.execute(qry.UPDATE_SOURCE_LAUNCHER, rom_launcher.is_default(), source_id, rom_launcher.get_id())


class LaunchersRepository(object):

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self.logger = logging.getLogger(__name__)

    def find(self, id: str) -> ROMLauncherAddon:
        if id is None:
            return None
        
        self._uow.execute(qry.SELECT_LAUNCHER, id)
        result_set = self._uow.single_result()
        addon = AklAddon(result_set.copy())
        
        return ROMLauncherAddon(result_set, addon)
    
    def find_all(self) -> typing.Iterator[ROMLauncherAddon]:
        self._uow.execute(qry.SELECT_LAUNCHERS)
        result_sets = self._uow.result_set()
        
        for result_set in result_sets:
            addon = AklAddon(result_set.copy())
            yield ROMLauncherAddon(result_set, addon)
  
    def insert_launcher(self, launcher: ROMLauncherAddon):
        self.logger.info(f"LaunchersRepository.insert_launcher(): Inserting new launcher '{launcher.get_name()}'")
        addon = launcher.get_addon()
        self._uow.execute(qry.INSERT_LAUNCHER, launcher.get_id(), launcher.get_name(), addon.get_id(), launcher.get_settings_str())
                  
    def update_launcher(self, launcher: ROMLauncherAddon):
        self.logger.info(f"LaunchersRepository.update_launcher(): Updating launcher '{launcher.get_name()}'")
        self._uow.execute(qry.UPDATE_LAUNCHER, launcher.get_name(), launcher.get_settings_str(), launcher.get_id())
        
    def delete_launcher(self, launcher: ROMLauncherAddon):
        self.logger.info(f"LaunchersRepository.delete_launcher(): Deleting source '{launcher.get_id()}'")
        self._uow.execute(qry.DELETE_LAUNCHER, launcher.get_id())
