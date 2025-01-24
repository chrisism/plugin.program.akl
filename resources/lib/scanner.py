# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Default scanner implementation
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
import re
import collections

# --- AKL packages ---
from akl import report, api
from akl.utils import io, kodi

from akl.scanners import RomScannerStrategy, ROMCandidateABC, MultiDiscInfo

logger = logging.getLogger(__name__)


class ROMFileCandidate(ROMCandidateABC):
    
    def __init__(self, file: io.FileName):
        self.file = file
        super(ROMFileCandidate, self).__init__()
        
    def get_ROM(self) -> api.ROMObj:
        rom = api.ROMObj()
        scanned_data = {
            'file': self.file.getPath(),
            'identifier': self.file.getBaseNoExt()
        }
        rom.set_name(self.file.getBaseNoExt())
        rom.set_scanned_data(scanned_data)
        return rom
        
    def get_sort_value(self):
        return self.file.getBase()


class RomFolderScanner(RomScannerStrategy):
    
    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str:
        return 'Folder scanner'
    
    def get_scanner_addon_id(self) -> str:
        addon_id = kodi.get_addon_id()
        return addon_id

    def get_rom_path(self) -> io.FileName:
        str_rom_path = self.scanner_settings['rompath'] if 'rompath' in self.scanner_settings else None
        if str_rom_path is None:
            return io.FileName("/")
        return io.FileName(str_rom_path)

    def get_rom_extensions(self) -> list:
        if 'romext' not in self.scanner_settings:
            return []
        return self.scanner_settings['romext'].split("|")
    
    def scan_recursive(self) -> bool:
        return self.scanner_settings['scan_recursive'] if 'scan_recursive' in self.scanner_settings else False
    
    def ignore_bios(self) -> bool:
        return self.scanner_settings['ignore_bios'] if 'ignore_bios' in self.scanner_settings else True
    
    def supports_multidisc(self) -> bool:
        return self.scanner_settings['multidisc'] if 'multidisc' in self.scanner_settings else False

    def _configure_get_wizard(self, wizard) -> kodi.WizardDialog:
        
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'rompath', 'Select the ROMs path', 0, '')
        wizard = kodi.WizardDialog_YesNo(wizard, 'scan_recursive', 'Scan recursive', 'Scan through this directory and any subdirectories?')
        wizard = kodi.WizardDialog_Dummy(wizard, 'romext', '', self.configuration_get_extensions_from_launchers)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'romext', 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
        wizard = kodi.WizardDialog_YesNo(wizard, 'multidisc',
                                         'Supports multi-disc ROMs?', 'Does this source contain multi-disc ROMS?')
        wizard = kodi.WizardDialog_YesNo(wizard, 'ignore_bios', 'Ignore BIOS', 'Ignore any BIOS file found during scanning?')
        
        return wizard
      
    def _configure_post_wizard_hook(self):
        path = self.scanner_settings['rompath'] if 'rompath' in self.scanner_settings else None
        self.scanner_settings['secname'] = path
        return True

    def _configure_get_edit_options(self) -> dict:
        recursive_scan_str = 'ON' if self.scanner_settings['scan_recursive'] else 'OFF'
        multidisc_str = 'ON' if self.scanner_settings['multidisc'] else 'OFF'
        bios_str = 'ON' if self.scanner_settings['ignore_bios'] else 'OFF'

        options = collections.OrderedDict()
        options[self._change_rompath] = 'Change ROMs path ({})'.format(self.scanner_settings['rompath'])
        options[self._change_rom_ext] = "Modify ROM extensions: '{0}'".format(self.scanner_settings['romext'])
        options[self._change_recursive_scan] = "Recursive scan: '{0}'".format(recursive_scan_str)
        options[self._change_multidisc] = "Multidisc ROM support (now {0})".format(multidisc_str)
        options[self._change_ignore_bios] = "Ignore any BIOS file (now {0})".format(bios_str)

        return options

    def _change_rompath(self):
        current_path = self.scanner_settings['rompath']
        selected_path = kodi.browse(0, 'Select Files path', 'files', preselected_path=current_path)

        if selected_path is None or selected_path == current_path:
            return
        
        self.scanner_settings['rompath'] = selected_path

    def _change_rom_ext(self):
        exts = self.scanner_settings['romext']
        exts = kodi.dialog_keyboard('Edit ROM extensions, use "|" as separator. (e.g lnk|cbr)', text=exts)

        if exts is None:
            return
        self.scanner_settings['romext'] = exts

    def _change_recursive_scan(self):
        current_state = self.scanner_settings['scan_recursive']
        self.scanner_settings['scan_recursive'] = not current_state

    def _change_multidisc(self):
        current_state = self.scanner_settings['multidisc']
        self.scanner_settings['multidisc'] = not current_state

    def _change_ignore_bios(self):
        current_state = self.scanner_settings['ignore_bios']
        self.scanner_settings['ignore_bios'] = not current_state

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _getCandidates(self, launcher_report: report.Reporter) -> typing.List[ROMCandidateABC]:
        self.progress_dialog.startProgress('Scanning and caching files in ROM path ...')
        files = []
        
        rom_path = self.get_rom_path()
        self.progress_dialog.updateProgress(2)
        launcher_report.write('Scanning files in {}'.format(rom_path.getPath()))

        if self.scan_recursive():
            logger.info('Recursive scan activated')
            files = rom_path.recursiveScanFilesInPath('*.*',
                                                      self.progress_dialog.setSteps,
                                                      self.progress_dialog.incrementStep)
        else:
            logger.info('Recursive scan not activated')
            files = rom_path.scanFilesInPath('*.*',
                                             self.progress_dialog.setSteps,
                                             self.progress_dialog.incrementStep)
        
        num_files = len(files)
        launcher_report.write('  File scanner found {} files'.format(num_files))
        self.progress_dialog.endProgress()
        
        return [*(ROMFileCandidate(f) for f in files)]

    # --- Get dead entries -----------------------------------------------------------------
    def _getDeadRoms(self, candidates: typing.List[ROMCandidateABC], roms: typing.List[api.ROMObj]) -> typing.List[api.ROMObj]:
        dead_roms = []
        num_roms = len(roms)
        if num_roms == 0:
            logger.info('Source is empty. No dead ROM check.')
            return dead_roms
        
        logger.info('Starting dead items scan')
        i = 0
            
        self.progress_dialog.startProgress('Checking for dead ROMs ...', num_roms)
        for rom in reversed(roms):
            fileName = rom.get_scanned_data_element_as_file('file')
            logger.info(f'Searching {fileName.getPath()}')
            self.progress_dialog.updateProgress(i)
            
            if not fileName.exists():
                logger.info(f'Not found. Marking as dead: {fileName.getPath()}')
                roms.remove(rom)
                dead_roms.append(rom)
            i += 1
            
        self.progress_dialog.endProgress()
        return dead_roms

    # ~~~ Now go processing item by item ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _processFoundItems(self,
                           candidates: typing.List[ROMCandidateABC],
                           roms: typing.List[api.ROMObj],
                           launcher_report: report.Reporter) -> typing.List[api.ROMObj]:

        num_items = len(candidates)
        new_roms: typing.List[api.ROMObj] = []

        self.progress_dialog.startProgress('Scanning found items', num_items)
        logger.debug('============================== Processing ROMs ==============================')
        launcher_report.write('Processing files ...')
        num_items_checked = 0
        
        allowedExtensions = self.get_rom_extensions()
        scanner_multidisc = self.supports_multidisc()

        for candidate in sorted(candidates, key=lambda c: c.get_sort_value()):
            file_candidate: ROMFileCandidate = candidate
            ROM_file = file_candidate.file
            
            self.progress_dialog.updateProgress(num_items_checked)
            
            # --- Get all file name combinations ---
            launcher_report.write(f'>>> {ROM_file.getPath()}')

            # ~~~ Update progress dialog ~~~
            file_text = f'ROM {ROM_file.getBase()}'
            self.progress_dialog.updateMessage(f'{file_text}\nChecking if has ROM extension ...')
                        
            # --- Check if filename matchs ROM extensions ---
            # The recursive scan has scanned all files. Check if this file matches some of
            # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
            processROM = False

            for ext in allowedExtensions:
                if ROM_file.getExt() == '.' + ext:
                    launcher_report.write("  Expected '{0}' extension detected".format(ext))
                    processROM = True
                    break

            if not processROM:
                launcher_report.write('  File has not an expected extension. Skipping file.')
                continue
                        
            # --- Check if ROM belongs to a multidisc set ---
            self.progress_dialog.updateMessage('{}\nChecking if ROM belongs to multidisc set..'.format(file_text))
                       
            MultiDiscInROMs = False
            MDSet = MultiDiscInfo.get_multidisc_info(ROM_file)
            if MDSet.isMultiDisc and scanner_multidisc:
                logger.info('ROM belongs to a multidisc set.')
                logger.info('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                logger.info('setName     "{0}"'.format(MDSet.setName))
                logger.info('discName    "{0}"'.format(MDSet.discName))
                logger.info('extension   "{0}"'.format(MDSet.extension))
                logger.info('order       "{0}"'.format(MDSet.order))
                launcher_report.write('  ROM belongs to a multidisc set.')
                
                # >> Check if the set is already in launcher ROMs.
                for new_rom in new_roms:
                    temp_FN = new_rom.get_scanned_data_element_as_file('file')
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs = True
                        MultiDisc_rom = new_rom
                        break

                logger.info('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    logger.info('First ROM in the set. Adding to ROMs ...')
                    # >> Manipulate ROM so filename is the name of the set
                    ROM_dir = io.FileName(ROM_file.getDir())
                    # ROM_file_original = ROM_file
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    logger.info('ROM_temp P "{0}"'.format(ROM_temp.getPath()))
                    ROM_file = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    logger.info('Adding additional disk "{0}"'.format(MDSet.discName))
                    MultiDisc_rom.add_disk(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...
                    
                    # >> Process next file
                    logger.info('Processing next file ...')
                    continue
            elif MDSet.isMultiDisc and not scanner_multidisc:
                launcher_report.write('  ROM belongs to a multidisc set but Multidisc support is disabled.')
            else:
                launcher_report.write('  ROM does not belong to a multidisc set.')
 
            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            self.progress_dialog.updateMessage('{}\nChecking if ROM is not already in source...'.format(file_text))
            repeatedROM = False
            for rom in roms:
                rpath = rom.get_scanned_data_element_as_file('file')
                if rpath == ROM_file:
                    repeatedROM = True
        
            if repeatedROM:
                launcher_report.write('  File already into ROM list. Skipping file.')
                continue
            else:
                launcher_report.write('  File not in ROM list. Processing it ...')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.ignore_bios:
                BIOS_re = re.findall(r'\[BIOS\]', ROM_file.getBase())
                if len(BIOS_re) > 0:
                    logger.info(f"BIOS detected. Skipping ROM '{ROM_file.getPath()}'")
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            # --- Create new rom dictionary ---
            # >> Database always stores the original (non transformed/manipulated) path
            new_rom = file_candidate.get_ROM()
            new_roms.append(new_rom)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self.progress_dialog.isCanceled():
                self.progress_dialog.endProgress()
                kodi.dialog_OK('Stopping ROM scanning. No changes have been made.')
                logger.info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return None
            
            num_items_checked += 1
           
        self.progress_dialog.endProgress()
        return new_roms
