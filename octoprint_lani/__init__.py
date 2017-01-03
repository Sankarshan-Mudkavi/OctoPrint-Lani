# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from octoprint_lani.listener import LaniListener


class LaniPlugin(octoprint.plugin.StartupPlugin):

    # ~~ Softwareupdate hook

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

    # ~~ StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info('Starting Lani Listener.')
        listener = LaniListener()
        listener.start()


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
