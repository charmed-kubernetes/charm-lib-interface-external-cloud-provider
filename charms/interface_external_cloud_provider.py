import json
import logging
from functools import cached_property
from pathlib import Path
from subprocess import CalledProcessError, check_output
from typing import List, Optional
from urllib.request import Request, urlopen

from ops import CharmBase, Relation, Unit

log = logging.getLogger(__name__)

CLOUD_PROVIDERS = [
    {"name": "aws", "vendor": "Amazon"},
    {"name": "openstack", "vendor": "OpenStack"},
    {"name": "azure", "vendor": "Microsoft"},
    {"name": "gce", "vendor": "Google"},
    {"name": "vsphere", "vendor": "VMware"},
]

OPENSTACK_METADATA = "http://169.254.169.254/openstack/2018-08-27/meta_data.json"
AWS_METADATA = "http://169.254.169.254/2009-04-04/meta-data/instance-id"
VSPHERE_METADATA = "/sys/class/dmi/id/product_uuid"
AZURE_METADATA = "http://169.254.169.254/metadata/instance?api-version=2017-12-01"
GOOGLE_METADATA = "http://metadata.google.internal/computeMetadata/v1/instance/id"


class ExternalCloudProvider:
    """Provides data for configuring kubernetes components using an external-cloud provider."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    @property
    def relations(self) -> List[Relation]:
        return self.charm.model.relations[self.endpoint]

    @property
    def unit(self) -> Unit:
        return self.charm.unit

    @property
    def has_xcp(self) -> bool:
        """Whether or not this cluster is using an external cloud provider."""

        if self.endpoint == "kube-control":
            # determine has_xcp from the kube-control relation
            for relation in self.relations:
                for unit in relation.units:
                    if xcp := relation.data[unit].get("has-xcp"):
                        if xcp.lower() == "true":
                            return True
        elif self.endpoint == "external-cloud-provider":
            # True if any units are joined on this relation.
            return bool(self.relations)

        return False

    @cached_property
    def _vendor(self):
        """
        Since the external-cloud-provider is joined, but no name is
        found over the relation, we can guess the cloud name using
        dmidecode.
        """
        try:
            vendor = check_output(["dmidecode", "-s", "system-manufacturer"])
        except CalledProcessError as e:
            log.warning("dmidecode failure: %s", e)
            return None
        return vendor.decode()

    @cached_property
    def name(self) -> Optional[str]:
        """Name of the cloud-provider."""
        vendor = self._vendor
        if vendor:
            log.info(f"Determined this cloud provider is {vendor}")
        else:
            log.warning(f"Cannot determine cloud provider from {vendor}")
            return None

        for cloud in CLOUD_PROVIDERS:
            if cloud["vendor"] in vendor:
                return cloud["name"]

        log.warning(f"Failed to identify cloud from machine's vendor: {vendor}")

    @cached_property
    def provider_id(self) -> Optional[str]:
        """Retrieve the cloud provider-id for this node"""
        provider_id = None
        if self.name == "vsphere":
            vsphere_id = Path(VSPHERE_METADATA).read_text()
            provider_id = f"vsphere:///{vsphere_id.strip()}"
        elif self.name == "openstack" and self.metadata:
            provider_id = f"openstack:///{self.metadata['uuid']}"
        elif self.name == "azure" and self.metadata:
            provider_id = self.metadata["compute"]["vmId"]
        elif self.name == "gce" and self.metadata:
            provider_id = self.metadata["id"]
        if provider_id:
            log.info(f"Determined this node's provider-id is {provider_id}")
        else:
            log.warning("Cannot determine this node's provider-id")
        return provider_id

    @cached_property
    def metadata(self) -> Optional[dict]:
        """Fetch instance metadata on this cloud environment."""
        if self.name == "openstack":
            metadata_req = urlopen(OPENSTACK_METADATA)
            metadata = metadata_req.read() if metadata_req.status == 200 else None
            return json.loads(metadata) if metadata else None
        elif self.name == "azure":
            req = Request(AZURE_METADATA, headers={"Metadata": "true"})
            metadata_req = urlopen(req)
            metadata = metadata_req.read() if metadata_req.status == 200 else None
            return json.loads(metadata) if metadata else None
        elif self.name == "gce":
            req = Request(GOOGLE_METADATA, headers={"Metadata-Flavor": "Google"})
            metadata_req = urlopen(req)
            return {"id": metadata_req.read()} if metadata_req.status == 200 else None


class ExternalCloudProviderProvides(ExternalCloudProvider):
    """Implements the Provides side of the external-cloud-provider interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint
        self.set_name(self.name)

    def set_name(self, name: str):
        """Set the provider name."""
        for relation in self.relations:
            relation.data[self.unit]["provider-name"] = name
