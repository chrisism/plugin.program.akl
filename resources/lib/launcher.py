#
# Advanced Kodi Launcher: Default launcher implementation
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
import collections

# --- AKL packages ---
from akl import platforms
from akl.utils import io, kodi
from akl.launchers import LauncherABC

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# Default implementation for launching anything ROMs or item based using an application.
# Inherit from this base class to implement your own specific ROM App launcher.
# -------------------------------------------------------------------------------------------------
class AppLauncher(LauncherABC):

    # --------------------------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------------------------
    def get_name(self) -> str:
        return 'App Launcher'
     
    def get_launcher_addon_id(self) -> str:
        addon_id = kodi.get_addon_id()
        return addon_id

    # --------------------------------------------------------------------------------------------
    # Launcher build wizard methods
    # --------------------------------------------------------------------------------------------
    #
    # Creates a new launcher using a wizard of dialogs. Called by parent build() method.
    #
    def _builder_get_wizard(self, wizard):
        wizard = kodi.WizardDialog_DictionarySelection(wizard, 'application', 'Select the way to launch the files', {
            'APP': 'Using a specific application to launch',
            'FILE': 'Directly execute the file itself'})
        wizard = kodi.WizardDialog_FileBrowse(wizard, 'application', 'Select the launcher application',
                                              1, self._builder_get_appbrowser_filter, shares="programs",
                                              conditionalFunction=self._builder_will_launch_through_app)
        wizard = kodi.WizardDialog_Dummy(wizard, 'args', '', self._builder_get_arguments_from_application_path)
        wizard = kodi.WizardDialog_Keyboard(wizard, 'args', 'Application arguments')
        
        return wizard
            
    def _build_post_wizard_hook(self):        
        self.non_blocking = True
        app = self.launcher_settings['application']
        app_FN = io.FileName(app)

        self.launcher_settings['secname'] = app_FN.getBase()
        return True
    
    def _builder_get_arguments_from_application_path(self, input, item_key, launcher_args):
        if input:
            return input
        app = launcher_args['application']
        if app == 'FILE':
            return ''
        
        appPath = io.FileName(app)
        default_arguments = platforms.emudata_get_program_arguments(appPath.getBase())

        return default_arguments

    def _builder_will_launch_through_app(self, item_key, properties) -> bool:
        return properties[item_key] != 'FILE'
        
    def _builder_get_edit_options(self):
        options = super()._builder_get_edit_options()
        options[self._change_application] = 'Change application ({})'.format(self.launcher_settings['application'])
        options[self._change_launcher_arguments] = "Modify Arguments: '{0}'".format(self.launcher_settings['args'])
        return options

    def _change_application(self):
        current_application = self.launcher_settings['application']
        
        options = collections.OrderedDict()
        options['APP'] = 'Using a specific application to launch'
        options['FILE'] = 'Directly execute the file itself'
        
        preselected = current_application if current_application == 'FILE' else 'APP'
        selected_option = kodi.OrdDictionaryDialog().select('Select the way to launch the files', options, preselected)
        
        if selected_option == 'APP':
            selected_application = kodi.browse(1, 'Select the launcher application', 'files',
                                               '', False, False, current_application)
            if selected_application is None or selected_application == current_application:
                return
        else:
            selected_application = selected_option
        
        self.launcher_settings['application'] = selected_application

    def _change_launcher_arguments(self):
        args = self.launcher_settings['args']
        args = kodi.dialog_keyboard('Edit application arguments', text=args)

        if args is None:
            return
        self.launcher_settings['args'] = args

    # ---------------------------------------------------------------------------------------------
    # Execution methods
    # ---------------------------------------------------------------------------------------------
    def get_application(self) -> str:
        if 'application' not in self.launcher_settings:
            logger.error('LauncherABC::launch() No application argument defined')
            return None
        
        if self.launcher_settings['application'] == 'FILE':
            return "$ROM$"
        
        application = io.FileName(self.launcher_settings['application'])
        
        # --- Check for errors and abort if errors found ---
        if not application.exists():
            logger.error('Launching app not found "{0}"'.format(application.getPath()))
            kodi.notify_warn('App {0} not found.'.format(application.getPath()))
            return None
        
        return application.getPath()
