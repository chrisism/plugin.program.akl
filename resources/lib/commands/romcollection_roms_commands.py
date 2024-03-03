# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher: Commands (romcollection roms management)
#
# Copyright (c) Wintermute0110 <wintermute0110@gmail.com> / Chrisism <crizizz@gmail.com>
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

from akl import constants
from akl.utils import kodi

from resources.lib.commands.mediator import AppMediator
from resources.lib import globals
from resources.lib.repositories import UnitOfWork, ROMCollectionRepository, ROMsRepository, SourcesRepository
from resources.lib.domain import g_assetFactory, RuleSet, Rule, ROM, RuleOperator

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------------
# ROMCollection ROM management.
# -------------------------------------------------------------------------------------------------

# --- Submenu menu command ---
@AppMediator.register('ROMCOLLECTION_MANAGE_ROMS')
def cmd_manage_roms(args):
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() SHOW MENU')
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    if romcollection_id is None:
        logger.warning('cmd_manage_roms(): No romcollection id supplied.')
        kodi.notify_warn(kodi.translate(40951))
        return
    
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

    has_roms = romcollection.has_roms()

    options = collections.OrderedDict()
    options['SET_ROMS_DEFAULT_ARTWORK'] = kodi.translate(42044)
    options['IMPORT_ROMS'] = kodi.translate(42082)
    if has_roms:
        options['SCRAPE_ROMS'] = kodi.translate(42052)
        options['CLEAR_ROMS'] = kodi.translate(42054)

    s = kodi.translate(41128).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected None. Closing context menu')
        if 'scraper_settings' in args:
            del args['scraper_settings']
        AppMediator.async_cmd('EDIT_ROMCOLLECTION', args)
        return
    
    # >> Execute subcommand. May be atomic, maybe a submenu.
    logger.debug('ROMCOLLECTION_MANAGE_ROMS: cmd_manage_roms() Selected {}'.format(selected_option))
    AppMediator.async_cmd(selected_option, args)


# --- Choose default ROMs assets/artwork ---
@AppMediator.register('SET_ROMS_DEFAULT_ARTWORK')
def cmd_set_roms_default_artwork(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        # --- Build Dialog.select() list ---
        default_assets_list = romcollection.get_ROM_mappable_asset_list()
        options = collections.OrderedDict()
        for default_asset_info in default_assets_list:
            # >> Label is the string 'Choose asset for XXXX (currently YYYYY)'
            mapped_asset_info = romcollection.get_ROM_asset_mapping(default_asset_info)
            # --- Append to list of ListItems ---
            options[default_asset_info] = kodi.translate(42055).format(
                kodi.translate(default_asset_info.name_id),
                kodi.translate(mapped_asset_info.name_id))
        
        dialog = kodi.OrdDictionaryDialog()
        selected_asset_info = dialog.select(kodi.translate(41077).format("ROM"), options)
        
        if selected_asset_info is None:
            # >> Return to parent menu.
            logger.debug('Main selected NONE. Returning to parent menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return
        
        logger.debug(f'Main select() returned {selected_asset_info.name}')
        mapped_asset_info = romcollection.get_ROM_asset_mapping(selected_asset_info)
        mappable_asset_list = g_assetFactory.get_asset_list_by_IDs(constants.ROM_ASSET_ID_LIST, 'image')
        logger.debug(f'{selected_asset_info.name} currently is mapped to {mapped_asset_info.name}')
            
        # --- Create ListItems ---
        options = collections.OrderedDict()
        for mappable_asset_info in mappable_asset_list:
            # >> Label is the asset name (Icon, Fanart, etc.)
            options[mappable_asset_info] = kodi.translate(mappable_asset_info.name_id)

        dialog = kodi.OrdDictionaryDialog()
        dialog_title_str = kodi.translate(41078).format(romcollection.get_object_name(),
                                                        kodi.translate(selected_asset_info.name_id))
        new_selected_asset_info = dialog.select(dialog_title_str, options, mapped_asset_info)
    
        if new_selected_asset_info is None:
            # >> Return to this method recursively to previous menu.
            logger.debug('Mapable selected NONE. Returning to previous menu.')
            AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
            return
        
        logger.debug(f'Mapable selected {new_selected_asset_info.name}.')
        romcollection.set_mapped_ROM_asset(selected_asset_info, new_selected_asset_info)
        kodi.notify(kodi.translate(40983).format(
            romcollection.get_object_name(),
            kodi.translate(selected_asset_info.name_id),
            kodi.translate(new_selected_asset_info.name_id)
        ))
        
        repository.update_romcollection(romcollection)
        uow.commit()
        AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection.get_id()})
        AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})

    AppMediator.async_cmd('SET_ROMS_DEFAULT_ARTWORK', {
        'romcollection_id': romcollection.get_id(),
        'selected_asset': selected_asset_info.id})


