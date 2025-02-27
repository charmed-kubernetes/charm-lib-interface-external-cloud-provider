from unittest import mock

import pytest

import charms.interface_external_cloud_provider as iecp


@pytest.mark.parametrize(
    "vendor, cloud_name",
    [
        ("Amazon EC2", "aws"),
        ("Google", "gce"),
        ("Microsoft Corporation", "azure"),
        ("VMware, Inc.", "vsphere"),
        ("OpenStack Foundation", "openstack"),
        ("Dell Inc.", None),
    ],
)
def test_vendor(vendor, cloud_name):
    charm = mock.MagicMock()
    with mock.patch("pathlib.Path.read_text", autospec=True) as mock_subprocess:
        mock_subprocess.return_value = vendor
        ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
        assert ecp.name == cloud_name


def test_charm_attr():
    charm = mock.MagicMock()
    ecp = iecp.ExternalCloudProvider(charm, "external-cloud-provider")
    assert ecp.unit == charm.unit
