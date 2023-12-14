from unittest import mock

import pytest

import charms.interface_external_cloud_provider as iecp


@pytest.mark.parametrize(
    "vendor, cloud_name",
    [
        (b"Amazon EC2", "aws"),
        (b"Google", "gce"),
        (b"Microsoft Corporation", "azure"),
        (b"VMware, Inc.", "vsphere"),
        (b"OpenStack Foundation", "openstack"),
        (b"Dell Inc.", None),
    ],
)
def test_vendor(vendor, cloud_name):
    charm = mock.MagicMock()
    with mock.patch(
        "charms.interface_external_cloud_provider.check_output"
    ) as mock_subprocess:
        mock_subprocess.return_value = vendor
        ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
        assert ecp.name == cloud_name


def test_charm_attr():
    charm = mock.MagicMock()
    ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
    assert ecp.unit == charm.unit
