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

# Python Wrapper for openstack barbican. Used in the key-manager dashboard
# v.0.1 - Initial Implementation - Marco Caimi <marco.caimi@fastweb.it>

import logging
from keystoneauth1.identity import v2, v3
from keystoneauth1 import session
from django.conf import settings

# import base api library from openstack dashboard codebase
from openstack_dashboard.api import base
from openstack_dashboard.api import keystone
from horizon.utils import functions
from horizon.utils.memoized import memoized

# import barbican SDK libraries
from barbicanclient import client

LOG = logging.getLogger(__name__)
API_LIMIT = getattr(settings, 'API_RESULT_LIMIT', 1000)

DEBUGLOG = True

def logwrap_info(message):
    if DEBUGLOG:
        LOG.info("BARBICAN API WRAPPER: %s" % message)

# wrapper around the keymanager API set
@memoized
def keymanagerclient(request):
    token = request.user.token.id

    if keystone.get_version() < 3:
        tenant_id = request.user.tenant_id
        logwrap_info("using keystone v2")
        ks_auth = v2.Token("https://%s:5000/v2.0" % settings.OPENSTACK_HOST, 
                        token=token, tenant_id=tenant_id)
    else:
        project_id = request.user.project_id
        domain_id = request.session.get('domain_context')
        logwrap_info("using keystone v3")
        ks_auth = v3.Token("https://%s:5000/v3" % settings.OPENSTACK_HOST, 
                        token=token, 
                        project_id=project_id,
                        project_domain_id=domain_id)

    ks_session = session.Session(auth=ks_auth)
    return client.Client(session=ks_session)

# barbican interface functions
def get_containers(request):
    logwrap_info("contacting barbican for a complete container list")
    return keymanagerclient(request).containers.list(limit=API_LIMIT)

# create named container
def create_container(request, name, certificate, private_key):
    logwrap_info("creating new certificate container")
    return keymanagerclient(request).containers.create_certificate(name, certificate=certificate, private_key=private_key)

# delete named container
def delete_container(request, container_ref):
    logwrap_info("deleting container %s"%container_ref)
    return keymanagerclient(request).containers.delete(container_ref=container_ref)

# get secrets
def get_secrets(request):
    logwrap_info("contacting barbican for a complete secret list")
    return keymanagerclient(request).secrets.list(limit=API_LIMIT)

# create new secret
def create_x509secret(request, name, payload, algorithm, bit_length, mode, secret_type):
    logwrap_info("creating a new x509 secret")
    return keymanagerclient(request).secrets.create(name=name, payload=payload, algorithm=algorithm, bit_length=bit_length, mode=mode, secret_type=secret_type)

# get existing secret
def get_secret(request, secret_ref):
    logwrap_info("getting secret %s"%secret_ref)
    reference = "https://%s:9311/v1/secrets/%s" % (settings.OPENSTACK_HOST, secret_ref)
    return keymanagerclient(request).secrets.get(reference)

# create new secret
def update_x509secret(request, ref, payload):
    logwrap_info("updateing x509 secret")
    reference = "https://%s:9311/v1/secrets/%s" % (settings.OPENSTACK_HOST, ref)
    return keymanagerclient(request).secrets.update(secret_ref=reference, payload=payload)

# delete secret
def delete_secret(request, secret_ref):
    logwrap_info("deleting secret %s" % secret_ref)
    return keymanagerclient(request).secrets.delete(secret_ref)
