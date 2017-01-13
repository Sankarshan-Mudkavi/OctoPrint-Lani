# coding=utf-8
from __future__ import absolute_import

import uuid
import os

import octoprint.plugin

from octoprint_lani.listener import LaniListener


class LaniPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.AssetPlugin):

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
                id = id_file.read()
                self._logger.info('ID: {}'.format(id))
        except IOError:
            id = str(uuid.uuid4())
            self._logger.info('No ID found. Using {}.'.format(id))
            with open(id_file_path, 'w') as id_file:
                id_file.write(id)

        return dict(
            id=id,
            instance_endpoint='https://api.laniservices.com/octoprint_instances/',
            registration_link='https://lanilabs.com/add_octoprint/',
            oskr_url='ws://oskr.laniservices.com:8080/octoprint/ws'
        )

    # StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info('Starting Lani Listener.')
        listener = LaniListener(self._settings.get(['id']), self._settings.get(["oskr_url"]))
        listener.start()

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
