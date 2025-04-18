import abc
import time

import psutil
import socket
import ipaddress
import os
import signal
import subprocess

import requests
from requests import RequestException


def get_rfc_1918_network_ip():
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == socket.AF_INET:
                ip = snic.address
                # Skip loopback addresses
                if ip.startswith("127."):
                    continue
                try:
                    # Validate if the IP is private (RFC1918)
                    if ipaddress.ip_address(ip).is_private:
                        return ip
                except Exception:
                    continue
    # Fallback in case no suitable IP is found
    return None


def is_process_running(host: str, port: int, timeout: int = 10) -> bool:
    start_time = time.time()
    url = f"http://{host}:{port}/logs"

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("Service is up and running.")
                return True
        except RequestException:
            pass  # Connection failed, will retry

        print("Service not yet running, retrying in 1 second...")
        time.sleep(1)  # Wait 1 second before retrying

    return False  # Timed out without getting a 200 response


def is_cluster_running(host: str, port: int, timeout: int = 10) -> bool:
    start_time = time.time()
    url = f"http://{host}:{port}/logs"

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                resp_dict = response.json()
                workers = resp_dict.get("workers")
                if workers and len(workers) > 0:
                    print("Cluster is up and running.")
                    return True
        except RequestException:
            pass  # Connection failed, will retry

        print("Cluster not yet ready, retrying in 1 second...")
        time.sleep(1)  # Wait 1 second before retrying

    return False  # Timed out without getting a 200 response


class LocustUtils:

    @staticmethod
    def is_running_on_current_node() -> bool:
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any("locust" in part.lower() for part in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    @staticmethod
    def kill_on_current_node(force: bool = False) -> bool:
        killed = False
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any("locust" in part.lower() for part in cmdline):
                    if force:
                        # kill -9
                        os.kill(proc.pid, signal.SIGKILL)
                    else:
                        # kill -15
                        os.kill(proc.pid, signal.SIGTERM)
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return killed

    @staticmethod
    def start_standard_on_current_node(file_name: str = "locustfile.py", web_port: int = 8089) -> int:
        master_cmd = f"locust -f {file_name} --web-port {web_port}"
        process = subprocess.Popen(master_cmd.split())
        print(f"Locust started with pid: {process.pid}")
        # Wait for the process to start
        is_process_running("0.0.0.0", web_port)
        return process.pid

    @staticmethod
    def start_driver_on_current_node(file_name: str = "locustfile.py", web_port: int = 8089) -> int:
        master_cmd = f"locust -f {file_name} --master --web-port {web_port}"
        process = subprocess.Popen(master_cmd.split())
        # Wait for the process to start
        is_process_running("0.0.0.0", web_port)
        return process.pid

    @staticmethod
    def start_worker_on_current_node(driver_ip: str, process_to_core_count_ratio: float = 2.0) -> int:
        import multiprocessing
        num_processes = int(multiprocessing.cpu_count() * process_to_core_count_ratio)
        worker_cmd = f"locust -f - --worker --master-host {driver_ip} --processes {num_processes}"
        process = subprocess.Popen(worker_cmd.split())
        return process.pid


class LocustBaseManager(abc.ABC):

    @abc.abstractmethod
    def is_running(self) -> bool:
        pass

    @abc.abstractmethod
    def kill(self, force: bool = False) -> bool:
        pass

    @abc.abstractmethod
    def start(self) -> int:
        pass


class LocustSingleNodeManager(LocustBaseManager):

    def __init__(self, file_name: str = "locustfile.py", web_port: int = 8089):
        self._file_name = file_name
        self._web_port = web_port

    def is_running(self) -> bool:
        return LocustUtils.is_running_on_current_node()

    def kill(self, force: bool = False) -> bool:
        return LocustUtils.kill_on_current_node(force=force)

    def start(self) -> int:
        return LocustUtils.start_standard_on_current_node(
            file_name=self._file_name, web_port=self._web_port
        )


def get_spark():
    from pyspark.sql import SparkSession
    return SparkSession.getActiveSession()


def active_worker_count():
    spark = get_spark()
    return int(spark.conf.get("spark.databricks.clusterUsageTags.clusterWorkers", "1"))


class LocustDistributedManager(LocustBaseManager):

    def __init__(self,
                 file_name: str = "locustfile.py",
                 web_port: int = 8089,
                 process_to_core_count_ratio: float = 2.0):
        self._file_name = file_name
        self._web_port = web_port
        self._process_to_core_count_ratio = process_to_core_count_ratio
        self._active_number_of_workers = active_worker_count()
        self._worker_names = [f"worker-{i}" for i in range(self._active_number_of_workers)]

    def is_running(self) -> bool:
        running_states = {"driver": LocustUtils.is_running_on_current_node()}

        def is_locust_running_on_executor(_executor: str):
            ip = get_rfc_1918_network_ip()
            status = LocustUtils.is_running_on_current_node()
            return _executor, ip, status

        results = get_spark() \
            .sparkContext \
            .parallelize(self._worker_names, self._active_number_of_workers) \
            .map(is_locust_running_on_executor).collect()

        for executor, ip, status in results:
            running_states[f"{executor}-{ip}"] = status

        for key, value in running_states.items():
            print(f"Locust running on {key}: {value}")

        return all(running_states.values())

    def kill(self, force: bool = False) -> bool:
        killed_states = {"driver": LocustUtils.kill_on_current_node(force=force)}

        def kill_on_executor(_executor: str):
            ip = get_rfc_1918_network_ip()
            status = LocustUtils.kill_on_current_node(force=force)
            return _executor, ip, status

        results = get_spark() \
            .sparkContext \
            .parallelize(self._worker_names, self._active_number_of_workers) \
            .map(kill_on_executor).collect()

        for executor, ip, status in results:
            killed_states[f"{executor}-{ip}"] = status

        for key, value in killed_states.items():
            print(f"Locust killed on {key}: {value}")

        return all(killed_states.values())

    def start(self) -> int:
        driver_ip = get_rfc_1918_network_ip()

        driver_pid = LocustUtils.start_driver_on_current_node(file_name=self._file_name, web_port=self._web_port)
        print(f"Driver, IP: {driver_ip} - Locust master started with pid: {driver_pid}.")

        def start_locust_worker(_executor_name: str, _driver_ip: str, _process_to_core_count_ratio: float = 2.0):
            worker_ip = get_rfc_1918_network_ip()
            worker_pid = LocustUtils.start_worker_on_current_node(_driver_ip, _process_to_core_count_ratio)
            return _executor_name, worker_ip, worker_pid

        # Distribute the worker start command using map to collect executor info
        results = get_spark() \
            .sparkContext \
            .parallelize(self._worker_names, self._active_number_of_workers) \
            .map(lambda executor_name: start_locust_worker(executor_name, driver_ip, self._process_to_core_count_ratio)) \
            .collect()

        for executor, ip, pid in results:
            print(f"Executor {executor}, IP: {ip} - Locust worker started with PID: {pid}")

        is_cluster_running("0.0.0.0", self._web_port, timeout=10)

        return driver_pid
