import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from tests.fakes import FakeFile, FakeExecutor, random_string

from resources.lib.launcher import AppLauncher
from akl.launchers import ExecutionSettings
from akl.api import ROMObj

class Test_Launcher(unittest.TestCase):
    
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

    # todo: Move to repository tests
    #def test_when_creating_a_launcher_with_not_exisiting_id_it_will_fail(self):
    #    # arrange
    #    launcher_data = {'id': 'aap'}
    #    plugin_dir = FakeFile(self.TEST_ASSETS_DIR)
    #    settings = self._get_test_settings()
    #    
    #    # act
    #    factory = AELObjectFactory(Fake_Paths(self.TEST_ASSETS_DIR), settings, None, None)
    #    #LauncherFactory(None, None, plugin_dir)
    #    actual = factory.create_from_dic(launcher_data)
    #    
    #    # assert
    #    self.assertIsNone(actual)
                
    @patch('akl.launchers.kodi', autospec=True)
    @patch('akl.utils.io.FileName', side_effect = FakeFile)
    @patch('akl.api.client_get_rom')
    @patch('akl.api.client_get_launcher_settings')
    @patch('akl.executors.ExecutorFactory')
    def test_if_app_launcher_will_correctly_passthrough_parameters_when_launching(self, 
            factory_mock:MagicMock, api_settings_mock:MagicMock, api_rom_mock: MagicMock, filename_mock, kodi_mock):
       
        # arrange
        expectedApp  = random_string(52)
        expectedArgs = random_string(25)

        launcher_id     = random_string(10)
        collection_id   = random_string(10)
        rom_id          = random_string(10)
        
        mock = FakeExecutor()
        factory_mock.create.return_value = mock
        
        launcher_settings = {}
        launcher_settings['id'] = 'ABC'
        launcher_settings['application'] = expectedApp
        launcher_settings['toggle_window'] = True
        launcher_settings['args'] = expectedArgs
        launcher_settings['m_name'] = 'MyApp'
        api_settings_mock.return_value = launcher_settings

        expected_rom = ROMObj({
            'id': rom_id,
            'm_name': random_string(22)
        })
        api_rom_mock.return_value = expected_rom

        # act
        target = AppLauncher(launcher_id, None, 'localhost', 8080, factory_mock, ExecutionSettings())
        target.launch()

        # assert
        self.assertIsNotNone(mock.actualApplication)
        self.assertEqual(expectedApp, mock.actualApplication)        
        self.assertIsNotNone(mock.actualArgs)
        self.assertEqual(expectedArgs, mock.actualArgs[0])
        
    @patch('akl.launchers.kodi', autospec=True)
    @patch('akl.utils.io.FileName', side_effect = FakeFile)
    @patch('akl.api.client_get_rom')
    @patch('akl.api.client_get_launcher_settings')
    @patch('akl.executors.ExecutorFactory')    
    def test_if_app_launcher_will_correctly_alter_arguments_when_launching(self, 
            factory_mock:MagicMock, api_settings_mock:MagicMock, api_rom_mock: MagicMock, filename_mock, kodi_mock):

        # arrange
        expectedApp = '/Sparta/Action.exe'
        expectedArgs = 'this is /Sparta/'

        launcher_settings = {}
        launcher_settings['id'] = 'ABC'
        launcher_settings['type'] = 'STANDALONE'
        launcher_settings['application'] = expectedApp
        launcher_settings['toggle_window'] = True
        launcher_settings['args'] = 'this is $apppath$'
        launcher_settings['m_name'] = 'MyApp'
        launcher_settings['display_launcher_notify'] = False
        api_settings_mock.return_value = launcher_settings
        
        launcher_id = random_string(10)
        rom_id = random_string(10)

        expected_rom = ROMObj({
            'id': rom_id,
            'm_name': random_string(22)
        })
        api_rom_mock.return_value = expected_rom
        
        mock = FakeExecutor()
        factory_mock.create.return_value = mock

        # act
        target = AppLauncher(launcher_id, None, 'localhost', 8080, factory_mock, ExecutionSettings())
        target.launch()

        # assert
        self.assertIsNotNone(mock.actualApplication)
        self.assertEqual(expectedApp, mock.actualApplication)        
        self.assertIsNotNone(mock.actualArgs)
        self.assertEqual(expectedArgs, ' '.join(mock.actualArgs))
                          
    @patch('akl.launchers.kodi', autospec=True)
    @patch('akl.utils.io.FileName', side_effect = FakeFile)
    @patch('akl.api.client_get_rom')
    @patch('akl.api.client_get_launcher_settings')
    @patch('akl.executors.ExecutorFactory')    
    def test_if_rom_launcher_will_correctly_passthrough_the_application_when_launching(self, 
            factory_mock:MagicMock, api_settings_mock:MagicMock, api_rom_mock: MagicMock, filename_mock, kodi_mock):
        
        # arrange
        expected = random_string(55)
        expectedArgs = '-a -b -c -d -e testing.zip -yes'

        launcher_settings= {}
        launcher_settings['id'] = 'ABC'
        launcher_settings['application'] = expected
        launcher_settings['toggle_window'] = True
        launcher_settings['romext'] = ''
        launcher_settings['args'] = '-a -b -c -d -e $rom$ -yes'
        launcher_settings['args_extra'] = ''
        launcher_settings['roms_base_noext'] = 'snes'
        api_settings_mock.return_value = launcher_settings
        
        launcher_id = random_string(10)
        rom_id = random_string(10)
        
        expected_rom = ROMObj({ 'id': rom_id, 'm_name': 'TestCase', 'scanned_data': {'file':'testing.zip'}, 'altapp': '', 'altarg': '' })
        api_rom_mock.return_value = expected_rom
                
        mock = FakeExecutor()
        factory_mock.create.return_value = mock

        # act
        target = AppLauncher(launcher_id, None, 'localhost', 8080, factory_mock, ExecutionSettings())
        target.launch()       

        # assert
        expectedArgsArray = expectedArgs.split(" ")

        self.assertIsNotNone(mock.actualApplication)
        self.assertEqual(expected, mock.actualApplication)
        self.assertEqual(len(expectedArgsArray), len(mock.actualArgs))
        self.assertEqual(expectedArgsArray[0], mock.actualArgs[0])
        self.assertEqual(expectedArgsArray[1], mock.actualArgs[1])
        self.assertEqual(expectedArgsArray[2], mock.actualArgs[2])
        self.assertEqual(expectedArgsArray[3], mock.actualArgs[3])
                
    # @patch('resources.objects.FileName', side_effect = FakeFile)
    # @patch('resources.objects.ExecutorFactory')
    # def test_if_rom_launcher_will_use_the_multidisk_launcher_when_romdata_has_disks_field_filled_in(self, mock_exeFactory, mock_file):
        
    #     # arrange
    #     settings = self._get_test_settings()

    #     launcher_data = {}
    #     launcher_data['id'] = 'ABC'
    #     launcher_data['type'] = OBJ_LAUNCHER_ROM
    #     launcher_data['application'] = 'path'
    #     launcher_data['toggle_window'] = True
    #     launcher_data['romext'] = ''
    #     launcher_data['application'] = ''
    #     launcher_data['args'] = ''
    #     launcher_data['args_extra'] = ''
    #     launcher_data['roms_base_noext'] = 'snes'
        
    #     rom_id = 'fghj'
    #     rom = { 'id': rom_id, 'm_name': 'TestCase', 'disks':['disc01.zip', 'disc02.zip'] }
    #     roms = { rom_id: rom }
    #     json_data = json.dumps(roms, ensure_ascii = False, indent = 1, separators = (',', ':'))
        
    #     rom_dir = FakeFile(self.TEST_ASSETS_DIR)
    #     rom_dir.setFakeContent(json_data)

    #     mock = FakeExecutor()
    #     mock_exeFactory.create.return_value = mock

    #     paths = Fake_Paths('\\fake\\')
    #     paths.ROMS_DIR = rom_dir
        
    #     repository = ROMCollectionRepository(paths, settings)
    #     launcher = StandardRomLauncher(paths, settings, launcher_data, None, mock_exeFactory, repository, None)
        
    #     # act
    #     launcher.select_ROM(rom_id)
        
    #     # assert        
    #     actual = launcher.__class__.__name__
    #     expected = 'StandardRomLauncher'
    #     assert actual == expected
                
    # @patch('resources.objects.FileName', side_effect = FakeFile)
    # @patch('resources.objects.xbmcgui.Dialog.select')
    # @patch('resources.objects.ExecutorFactory')
    # def test_if_rom_launcher_will_apply_the_correct_disc_in_a_multidisc_situation(self, mock_exeFactory, mock_dialog, mock_file):

    #     # arrange
    #     settings = self._get_test_settings()

    #     launcher_data = {}
    #     launcher_data['id'] = 'ABC'
    #     launcher_data['type'] = OBJ_LAUNCHER_ROM
    #     launcher_data['application'] = 'c:\\temp\\'
    #     launcher_data['toggle_window'] = True
    #     launcher_data['romext'] = ''
    #     launcher_data['application'] = ''
    #     launcher_data['args'] = '-a -b -c -d -e $rom$ -yes'
    #     launcher_data['args_extra'] = ''
    #     launcher_data['roms_base_noext'] = 'snes'

    #     rom = {}
    #     rom['id'] = 'qqqq'
    #     rom['m_name'] = 'TestCase'
    #     rom['filename'] = 'd:\\games\\discXX.zip'
    #     rom['altapp'] = ''
    #     rom['altarg'] = ''
    #     rom['disks'] = ['disc01.zip', 'disc02.zip']
        
    #     rom_id = rom['id']
    #     roms = { rom_id: rom }
    #     json_data = json.dumps(roms, ensure_ascii = False, indent = 1, separators = (',', ':'))
        
    #     rom_dir = FakeFile(self.TEST_ASSETS_DIR)
    #     rom_dir.setFakeContent(json_data)

    #     mock_dialog.return_value = 1
    #     mock = FakeExecutor()
    #     mock_exeFactory.create.return_value = mock
        
    #     paths = Fake_Paths('\\fake\\')
    #     paths.ROMS_DIR = rom_dir
        
    #     repository = ROMCollectionRepository(paths, settings)
    #     launcher = StandardRomLauncher(paths, settings, launcher_data, None, mock_exeFactory, repository, None)
    #     launcher.select_ROM(rom_id)

    #     expected = launcher_data['application']
    #     expectedArgs = '-a -b -c -d -e d:\\games\\disc02.zip -yes'

    #     # act
    #     launcher.launch()

    #     # assert
    #     self.assertEqual(expectedArgs, mock.actualArgs)

if __name__ == '__main__':
   unittest.main()
