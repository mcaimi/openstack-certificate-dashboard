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
from openstack_dashboard.dashboards.project.secretscontainers import tables as secretscontainers_tables
from openstack_dashboard.dashboards.project.secretscontainers import forms as secretscontainers_forms

LOG = logging.getLogger(__name__)

class SecretData(object):
    def __init__(self, secret_object):
        self.secret_object = secret_object
        self.secret_object_dict = self.secret_object.__dict__
        for k in self.secret_object_dict:
            setattr(self, k, self.secret_object_dict.get(k))

        # map HREF to id
        self.id = self.secret_object.container_ref
        self.container_ref = self.id
        self.name = self.secret_object.name
        self.status = self.secret_object.status
        self.type = self.secret_object._api.get(self.container_ref).get('type', '').lower()

        # map secrets and consumers
        self.consumers = self.secret_object.consumers
        self.secrets = self.secret_object.secrets

class SecretsContainerCreateView(forms.ModalFormView):
    template_name = 'project/secretscontainers/containercreate.html'
    modal_header = _("Create a new Secrets Container")
    form_id = "secret_container_create_form"
    form_class = secretscontainers_forms.SecretsContainerCreateForm
    submit_label = _("Create Container")
    submit_url = reverse_lazy("horizon:project:secretscontainers:containercreate")
    success_url = reverse_lazy('horizon:project:secretscontainers:index')
    page_title = _("Create a new Secrets Container")

class IndexView(tables.DataTableView):
    table_class = secretscontainers_tables.SecretContainerTable
    template_name = 'project/secretscontainers/index.html'
    page_title = _("Secrets Management - Containers")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context

    def get_data(self):
        objects = []
        try:
            for container_object in barbican.get_containers(self.request):
                objects.append(SecretData(container_object))
        except:
            objects = []
    
        return objects
