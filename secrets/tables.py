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

from django.template import defaultfilters
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from django.core.urlresolvers import reverse,reverse_lazy, NoReverseMatch

from horizon import tables,exceptions,messages
from openstack_dashboard.api import barbican as barbican_bridge

LOG = logging.getLogger(__name__)

# create secret button link handler
class X509SecretCreateLink(tables.LinkAction):
    name = "certcreate"
    verbose_name = _("Add a New X509 Certificate")
    url = "horizon:project:secrets:certcreate"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, datum):
        return True

# update certificate
class X509SecretUpdateLink(tables.LinkAction):
    name = "certupdate"
    verbose_name = "Update Certificate Payload"
    url = "horizon:project:secrets:certupdate"
    cancel_url = "horizon:project:secrets:index"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        if not self.url:
            raise NotImplementedError('A LinkAction class must have a '
                                      'url attribute or define its own '
                                      'get_link_url method.')

        if callable(self.url):
            return self.url(datum, **self.kwargs)
        try:
            if datum:
                obj_id = self.table.get_object_id(datum)
                return reverse(self.url, args=(obj_id.split("/")[-1],))
            else:
                return reverse(self.url)

        except NoReverseMatch as ex:
            LOG.error('No reverse found for "%(url)s": %(exception)s', {'url': self.url, 'exception': ex})
            return reverse_lazy(self.cancel_url)

    def allowed(self, request, datum):
        return False

# delete secret
class SecretDeleteLink(tables.DeleteAction):
    name = "secretdelete"
    success_url = reverse_lazy("horizon:project:secrets:index")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Entry",
            u"Delete Entry",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Delete Action Accepted",
            u"Delete Action Accepted",
            count
        )

    def allowed(self, request, datum):
       return True

    def delete(self, request, obj_id):
        barbican_bridge.delete_secret(request, obj_id)

class SecretTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('ID'), hidden=True)
    secret_ref = tables.Column('secret_ref', link='horizon:project:secrets:secret', verbose_name=_('Secret HREF'))
    name = tables.Column('name', verbose_name=_('Name'))
    secret_type = tables.Column('secret_type', verbose_name=_('Type'))
    algorithm = tables.Column('algorithm', verbose_name=_('Algorithm'))
    bit_length = tables.Column('bit_length', verbose_name=_('Bit Length'))
    mode = tables.Column('mode', verbose_name=_('Mode'))
    status = tables.Column('status', verbose_name=_('Status'))

    class Meta(object):
        name = "secrets"
        verbose_name = _("X509 Certificate Management")
        table_actions = (X509SecretCreateLink, )
        row_actions = (X509SecretUpdateLink, SecretDeleteLink, )
