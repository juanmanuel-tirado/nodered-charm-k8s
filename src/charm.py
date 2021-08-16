#!/usr/bin/env python3
# Copyright 2021 Juan M. Tirado
# See LICENSE file for licensing details.


import logging
import requests

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

METHOD_GET='get'
METHOD_POST='post'
METHOD_DELETE='delete'


class NoderedOperatorCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install_package_action, self._on_install_package_action)
        self.framework.observe(self.on.uninstall_package_action, self._on_uninstall_package_action)
        self.ingress = IngressRequires(self, {
            'service-hostname': self.model.config['hostname'],
            'service-name': self.app.name,
            'service-port': self.model.config['port'],
        })

    @property
    def _hostname(self):
        return self.config['hostname'] or self.app.name

    def _nodered_layer(self):
        '''
        It returns a layer configuration object.
        '''
        return {
            "summary": "nodered layer",
            "description": "pebble config layer for nodered",
            "services": {
                "nodered": {
                    "override": "replace",
                    "summary": "nodered",
                    "command": "node-red -p {} {} -u {} --title {}".format(
                        self.model.config['port'],
                        '--safe' if self.model.config['safe'] else '',
                        self.meta.storages['projects'].location,
                        self.model.config['title']),
                    "startup": "enabled",
                }
            },
        }

    def _call_api(self, method, uri, json):
        '''
        Generic method to call the Node-red api for a given URI and
        the json payload. It returns result object.
        '''
        if method==METHOD_GET:
            return requests.post(uri, json=json)
        if method==METHOD_POST:
            return requests.post(uri, json=json)
        if method==METHOD_DELETE:
            return requests.delete(uri,json=json)
        

    def _on_install_package_action(self, event):
        """Handle the install-package action."""
        # Fetch the package parameter from the ActionEvent params dict
        
        package = event.params['package']
        # Use shell to execute the command
        uri = f'http://localhost:{self.model.config["port"]}/nodes'
        r = self._call_api(METHOD_POST, uri, {'module': package})
        
        if not r.ok:
            event.log(f'Failed with code {r.status_code}: {r.text}')
            event.fail(
                f'Failed to run {uri}. Output was:\n{r.status_code}'
            )
        else:
            event.log(f'Module {package} installed')

    def _on_uninstall_package_action(self, event):
        """Handle the uninstall-package action."""
        # Fetch the package parameter from the ActionEvent params dict
        
        package = event.params['package']
        # Use shell to execute the command
        uri = f'http://localhost:{self.model.config["port"]}/nodes/{package}'
        r = self._call_api(METHOD_DELETE, uri, {})
        
        if not r.ok:
            event.log(f'Failed with code {r.status_code}: {r.text}')
            event.fail(
                f'Failed to run {uri}. Output was:\n{r.status_code}'
            )
        else:
            event.log(f'Module {package} uninstalled')

        

    def _on_config_changed(self, event):
        '''
        To be invoked when a config changed is found.
        '''
        container = self.unit.get_container('nodered')
        # Create a new config layer
        layer = self._nodered_layer()
        try:
            # Get the nodered container
            services = container.get_plan().to_dict().get('services', {})
        except ConnectionError:
            event.defer()
            return

        if services != layer['services']:
            # Some changes were done, add the new layer.
            container.add_layer('nodered', layer, combine=True)
            logging.info('Added updated layer nodered to Pebble plan')
            # Stop the service if running
            if container.get_service('nodered').is_running():
                logging.info('Stopped nodered service')
                container.stop('nodered')
            container.start('nodered')
            logging.info('Started nodered service')
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(NoderedOperatorCharm)
