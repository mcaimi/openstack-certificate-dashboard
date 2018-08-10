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
class X509SecretsCreateForm(forms.SelfHandlingForm):
    CIPHERSUITES=(
            ("aes", "AES"),
            ("3des", "Triple DES"),
            ("blowfish", "Blowfish"),
            )
    BITLENGHTS=(
            ("256", "256-bit"),
            ("512", "512-bit"),
            ("1024", "1024-bit"),
            ("2048", "2048-bit"),
            ("4096", "4096-bit"),
            )
    CRYPTOMODES=(
            ("cbc", "cipher block chaining"),
            ("cfb", "cipher feedback"),
            ("ofb", "output feedback"),
            ("ctr", "counter"),
            )

    secret_name = forms.CharField(max_length=255, label=_("X509 Certificate Name"), required=True)
    secret_type = forms.CharField(widget=forms.HiddenInput())
    ciphersuite = forms.ChoiceField(choices=CIPHERSUITES, required=True)
    bitlength = forms.ChoiceField(choices=BITLENGHTS, required=True)
    cryptomode = forms.ChoiceField(choices=CRYPTOMODES, required=True)
    certificate = forms.CharField(label=_("Certificate"), widget=forms.Textarea(), required=True)
    private_key = forms.CharField(label=_("Private Key"), widget=forms.Textarea(), required=True)


    def __init__(self, request, *args, **kwargs):
        super(X509SecretsCreateForm, self).__init__(request, *args, **kwargs)

        self.fields['secret_name'].initial = "x509_cert"
        self.fields['secret_type'].initial = 'opaque'
        self.fields['ciphersuite'].initial = 'aes'
        self.fields['bitlength'].initial = '256'
        self.fields['cryptomode'].initial = 'cbc'
        self.fields['certificate'].initial = 'Copy your certificate here'
        self.fields['private_key'].initial = 'Copy your private key here'

    def handle(self, request, data):
        LOG.info("secrets::forms::SecretsCreateForm: RUNNING HTTP POST HOOK")
        user = self.request.user
        secretname = data.get('secret_name')
        secret_type = data.get('secret_type')
        cipher_suite = data.get("ciphersuite")
        bitlength = data.get("bitlength")
        mode = data.get("cryptomode")
        certificate = data.get('certificate')
        private_key = data.get('private_key')

        try:
            new_cert_secret = barbican_bridge.create_x509secret(request, name=secretname+"_crt", payload=certificate, algorithm=cipher_suite, bit_length=int(bitlength), mode=mode, secret_type=secret_type)
            messages.success(request, _('[KEYMANAGER]: Certificate Create Request queued for execution.'))
            new_cert_secret.store()
            messages.success(request, _('[KEYMANAGER]: Certificate Successfully Stored'))

            new_key_secret = barbican_bridge.create_x509secret(request, name=secretname+"_key", payload=private_key, algorithm=cipher_suite, bit_length=int(bitlength), mode=mode, secret_type=secret_type)
            messages.success(request, _('[KEYMANAGER]: Private Key Create Request queued for execution.'))
            new_key_secret.store()
            messages.success(request, _('[KEYMANAGER]: Private Key Successfully Stored'))
        except:
            exceptions.handle(request, _('[KEYMANAGER]: Error while submitting Certificate or Private Key Create Request.'))

        return True

# Key-manager container update Django form
class X509SecretsUpdateForm(forms.SelfHandlingForm):
    cert_ref = forms.CharField(widget=forms.HiddenInput())
    secret_name = forms.CharField(widget=forms.HiddenInput())
    secret_type = forms.CharField(widget=forms.HiddenInput())
    payload = forms.CharField(label=_("Payload"), widget=forms.Textarea(), required=True)

    def __init__(self, request, *args, **kwargs):
        super(X509SecretsUpdateForm, self).__init__(request, *args, **kwargs)

        self.fields['cert_ref'].initial = kwargs.get('initial', {}).get('cert_ref')
        # get initial value
        secret = barbican_bridge.get_secret(request, self.fields['cert_ref'].initial)

        self.fields['secret_name'].initial = secret.name
        self.fields['secret_type'].initial = secret.secret_type
        self.fields['payload'].initial = secret.payload

    def handle(self, request, data):
        LOG.info("secrets::forms::SecretsUpdateForm: RUNNING HTTP POST HOOK")
        user = self.request.user
        secretname = data.get('secret_name')
        secret_type = data.get('secret_type')
        secret_id = data.get('cert_ref')
        payload = data.get('payload')

        try:
            barbican_bridge.update_x509secret(request, ref=secret_id, payload=payload)
            messages.success(request, _('[KEYMANAGER]: Update Request queued for execution.'))
        except:
            exceptions.handle(request, _('[KEYMANAGER]: Error while submitting Certificate or Private Key Update Request.'))

        return True

