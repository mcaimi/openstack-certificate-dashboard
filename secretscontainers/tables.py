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

import logging
import uuid

from django.template import defaultfilters, loader
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from django.core.urlresolvers import reverse,reverse_lazy, NoReverseMatch

from horizon import tables,exceptions,messages
from openstack_dashboard.api import barbican as barbican_bridge

LOG = logging.getLogger(__name__)

# create container button link handler
class ContainerCreateLink(tables.LinkAction):
    name = "containercreate"
    verbose_name = _("Add a Secrets Container")
    url = "horizon:project:secretscontainers:containercreate"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, datum):
        return True

# container delete button link handler
class ContainerDeleteLink(tables.DeleteAction):
    name = "containerdelete"
    success_url = reverse_lazy("horizon:project:secretscontainers:index")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Secrets Container",
            u"Delete Secrets Container",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Container Delete Action Accepted",
            u"Container Delete Action Accepted",
            count
        )

    def allowed(self, request, datum):
       return True

    def delete(self, request, obj_id):
       barbican_bridge.delete_container(request, obj_id)

def get_consumers(entity):
    template_name = 'project/secretscontainers/_consumers.html'
    if hasattr(entity, 'consumers'):
        name = "".join(set([x.get('name') for x in entity.consumers]))
        number_of_consumers = len(entity.consumers)
        consumers_id = ",<br/>".join([x.get('URL').split("/")[-1] for x in entity.consumers])

        context = {
            "name": name,
            "id": consumers_id,
            "number_of_consumers": number_of_consumers,
        }
        return loader.render_to_string(template_name, context)
    return _("No Consumer")

def get_secrets(entity):
    template_name = 'project/secretscontainers/_secrets.html'
    if hasattr(entity, 'secrets'):
        name = str(uuid.uuid1())
        certificate_obj = entity.secrets.get('certificate')
        private_key_obj = entity.secrets.get('private_key')

        certificate_id = certificate_obj.secret_ref.split("/")[-1]
        certificate_name = certificate_obj.name

        private_key_id = private_key_obj.secret_ref.split("/")[-1]
        private_key_name = private_key_obj.name

        context = {
            "name": name,
            "certificate_id": certificate_id,
            "certificate_name": certificate_name,
            "private_key_id": private_key_id,
            "private_key_name": private_key_name,
        }
        return loader.render_to_string(template_name, context)
    return _("No Consumer")

class SecretContainerTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('ID'), hidden=True)
    container_ref = tables.Column('container_ref', link='horizon:project:secretscontainers:secrets', verbose_name=_('Container HREF'))
    name = tables.Column('name', verbose_name=_('Container Name'))
    consumers = tables.Column(get_consumers, verbose_name=_('Active Consumers'))
    secrets = tables.Column(get_secrets, verbose_name=_('Stored Secrets'))
    type = tables.Column('type', verbose_name=_('Container Type'))
    status = tables.Column('status', verbose_name=_('Container Status'))

    class Meta(object):
        name = "secretscontainers"
        verbose_name = _("Secrets Management: Containers")
        table_actions = (ContainerCreateLink, )
        row_actions = (ContainerDeleteLink, )