@AppMediator.register('IMPORT_ROMS')
def cmd_import_roms(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    selected_option = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)
        import_rules = repository.find_import_rules_by_collection(romcollection)

        options = collections.OrderedDict()
        for import_rule in import_rules:
            options[import_rule.get_ruleset_id()] = kodi.get_listitem(
                label=kodi.translate(41174).format(import_rule.get_source_name()),
                label2=f"{import_rule.get_rules_description()}",
                art={'icon': 'DefaultPlaylist.png'})

        options['NEW_IMPORT_RULESET'] = kodi.get_listitem(label=kodi.translate(40921), label2='',
                                                          art={'icon': 'DefaultAddSource.png'})

    s = kodi.translate(41130).format(romcollection.get_name())
    selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
    if selected_option is None:
        # >> Exits context menu
        logger.debug('IMPORT_ROMS: Selected None. Closing context menu')
        AppMediator.async_cmd('ROMCOLLECTION_MANAGE_ROMS', args)
        return
    
    if selected_option == 'NEW_IMPORT_RULESET':
        AppMediator.async_cmd(selected_option, args)
        return
    
    logger.debug(f'IMPORT_ROMS: Selected set {selected_option}')
    args['ruleset_id'] = selected_option
    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)


@AppMediator.register('NEW_IMPORT_RULESET')
def cmd_new_import_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
        
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        romcollection = repository.find_romcollection(romcollection_id)

        selected_source = _select_source_for_rules(uow)
        if selected_source is None:
            # >> Exits context menu
            logger.debug('NEW_IMPORT_RULESET: No source selected. Closing context menu')
            AppMediator.async_cmd('IMPORT_ROMS', args)
            return
        
        logger.debug(f'NEW_IMPORT_RULESET: Selected source {selected_source.get_id()}')
        
        ruleset = RuleSet()
        ruleset.apply_source(selected_source)
        
        repository.add_ruleset_to_romcollection(romcollection.get_id(), ruleset)
        uow.commit()
        
    args['ruleset_id'] = ruleset.get_ruleset_id()
    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)


@AppMediator.register('EDIT_IMPORT_RULESET')
def cmd_edit_import_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    ruleset_id: str = args['ruleset_id'] if 'ruleset_id' in args else None
        
    selected_option = None
    next_command = None
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        ruleset = repository.find_ruleset(romcollection_id, ruleset_id)
        
        options = collections.OrderedDict()
        options["EXECUTE_RULESET"] = kodi.get_listitem(kodi.translate(42089), "",
                                                       art={'icon': 'DefaultAddonsUpdates.png'})
        options["SET_RULESET_SOURCE"] = kodi.get_listitem(kodi.translate(42506), ruleset.get_source_name(),
                                                          art={'icon': 'DefaultPlaylist.png'})
        options["CHANGE_RULESET_OPERATOR"] = kodi.get_listitem(kodi.translate(41060), ruleset.get_set_operator_str(),
                                                               art={'icon': 'DefaultMimetypeInfo.png'})
        for rule in ruleset.get_rules():
            options[rule.get_id()] = kodi.get_listitem(kodi.translate(42511), rule.get_description(),
                                                       art={'icon': 'DefaultScript.png'})
        options["ADD_RULE_TO_RULESET"] = kodi.get_listitem(label=kodi.translate(42086), label2='',
                                                           art={'icon': 'DefaultAddSource.png'})
        if ruleset.has_rules():
            options["REMOVE_ALL_RULES"] = kodi.get_listitem(kodi.translate(41173), kodi.translate(41189).format(
                                                            ruleset.get_rules_shortdescription()))

        s = kodi.translate(41184)
        selected_option = kodi.OrdDictionaryDialog().select(s, options, use_details=True)
        if selected_option is None:
            # >> Exits context menu
            logger.debug('EDIT_IMPORT_RULESET: No action selected. Closing context menu')
            args.pop('ruleset_id')
            next_command = 'IMPORT_ROMS'
            return
        
        elif selected_option == 'SET_RULESET_SOURCE':
            source = _select_source_for_rules(uow)
            if source:
                ruleset.apply_source(source)
                repository.update_ruleset_in_romcollection(romcollection_id, ruleset)
                uow.commit()
            next_command = 'EDIT_IMPORT_RULESET'

        elif selected_option == 'CHANGE_RULESET_OPERATOR':
            ruleset.change_operator()
            repository.update_ruleset_in_romcollection(romcollection_id, ruleset)
            uow.commit()
            kodi.notify(kodi.translate(41180))
            next_command = 'EDIT_IMPORT_RULESET'

        elif selected_option == 'REMOVE_ALL_RULES':
            if kodi.dialog_yesno(kodi.translate(41175)):
                ruleset.clear_rules()
                repository.delete_all_rules_from_ruleset(ruleset)
                uow.commit()
                kodi.notify(kodi.translate(41176))
            next_command = 'EDIT_IMPORT_RULESET'
                    
        elif selected_option == 'EXECUTE_RULESET' or selected_option == 'ADD_RULE_TO_RULESET':
            next_command = selected_option
            
        else:
            args['rule_id'] = selected_option
            next_command = 'EDIT_RULE'
        
    AppMediator.sync_cmd(next_command, args)


