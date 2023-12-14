import charms.interface_external_cloud_provider as iecp
from unittest import mock
from pathlib import Path
import pytest


@pytest.mark.parametrize("vendor, cloud_name", [
    ("Amazon EC2", "aws"),
    ("Google", "gce"),
    ("Microsoft Corporation", "azure"),
    ("VMWare, Inc.", "vsphere"),
    ("OpenStack Foundation", "openstack"),
    ("Dell Inc.", None),
])
def test_vendor(vendor, cloud_name):
    charm = mock.MagicMock()
    with mock.patch("charms.interface_external_cloud_provider.check_output") as mock_subprocess:
        mock_subprocess.return_value = vendor
        ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
        assert ecp.name == cloud_name

def test_charm_attr():
    charm = mock.MagicMock()
    ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
    assert ecp.unit == charm.unit
