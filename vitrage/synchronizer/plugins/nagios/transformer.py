# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log as logging

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common import datetime_utils
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins.base.alarm.properties \
    import AlarmProperties as AlarmProps
from vitrage.synchronizer.plugins.base.alarm.transformer \
    import BaseAlarmTransformer
from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties
from vitrage.synchronizer.plugins import transformer_base as tbase

LOG = logging.getLogger(__name__)


class NagiosTransformer(BaseAlarmTransformer):

    STATUS_OK = 'OK'

    def __init__(self, transformers):
        super(NagiosTransformer, self).__init__(transformers)

    def _create_entity_vertex(self, entity_event):

        timestamp = datetime_utils.change_time_str_format(
            entity_event[NagiosProperties.LAST_CHECK],
            '%Y-%m-%d %H:%M:%S',
            tbase.TIMESTAMP_FORMAT)

        metadata = {
            VProps.NAME: entity_event[NagiosProperties.SERVICE],
            VProps.SEVERITY: entity_event[NagiosProperties.STATUS],
            VProps.INFO: entity_event[NagiosProperties.STATUS_INFO]
        }

        return graph_utils.create_vertex(
            self.extract_key(entity_event),
            entity_category=EntityCategory.ALARM,
            entity_type=entity_event[SyncProps.SYNC_TYPE],
            entity_state=AlarmProps.ALARM_STATE,
            update_timestamp=timestamp,
            metadata=metadata)

    def _create_neighbors(self, entity_event):

        vitrage_id = self.extract_key(entity_event)
        timestamp = datetime_utils.change_time_str_format(
            entity_event[NagiosProperties.LAST_CHECK],
            '%Y-%m-%d %H:%M:%S',
            tbase.TIMESTAMP_FORMAT)

        resource_type = entity_event[NagiosProperties.RESOURCE_TYPE]
        if resource_type == EntityType.NOVA_HOST:
            return [self._create_host_neighbor(
                vitrage_id,
                timestamp,
                entity_event[NagiosProperties.RESOURCE_NAME])]

        return []

    def _create_host_neighbor(self, vitrage_id, timestamp, host_name):

        transformer = self.transformers[EntityType.NOVA_HOST]

        if transformer:

            properties = {
                VProps.ID: host_name,
                VProps.UPDATE_TIMESTAMP: timestamp
            }
            host_vertex = transformer.create_placeholder_vertex(properties)

            relationship_edge = graph_utils.create_edge(
                source_id=vitrage_id,
                target_id=host_vertex.vertex_id,
                relationship_type=EdgeLabels.ON)

            return tbase.Neighbor(host_vertex, relationship_edge)

        LOG.warning('Cannot transform host, host transformer does not exist')
        return None

    def _ok_status(self, entity_event):
        return entity_event[NagiosProperties.STATUS] == self.STATUS_OK

    def extract_key(self, entity_event):

        sync_type = entity_event[SyncProps.SYNC_TYPE]
        alarm_name = entity_event[NagiosProperties.SERVICE]
        resource_name = entity_event[NagiosProperties.RESOURCE_NAME]
        return tbase.build_key(self.key_values([sync_type,
                                                resource_name,
                                                alarm_name]))