@AppMediator.register('ADD_RULE_TO_RULESET')
def cmd_add_rule_to_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    ruleset_id: str = args['ruleset_id'] if 'ruleset_id' in args else None
    
    field_options = collections.OrderedDict()
    fields = ROM.get_fields_with_translations()
    for fieldkey, fieldname in fields.items():
        field_options[fieldkey] = kodi.translate(fieldname)
    
    operator_options = collections.OrderedDict()
    operator_options[RuleOperator.Equals] = kodi.translate(30918)
    operator_options[RuleOperator.NotEquals] = kodi.translate(30919)
    operator_options[RuleOperator.Contains] = kodi.translate(30920)
    operator_options[RuleOperator.DoesNotContain] = kodi.translate(30921)
    operator_options[RuleOperator.MoreThan] = kodi.translate(30922)
    operator_options[RuleOperator.LessThan] = kodi.translate(30923)

    wizard = kodi.WizardDialog_DictionarySelection(None, 'property', kodi.translate(41177), field_options)
    wizard = kodi.WizardDialog_DictionarySelection(wizard, 'operator', kodi.translate(41178), operator_options)
    wizard = kodi.WizardDialog_Keyboard(wizard, 'value', kodi.translate(41179))
        
    rule = Rule()
    rule.set_ruleset(ruleset_id)
    
    entity_data = rule.get_data_dic()
    entity_data = wizard.runWizard(entity_data)
    if entity_data is None:
        AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
        return
        
    rule.import_data_dic(entity_data)
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        ruleset = repository.find_ruleset(romcollection_id, ruleset_id)
        
        ruleset.add_rule(rule)
        repository.update_ruleset_in_romcollection(romcollection_id, ruleset)
        uow.commit()

    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
    kodi.notify(kodi.translate(41180))


