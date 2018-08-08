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

from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import barbican as barbican_bridge

LOG = logging.getLogger(__name__)

# Key-manager container create Django form
class SecretsContainerCreateForm(forms.SelfHandlingForm):
    containername = forms.CharField(max_length=255, label=_("Container Name"), required=True)
    containertype = forms.CharField(widget=forms.HiddenInput())
    certificate_object = forms.ThemableChoiceField(label=_("Select Certificate"), help_text=_("X509 Certificate ID from Openstack Keymanager"))
    pk_object = forms.ThemableChoiceField(label=_("Select Private Key"), help_text=_("Private Key ID from Openstack Keymanager"))

    def __init__(self, request, *args, **kwargs):
        super(SecretsContainerCreateForm, self).__init__(request, *args, **kwargs)

        # retrieve a list of stored secrets
        secrets_list = barbican_bridge.get_secrets(request)
        certificate_choices = [ (x.secret_ref.split("/")[-1], x.name) for x in secrets_list ]
        pk_choices = [ (x.secret_ref.split("/")[-1], x.name) for x in secrets_list ]

        self.fields['containername'].initial = "SSL Container"
        self.fields['containertype'].initial = 'certificate'
        self.fields['certificate_object'].choices = certificate_choices
        self.fields['pk_object'].choices = pk_choices

    def handle(self, request, data):
        LOG.info("secretscontainers::forms::SecretsContainerCreateForm: RUNNING HTTP POST HOOK")
        user = self.request.user
        name = data.get('containername')
        ctype = data.get('containertype')
        certref = data.get('certificate_object')
        pkref = data.get('pk_object')

        # retrieve object from keymanager
        cert = barbican_bridge.get_secret(request, certref)
        pk = barbican_bridge.get_secret(request, pkref)

        try:
            new_container = barbican_bridge.create_container(request, name=name, certificate=cert, private_key=pk)
            messages.success(request, _('[KEYMANAGER]: Container Create Request queued for execution.'))
            new_container.store()
            messages.success(request, _('[KEYMANAGER]: Container Stored.'))
        except:
            exceptions.handle(request, _('[KEYMANAGER]: Error while submitting Container Create Request.'))

        return True

