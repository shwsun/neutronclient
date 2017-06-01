# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

from neutronclient.common import utils


# -------------------------------------------------
# NOTE(jethro): below are a little things I stuffed
# -------------------------------------------------
from oslo_utils import importutils

osprofiler_profiler = importutils.try_import("osprofiler.profiler")

import random
import subprocess

def is_sampled(rate):
    MAX_RANGE = 100
    if random.randint(0, 100) < MAX_RANGE * rate:
        return True
    return False

SAMPLING_RATE = 0.5


API_NAME = 'network'
API_VERSIONS = {
    '2.0': 'neutronclient.v2_0.client.Client',
    '2': 'neutronclient.v2_0.client.Client',
}


def make_client(instance):
    """Returns an neutron client."""
    neutron_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS,
    )
    instance.initialize()
    url = instance._url
    url = url.rstrip("/")
    client = neutron_client(username=instance._username,
                            project_name=instance._project_name,
                            password=instance._password,
                            region_name=instance._region_name,
                            auth_url=instance._auth_url,
                            endpoint_url=url,
                            endpoint_type=instance._endpoint_type,
                            token=instance._token,
                            auth_strategy=instance._auth_strategy,
                            insecure=instance._insecure,
                            ca_cert=instance._ca_cert,
                            retries=instance._retries,
                            raise_errors=instance._raise_errors,
                            session=instance._session,
                            auth=instance._auth)
    return client


def Client(api_version, *args, **kwargs):
    """Return an neutron client.

    @param api_version: only 2.0 is supported now
    """
    neutron_client = utils.get_client_class(
        API_NAME,
        api_version,
        API_VERSIONS,
    )

    # NOTE(jethro): profile demonstrate the --profile, here set to be true by
    # default. Also note that novaclient has two client instance (one as default
    # and one is discovered), here the sampling only work on the discovered
    # client instance.
    profile = "123"
    if profile and is_sampled(SAMPLING_RATE):
        # Initialize the root of the future trace: the created trace ID will
        # be used as the very first parent to which all related traces will be
        # bound to. The given HMAC key must correspond to the one set in
        # nova-api nova.conf, otherwise the latter will fail to check the
        # request signature and will skip initialization of osprofiler on
        # the server side.
        print("sampled")
        osprofiler_profiler.init(profile)
    try:
        trace_id = osprofiler_profiler.get().get_base_id()
        print("Trace ID: %s" % trace_id)
        print("Traces are dumped into /home/centos/traces")
        cmd = "echo " + trace_id + " >> /home/centos/neutron-jobs"
        subprocess.call(["bash", "-c", cmd])
    except:
        pass
    return neutron_client(*args, **kwargs)
