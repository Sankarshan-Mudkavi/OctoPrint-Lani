# coding=utf-8
from __future__ import absolute_import

import uuid
import os
import json
import requests

import octoprint.plugin
import octoprint.printer

from octoprint_lani.listener import LaniListener


class PrinterCallback(octoprint.printer.PrinterCallback):
    def __init__(self, logger, uuid, update_url):
        super(self.__class__, self).__init__()
        self._logger = logger
        self._uuid = uuid
        self._update_url = update_url
        self.last_state = ''

    def on_printer_send_current_data(self, data):
        state = json.dumps({
            self._uuid: data
        })
        if state != self.last_state:
            self.last_state = state
            try:
                requests.post(self._update_url, data=state)
            except requests.ConnectionError:
                pass
            except:
                self._logger.info('Ignoring request error.')

    # def on_printer_add_temperature(self, data):
    #     pass


class LaniPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.ShutdownPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.EventHandlerPlugin,
                 octoprint.plugin.ProgressPlugin):

    # def __send_state_update(self, progress=None):
    #     global last_state
    #     current_state = self._printer.get_state_id()
    #     uuid = self._settings.get(['id'])

    #     state = {
    #         uuid: {
    #             'state': current_state,
    #             'temperatures': self._printer.get_current_temperatures(),
    #             'job': self._printer.get_current_job(),
    #         },
    #     }
    #     if progress is not None:
    #         state[uuid]['progress'] = progress
    #     elif last_state == current_state:
    #         # No need to make another request
    #         return

    #     last_state = current_state
    #     self._logger.info('Sending state update: {}'.format(json.dumps(state)))
    #     requests.post(self._settings.get(['oskr_update_url']), data=json.dumps(state))

    # EventHandler mixin

    # def on_event(self, event, payload):
    #     self.__send_state_update()

    # Progress mixin

    # def on_print_progress(self, storage, path, progress):
    #     self.__send_state_update(progress=progress)

    # Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            lani=dict(
                displayName="Lani Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="mikerybka",
                repo="OctoPrint-Lani",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/mikerybka/OctoPrint-Lani/archive/{target_version}.zip"
            )
        )

    # SettingsPlugin mixin

    def get_settings_defaults(self):
        self._logger.info('Checking for unique ID.')
        id_file_path = os.path.join(self.get_plugin_data_folder(), 'id.txt')
        try:
            with open(id_file_path, 'r') as id_file:
                id = id_file.read().strip()
                self._logger.info('ID: {}'.format(id))
        except IOError:
            id = str(uuid.uuid4())
            self._logger.info('No ID found. Using {}.'.format(id))
            with open(id_file_path, 'w') as id_file:
                id_file.write(id)

        return dict(
            id=id,
            # instance_endpoint='http://localhost:3000/octoprint_instances/',
            instance_endpoint='https://lani-api.herokuapp.com/octoprint_instances/',
            # registration_link='http://localhost:8000/add_octoprint/',
            registration_link='https://lanilabs.com/add_octoprint/',
            oskr_ws_url='ws://oskr.laniservices.com:8080/octoprint/client?uuid={}'.format(id),
            oskr_update_url='https://oskr.laniservices.com/octoprint/update?uuid={}'.format(id),
        )

    # StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info('Initializing.')

        self._logger.info('Registering callback for printer events.')
        self._printer.register_callback(PrinterCallback(
            self._logger,
            self._settings.get(['id']),
            self._settings.get(['oskr_update_url']),
        ))

        self._logger.info('Sending initial state data.')
        requests.post(self._settings.get(['oskr_update_url']), data=json.dumps({
            self._settings.get(['id']): self._printer.get_current_data()
        }))

        self._logger.info('Starting Lani Listener.')
        self.listener = LaniListener(
            self._logger,
            self._settings.get(['oskr_ws_url']),
            self.get_plugin_data_folder(),
        )
        self.listener.start()

    # ShutdownPlugin mixin

    def on_shutdown(self):
        self._logger.info('Cleaning up.')
        if self.listener.is_alive():
            self._logger.info('Terminating listener process.')
            self.listener.terminate()

    # TemplatePlugin

    def get_template_vars(self):
        id = self._settings.get(['id'])
        return dict(
            instance_endpoint='{}{}'.format(self._settings.get(["instance_endpoint"]), id),
            registration_link='{}{}'.format(self._settings.get(["registration_link"]), id)
        )

    # AssetPlugin mixin

    def get_assets(self):
        return dict(
            js=['js/lani.js']
        )

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Lani"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LaniPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

