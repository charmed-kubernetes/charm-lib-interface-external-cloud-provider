import json
import logging
from functools import cached_property
from subprocess import CalledProcessError, check_output
from typing import List, Optional

from ops import CharmBase, Relation, Unit

log = logging.getLogger(__name__)

CLOUD_PROVIDERS = [
    {"name": "aws", "vendor": "Amazon"},
    {"name": "openstack", "vendor": "OpenStack"},
    {"name": "azure", "vendor": "Microsoft"},
    {"name": "gcp", "vendor": "Google"},
    {"name": "vsphere", "vendor": "VMware"},
]


class ExternalCloudProviderBase:
    @property
    def relations(self) -> List[Relation]:
        return self.charm.model.relations[self.endpoint]

    @cached_property
    def hostnamectl(self):
        """
        Since the external-cloud-provider is joined, but no name is
        found over the relation, we can guess the cloud name using
        hostnamectl.
        """
        try:
            hostnamectl = check_output("hostnamectl", "--json=short")
        except CalledProcessError as e:
            log.warning("hostnamectl failure", e)
            return None

        return json.loads(hostnamectl)


class ExternalCloudProviderRequires:
    """Implements the Requires side of the external-cloud-provider interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    @property
    def name(self) -> Optional[str]:
        """Name of the cloud-provider."""
        for relation in self.relations:
            for unit in relation.units:
                if name := relation.data[unit].get("name"):
                    return name

        vendor = self.hostnamectl.get("HardwareVendor")
        if not vendor:
            log.warning(
                f"Failed to detect cloud vendor from hostnamectl {self.hostnamectl}"
            )
            return None

        for cloud in CLOUD_PROVIDERS:
            if cloud["vendor"] in vendor:
                return cloud["name"]

        log.warning(f"Failed to identify cloud from machine's vendor: {vendor}")

    @property
    def unit(self) -> Unit:
        return self.charm.unit


class ExternalCloudProviderProvides:
    """Implements the Provides side of the external-cloud-provider interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint
        self.set_name(self.name)

    def set_name(self, name: str):
        """Set the provider name."""
        for relation in self.relations:
            relation.data[self.unit]["name"] = name

    @property
    def unit(self) -> Unit:
        return self.charm.unit