@AppMediator.register('EDIT_RULE')
def cmd_edit_rule(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    ruleset_id: str = args['ruleset_id'] if 'ruleset_id' in args else None
    rule_id: str = args['rule_id'] if 'rule_id' in args else None

    dialog = kodi.ListDialog()
    selected_action = dialog.select(kodi.translate(41182), [
        kodi.translate('42087'),
        kodi.translate('42088')
    ])
        
    field_options = collections.OrderedDict()
    fields = ROM.get_fields_with_translations()
    for fieldkey, fieldname in fields.items():
        field_options[fieldkey] = kodi.translate(fieldname)
    
    operator_options = collections.OrderedDict()
    operator_options[RuleOperator.Equals] = kodi.translate(30918)
    operator_options[RuleOperator.NotEquals] = kodi.translate(30919)
    operator_options[RuleOperator.Contains] = kodi.translate(30920)
    operator_options[RuleOperator.DoesNotContain] = kodi.translate(30921)
    operator_options[RuleOperator.MoreThan] = kodi.translate(30922)
    operator_options[RuleOperator.LessThan] = kodi.translate(30923)

    wizard = kodi.WizardDialog_DictionarySelection(None, 'property', kodi.translate(41177), field_options)
    wizard = kodi.WizardDialog_DictionarySelection(wizard, 'operator', kodi.translate(41178), operator_options)
    wizard = kodi.WizardDialog_Keyboard(wizard, 'value', kodi.translate(41179))
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        ruleset = repository.find_ruleset(romcollection_id, ruleset_id)
        
        rule = ruleset.get_rule(rule_id)
        if rule is None:
            kodi.notify_error(kodi.translate(41181))
            return
        
        if selected_action == 1:
            repository.delete_rule_from_ruleset(ruleset, rule)
            uow.commit()
        
        if selected_action == 0:
            entity_data = rule.get_data_dic()
            entity_data = wizard.runWizard(entity_data)
            if entity_data is None:
                AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
                return
                
            rule.import_data_dic(entity_data)
            repository.update_ruleset_in_romcollection(romcollection_id, ruleset)
            uow.commit()

    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
    kodi.notify(kodi.translate(41180))


def _select_source_for_rules(uow: UnitOfWork):
    src_repository = SourcesRepository(uow)
    sources = src_repository.find_all()
        
    options = collections.OrderedDict()
    for source in sources:
        options[source] = source.get_name()

    s = kodi.translate(41172)
    selected_option = kodi.OrdDictionaryDialog().select(s, options)
    return selected_option


@AppMediator.register('EXECUTE_RULESET')
def cmd_execute_ruleset(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    ruleset_id: str = args['ruleset_id'] if 'ruleset_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        src_repository = SourcesRepository(uow)
    
        ruleset = repository.find_ruleset(romcollection_id, ruleset_id)
        collection = repository.find_romcollection(romcollection_id)
        source = src_repository.find(ruleset.get_source_id())
            
        roms_in_collection = roms_repository.find_roms_by_romcollection(collection)
        collection_rom_ids = [rom.get_id() for rom in roms_in_collection]
        roms = [*roms_repository.find_roms_by_source(source)]
        counter = 0
        progress_dialog = kodi.ProgressDialog()
        progress_dialog.startProgress(kodi.translate(41185), num_steps=len(roms))
        for rom in roms:
            progress_dialog.incrementStep()
            if rom.get_id() in collection_rom_ids:
                continue
            
            if not ruleset.applies_to(rom):
                continue
            logger.debug(f"Adding ROM {rom.get_name()} to ROM Collection {collection.get_name()}")
            repository.add_rom_to_romcollection(romcollection_id, rom.get_id())
            counter += 1
            
        progress_dialog.endProgress()
        progress_dialog.close()
        
    AppMediator.async_cmd('EDIT_IMPORT_RULESET', args)
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    kodi.notify(kodi.translate(41183))


# --- Empty     Launcher ROMs ---
@AppMediator.register('CLEAR_ROMS')
def cmd_clear_roms(args):
    romcollection_id: str = args['romcollection_id'] if 'romcollection_id' in args else None
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        collection_repository = ROMCollectionRepository(uow)
        roms_repository = ROMsRepository(uow)
        
        romcollection = collection_repository.find_romcollection(romcollection_id)
        roms = roms_repository.find_roms_by_romcollection(romcollection)
        
        # If collection is empty (no ROMs) do nothing
        num_roms = len([*roms])
        if num_roms == 0:
            kodi.dialog_OK(kodi.translate(41151))
            return

        # Confirm user wants to delete ROMs
        ret = kodi.dialog_yesno(kodi.translate(41142).format(romcollection.get_name(), num_roms))
        if not ret:
            return

        # --- If there is a No-Intro XML DAT configured remove it ---
        # TODO fix
        # romcollection.reset_nointro_xmldata()

        # Confirm if the user wants to remove the ROMs also when linked to other collections.
        delete_completely = kodi.dialog_yesno(kodi.translate(41064))
        if not delete_completely:
            collection_repository.remove_all_roms_in_launcher(romcollection_id)
        else:
            roms_repository.delete_roms_by_romcollection(romcollection_id)
        uow.commit()
        
    AppMediator.async_cmd('RENDER_ROMCOLLECTION_VIEW', {'romcollection_id': romcollection_id})
    AppMediator.async_cmd('RENDER_CATEGORY_VIEW', {'category_id': romcollection.get_parent_id()})
    kodi.notify(kodi.translate(40977))
