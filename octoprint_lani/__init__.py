# coding=utf-8
from __future__ import absolute_import

import uuid
import os
import json
import urllib2

import octoprint.plugin

from octoprint_lani.listener import LaniListener


class LaniPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.EventHandlerPlugin):

    def message_handler(self, payload):
        try:
            message = json.loads(payload)
            if message["type"] == "PRINT_STL":
                print(self._printer.get_state_id())
                # TODO: check for enabled printer
                model_file_location = "{}/model.stl".format(self.get_plugin_data_folder())
                print('Downloading file')
                res = urllib2.urlopen(message["url"])
                with open(model_file_location, 'w') as file:
                    file.write(res.read())
                print('slicing file')
                default_slicer = self._slicing_manager.default_slicer
                print(default_slicer)
                # print(self._slicing_manager.all_profiles(default_slicer, require_configured=True))
                print(self._slicing_manager.all_profiles(default_slicer))

                slicer_profile = None
                for profile in self._slicing_manager.all_profiles(default_slicer).itervalues():
                    if profile.default:
                        slicer_profile = profile.name
                        break
                if slicer_profile is None:
                    slicer_profile = self._slicing_manager.all_profiles(default_slicer).keys()[0]

                def callback(*args, **kwargs):
                    # TODO: check _errors here
                    if '_error' in kwargs:
                        print(kwargs['_error'])
                        return
                    print('slicing compllete')
                    print(args)
                    print(kwargs)
                    print(self._printer.is_ready())
                    print(self._printer.get_state_id())
                    if self._printer.is_ready():
                        print("printing")
                        self._printer.select_file(
                            "{}/model.gcode".format(self.get_plugin_data_folder()),
                            False,
                            printAfterSelect=True,
                        )
                        print("started")

                self._slicing_manager.slice(
                    default_slicer,
                    model_file_location,
                    "{}/model.gcode".format(self.get_plugin_data_folder()),
                    slicer_profile,
                    callback,
                )
                # self._printer.printwhatever()
            elif message["type"] == "STOP":
                self._printer.stop()
            print('handled')
        # except (KeyError, ValueError, IOError, octoprint.slicing.exceptions.SlicerNotConfigured):
        except (KeyError):
            print("Invalid message")

    # EventHandler mixin

    def on_event(self, event, payload):
        print(json.dumps({
            'state': self._printer.get_state_id(),
        }))

    def on_print_progress(self, storage, path, progress):
        print(json.dumps({
            'state': self._printer.get_state_id(),
            'progress': progress,
        }))

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
            instance_endpoint='https://api.laniservices.com/octoprint_instances/',
            registration_link='https://lanilabs.com/add_octoprint/',
            oskr_url='ws://oskr.laniservices.com:8080/octoprint/client'
        )

    # StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info('Starting Lani Listener.')
        listener = LaniListener(
            self._settings.get(['id']),
            self._settings.get(["oskr_url"]),
            self.get_plugin_data_folder(),
        )
        listener.start()

        # twistedLogger = log.PythonLoggingObserver(loggerName='octoprint.plugins.lani.listener.twisted')
        # twistedLogger.start()

        # factory = WebSocketFactory('ws://oskr.laniservices.com:8080/octoprint/client' + '?uuid=' + self._settings.get(['id']))
        # factory.protocol = WebSocketProtocol

        # connectWS(factory)
        # # reactor.run(installSignalHandlers=False)
        # Process(target=reactor.run).start()
        print('test')

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

