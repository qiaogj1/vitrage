# Copyright 2017 Nokia
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from datetime import datetime
from oslo_log import log as logging
from oslotest import base

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventProperties as EventProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage import keystone_client
from vitrage import service
from vitrageclient import client as v_client

LOG = logging.getLogger(__name__)


class TestEvents(base.BaseTestCase):
    """Test class for Vitrage event API"""

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = service.prepare_service([])
        cls.vitrage_client = \
            v_client.Client('1', session=keystone_client.get_session(cls.conf))

    def test_send_doctor_event(self):
        """Sending an event in Doctor format should result in an alarm"""
        try:
            # post an event to the message bus
            event_time = datetime.now().isoformat()
            event_type = 'compute.host.down'
            details = {
                'hostname': 'host123',
                'source': 'sample_monitor',
                'cause': 'another alarm',
                'severity': 'critical',
                'status': 'down',
                'monitor_id': 'sample monitor',
                'monitor_event_id': '456',
            }

            self.vitrage_client.event.post(event_time, event_type, details)

            # list all alarms
            api_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                        all_tenants=False)

            # expect to get a 'host down alarm', generated by Doctor datasource
            self.assertIsNotNone(api_alarms, 'Expected host down alarm')
            self.assertEqual(1, len(api_alarms), 'Expected host down alarm')
            alarm = api_alarms[0]

            self._wait_for_status(2,
                                  self._check_alarm,
                                  alarm=alarm,
                                  event_time=event_time,
                                  event_type=event_type,
                                  details=details)

        except Exception as e:
            LOG.exception(e)
            raise
        finally:
            # do what?
            LOG.warning('done')

    def _check_alarm(self, alarm, event_time, event_type, details):
        LOG.info('alarm = %s', str(alarm))
        self.assertEqual(EntityCategory.ALARM, alarm[VProps.CATEGORY])
        self.assertEqual(event_type, alarm[VProps.NAME])
        self.assertEqual(event_time, alarm[EventProps.TIME])
        self.assertEqual(event_type, alarm[DSProps.ENTITY_TYPE])
        self.assertEqual(details['status'], alarm[VProps.STATE])
        self.assertFalse(alarm[VProps.IS_DELETED])
        self.assertFalse(alarm[VProps.IS_PLACEHOLDER])
