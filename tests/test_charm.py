# Copyright 2021 jtirado
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import patch

from charm import NoderedOperatorCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(NoderedOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_on_config_changed(self):
        plan = self.harness.get_container_pebble_plan('nodered')
        self.assertEqual(plan.to_dict(), {})

        self.harness.update_config({'port': 1880})
        plan = self.harness.get_container_pebble_plan('nodered')

        expected = self.harness.charm._nodered_layer()
        expected.pop('summary', '')
        expected.pop('description', '')
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        container = self.harness.model.unit.get_container('nodered')
        self.assertEqual(container.get_service('nodered').is_running(), True)

        # With the running container we modify the configuration
        self.harness.update_config({'port': 7777})
        plan = self.harness.get_container_pebble_plan('nodered')

        aux = expected['services']['nodered']['command'].replace('1880', '7777')
        expected['services']['nodered']['command'] = aux
        self.assertEqual(plan.to_dict(), expected)
        self.assertEqual(container.get_service('nodered').is_running(), True)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        # And finally test again with the same config to ensure we exercise
        # the case where the plan we've created matches the active one. We're
        # going to mock the container.stop and container.start calls to confirm
        # they were not called.
        with patch('ops.model.Container.start') as _start, \
                patch('ops.model.Container.stop') as _stop:

            self.harness.charm.on.config_changed.emit()
            _start.assert_not_called()
            _stop.assert_not_called()
