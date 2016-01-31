# Copyright 2016 - Alcatel-Lucent
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

import abc

import six

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common import utils


@six.add_metaclass(abc.ABCMeta)
class BasePlugin(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_all(self):
        pass

    def make_pickleable(self, entities, sync_type, fields_to_remove=None):

        pickleable_entities = []

        for entity in entities:
            pickleable_entity = entity.__dict__

            for field in fields_to_remove:
                pickleable_entity.pop(field)

            self._add_sync_type(pickleable_entity)
            self._add_sampling_time(pickleable_entity)
            pickleable_entities.append(pickleable_entity)

        return pickleable_entities

    @staticmethod
    def _add_sync_type(entity, sync_type):
        if sync_type:
            entity[SyncProps.SYNC_TYPE] = sync_type

    @staticmethod
    def _add_sampling_time(entity):
        entity[SyncProps.SAMPLE_DATE] = str(utils.utcnow())
