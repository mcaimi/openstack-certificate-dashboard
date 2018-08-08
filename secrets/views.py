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

from django.core.urlresolvers import reverse,reverse_lazy, NoReverseMatch
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import settings
from openstack_dashboard.api import barbican
from openstack_dashboard.dashboards.project.secrets import tables as secrets_tables
from openstack_dashboard.dashboards.project.secrets import forms as secrets_forms

LOG = logging.getLogger(__name__)

class SecretData(object):
    def __init__(self, secret_object):
        self.secret_object = secret_object
        self.secret_object_dict = self.secret_object.__dict__
        for k in self.secret_object_dict:
            setattr(self, k, self.secret_object_dict.get(k))

        # map HREF to id
        self.id = self.secret_object.secret_ref
        self.secret_ref = self.id
        self.name = self.secret_object.name
        self.expiration = self.secret_object.expiration
        self.algorithm = self.secret_object.algorithm
        self.bit_length = self.secret_object.bit_length
        self.secret_type = self.secret_object.secret_type
        self.status = self.secret_object.status
        self.mode = self.secret_object.mode

class X509SecretsCreateView(forms.ModalFormView):
    template_name = 'project/secrets/create.html'
    modal_header = _("Create a new X509 Certificate")
    form_id = "x509_secret_create_form"
    form_class = secrets_forms.X509SecretsCreateForm
    submit_label = _("Create Certificate")
    submit_url = reverse_lazy("horizon:project:secrets:certcreate")
    success_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Add new Certificate")

class X509SecretsUpdateView(forms.ModalFormView):
    template_name = 'project/secrets/update.html'
    modal_header = _("Update Certificate Payload")
    form_id = "x509_secret_update_form"
    form_class = secrets_forms.X509SecretsUpdateForm
    submit_label = _("Update Payload")
    submit_url = "horizon:project:secrets:certupdate"
    success_url = reverse_lazy('horizon:project:secrets:index')
    cancel_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Update Certificate Bits")

    def get_context_data(self, **kwargs):
        context = super(X509SecretsUpdateView, self).get_context_data(**kwargs)
        context['cert_ref'] = self.kwargs.get('cert_ref')
        submit_args = (self.kwargs.get('cert_ref'),)
        context['submit_url'] = reverse(self.submit_url, args=submit_args)
        LOG.info("Certificate Update View: updated context %s" % context)
        return context

    def get_initial(self):
        return {'cert_ref': self.kwargs['cert_ref'],}

class IndexView(tables.DataTableView):
    table_class = secrets_tables.SecretTable
    template_name = 'project/secrets/index.html'
    page_title = _("X509 Certificate Management")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context

    def get_data(self):
        objects = []
        try:
            for secret_object in barbican.get_secrets(self.request):
                objects.append(SecretData(secret_object))
        except:
            objects = []
    
        return objects
