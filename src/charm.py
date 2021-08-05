#!/usr/bin/env python3
# Copyright 2021 Juan M. Tirado
# See LICENSE file for licensing details.


import logging

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class NoderedOperatorCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
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
