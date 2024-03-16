import sys
import unittest, os
import unittest.mock
from unittest.mock import patch

import logging

import tests.fake_routing
import tests.fakes

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib.repositories import UnitOfWork
from resources.lib.domain import *
from resources.lib import globals

from resources.lib.commands import addon_commands as target

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)

class Test_cmd_scan_addons(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
        
        logger.info('ROOT DIR: {}'.format(cls.ROOT_DIR))
        logger.info('TEST DIR: {}'.format(cls.TEST_DIR))
        logger.info('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        logger.info('---------------------------------------------------------------------------')
        
        dbPath = io.FileName(os.path.join(cls.TEST_ASSETS_DIR, 'test_db.db'))
        globals.g_PATHS = globals.AKL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_FILE_PATH = dbPath
        
    mocked_addons_collection = {}  
    def mocked_addons(addon_id):
        return Test_cmd_scan_addons.mocked_addons_collection[addon_id]
    
    saved_entities = []
    def repository_save(entity):
        Test_cmd_scan_addons.saved_entities.append(entity)
        
    updated_entities = []
    def repository_update(entity):
        Test_cmd_scan_addons.updated_entities.append(entity)
        
    def repository_empty(): return []
    
    @patch('akl.utils.kodi.translate')
    @patch('xbmcaddon.Addon', side_effect = mocked_addons)
    @patch('resources.lib.repositories.AklAddonRepository.insert_addon', side_effect = repository_save)
    @patch('resources.lib.repositories.AklAddonRepository.update_addon', side_effect = repository_update)
    @patch('resources.lib.repositories.AklAddonRepository.find_all', side_effect = repository_empty)
    @patch('akl.utils.kodi.jsonrpc_query')
    def test_saving_new_addons(self, jsonrpc_response_mock, find_all_mock, repo_update_mock, 
                               repo_save_mock, addon_mock, translate_mock):        
        # arrange
        Test_cmd_scan_addons.mocked_addons_collection = {
            'plugin.mock.A': tests.fakes.FakeAddon({ 'version': '1.2.3', 'akl.enabled': 'true', 'akl.plugin_types': 'SCANNER', 'akl.scanner.friendlyname': 'MockA' }),
            'plugin.mock.B': tests.fakes.FakeAddon({ 'version': '3.3.1', 'akl.enabled': 'false' }),
            'plugin.mock.C': tests.fakes.FakeAddon({ 'version': '6.8.0', 'akl.enabled': 'true', 'akl.plugin_types': 'LAUNCHER', 'akl.launcher.friendlyname': 'MockC'  })
        }
        jsonrpc_response_mock.return_value = {
            'result': { 'addons': [ { 'addonid': 'plugin.mock.A' }, { 'addonid': 'plugin.mock.B' }, { 'addonid': 'plugin.mock.C' } ]}
        }
        
        # act
        target.cmd_scan_addons({})
        # assert
        self.assertEqual(len(Test_cmd_scan_addons.saved_entities), 2)

    def test_enums(self):
        a = constants.AddonType.SCRAPER
        print(str(a))
        print(a.name)
        print(a.value)
        b = constants.AddonType['SCANNER']
        print(str(b))
        print(b.name)
        print(b.value)

        self.assertTrue(b == constants.AddonType.SCANNER)
        
        z = dict()
        z['naam'] = 'piet'
        z['adres'] = 'van "Houten"laan'
        z['pad'] = "c:\\windows\\app"
        
        a = {
            'x': 'xx',
            'y': 'y"y',
            'd': 'd-d\\aap',
            'z': z
        }
        
        astr = json.dumps(a)
        logger.info(astr)
