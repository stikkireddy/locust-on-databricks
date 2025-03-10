from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


def remove_lowest_subdomain_from_host(url):
    parsed_url = urlparse(url)
    host = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    parts = host.split('.')
    # Check if there are subdomains to remove
    if len(parts) > 2:
        # Remove the lowest subdomain
        parts.pop(0)

    # Reconstruct the modified host
    modified_host = '.'.join(parts)

    return modified_host


class ClusterUtils:

    def __init__(self):
        from pyspark.sql import SparkSession
        self._spark = SparkSession.getActiveSession()

    @property
    def workspace_url(self):
        return self._spark.conf.get("spark.databricks.workspaceUrl")

    @property
    def org_id(self):
        return self._spark.conf.get("spark.databricks.clusterUsageTags.orgId")

    @property
    def cluster_id(self):
        return self._spark.conf.get("spark.databricks.clusterUsageTags.clusterId")

    @property
    def cloud(self):
        url = self.workspace_url
        if url.endswith("azuredatabricks.net"):
            return "azure"
        if ".gcp." in url:
            return "gcp"
        return "aws"


@dataclass
class ProxySettings:
    proxy_url: str
    port: str
    url_base_path: str
    url_base_path_no_port: Optional[str] = None

    def get_proxy_url(self, ensure_ends_with_slash=False):
        """
        For certain apps that use relative paths like "assets/index-*.js" we need to ensure that the url ends
        with a slash.
        """
        if ensure_ends_with_slash is True:
            return self.proxy_url.rstrip("/") + "/"
        return self.proxy_url


def get_cloud_proxy_settings(cloud: str,
                             org_id: str,
                             cluster_id: str,
                             port: int,
                             host: str) -> ProxySettings:
    cloud_norm = cloud.lower()
    if cloud_norm not in ["aws", "azure"]:
        raise Exception("only supported in aws or azure")
    prefix_url_settings = {
        "aws": "https://dbc-dp-",
        "azure": "https://adb-dp-",
    }
    suffix_url_settings = {
        "azure": "azuredatabricks.net",
    }
    if cloud_norm == "aws":
        suffix = remove_lowest_subdomain_from_host(host)
        suffix_url_settings["aws"] = suffix

    org_shard = ""
    # org_shard doesnt need a suffix of "." for dnsname its handled in building the url
    # only azure right now does dns sharding
    # gcp will need this
    if cloud_norm == "azure":
        org_shard_id = int(org_id) % 20
        org_shard = f".{org_shard_id}"

    url_base_path_no_port = f"/driver-proxy/o/{org_id}/{cluster_id}"
    url_base_path = f"{url_base_path_no_port}/{port}/"
    return ProxySettings(
        proxy_url=f"{prefix_url_settings[cloud_norm]}{org_id}{org_shard}.{suffix_url_settings[cloud_norm]}{url_base_path}",
        port=str(port),
        url_base_path=url_base_path,
        url_base_path_no_port=url_base_path_no_port
    )


def get_proxy_settings_for_port(port: int) -> ProxySettings:
    utils = ClusterUtils()
    print("Proxy Inputs", utils.cloud, utils.cluster_id, utils.org_id, utils.workspace_url)
    return get_cloud_proxy_settings(utils.cloud, utils.org_id, utils.cluster_id, port, utils.workspace_url)
