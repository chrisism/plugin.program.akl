import sys
import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging
from distutils.version import LooseVersion

import tests.fake_routing
from tests.fakes import FakeFile, FakeUnitOfWork

module = type(sys)('routing')
module.Plugin = tests.fake_routing.Plugin
sys.modules['routing'] = module

from resources.lib import globals
from resources.lib.services import AppService
from resources.lib.repositories import UnitOfWork

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)

class Test_services(unittest.TestCase):
    
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
        
        globals.g_PATHS = globals.AKL_Paths('plugin.tests')
        globals.g_PATHS.DATABASE_MIGRATIONS_PATH = FakeFile('db')
        
    @patch('resources.lib.services.globals.g_bootstrap_instances', autospec=True)
    @patch('akl.utils.io.FileName.scanFilesInPath')
    def test_version_compare(self, file_mock:MagicMock, globals_mock):  
        # arrange
        file_mock.return_value = [
            FakeFile('1.2.1.sql'),
            FakeFile('1.1.0.sql'), 
            FakeFile('1.3.0_004.sql'),
            FakeFile('1.3.0_001.sql'),
            FakeFile('1.3.0_002.sql'),
            FakeFile('/files/1.3.0.sql'),
            FakeFile('1.1.5.sql'),
            FakeFile('1.1.5_002.sql'),
            FakeFile('/migrations/with/1.2.7.sql')
        ]
        
        a = LooseVersion('1.5.0~rc4') 
        b = LooseVersion('1.5.0~rc7')
        
        c = a < b
        self.assertTrue(c)
        
        target = UnitOfWork(FakeFile("/x.db"))
        start_version = LooseVersion('1.1.1')
        globals.addon_version = '1.0.0'
        
        # act
        actual = target.get_migration_files(start_version)
        
        # assert
        self.assertIsNotNone(actual)
        self.assertEqual(actual[0].getPath(), '1.1.5.sql')
        self.assertEqual(actual[1].getPath(), '1.1.5_002.sql')
        self.assertEqual(actual[2].getPath(), '1.2.1.sql')
        self.assertEqual(actual[3].getPath(), '/migrations/with/1.2.7.sql')
        self.assertEqual(actual[4].getPath(), '/files/1.3.0.sql')
        self.assertEqual(actual[5].getPath(), '1.3.0_001.sql')
        self.assertEqual(actual[6].getPath(), '1.3.0_002.sql')
        self.assertEqual(actual[7].getPath(), '1.3.0_004.sql')
