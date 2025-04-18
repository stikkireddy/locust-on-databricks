import time
from pathlib import Path

from lod.client import LocustClient
from lod.manager import LocustBaseManager, LocustSingleNodeManager, LocustDistributedManager
from lod.proxy import get_proxy_settings_for_port


class LocustRunner:

    def __init__(self, locustfile_path: str | Path, port: int = 8089):
        self._web_port = port
        self._locustfile_path = locustfile_path
        self._distributed = False
        self._locust_manager: LocustBaseManager = LocustSingleNodeManager(
            file_name=locustfile_path, web_port=port
        )
        self._is_locust_running = False
        self._locust_client = LocustClient(
            server_port=port,
        )
        self._proxy_settings = get_proxy_settings_for_port(self._web_port)
        self._preloaded_locust_swarm = None

    def start_locust(self) -> int:
        pid = self._locust_manager.start()
        self._is_locust_running = True
        try:
            import IPython
            display_html = IPython.get_ipython().user_ns["displayHTML"]
            display_text = f'<a href="{self._proxy_settings.get_proxy_url(ensure_ends_with_slash=True)}">Click to go to Access Locust Web UI!</a>'
            display_html(display_text)
        except Exception:
            print(f"Access Locust Web UI at {self._proxy_settings.get_proxy_url(ensure_ends_with_slash=True)}")
        if self._preloaded_locust_swarm:
            print("Preloaded swarm parameters:", self._preloaded_locust_swarm)
            self.run_swarm(**self._preloaded_locust_swarm)
            self._preloaded_locust_swarm = None
        return pid

    def distributed(self, process_to_core_count_ratio: float = 2.0):
        self._distributed = True
        self._locust_manager = LocustDistributedManager(
            file_name=self._locustfile_path,
            web_port=self._web_port,
            process_to_core_count_ratio=process_to_core_count_ratio
        )
        return self

    def stop_locust(self, force: bool = False):
        self._locust_manager.kill(force=force)
        self._is_locust_running = False

    def set_initial_swarm(self,
                          host: str,
                          user_count: int,
                          spawn_rate: int,
                          run_time: str = "5m"):
        if self._is_locust_running:
            raise Exception("Locust is already running. Please stop it before setting initial swarm parameters.")
        else:
            self._preloaded_locust_swarm = {
                'host': host,
                'user_count': user_count,
                'spawn_rate': spawn_rate,
                'run_time': run_time
            }

        return self

    def run_swarm(self,
                  host: str,
                  user_count: int,
                  spawn_rate: int,
                  run_time: str = "5m"):
        if self._is_locust_running:
            self._locust_client.swarm(
                host=host,
                user_count=user_count,
                spawn_rate=spawn_rate,
                run_time=run_time
            )

            timeout_seconds = 60
            start_time = time.time()
            while True:
                if self._locust_client.swarm_is_active():
                    print("Locust swarm is running.")
                    break
                elif time.time() - start_time > timeout_seconds:
                    raise Exception("Timeout waiting for Locust to warm up.")
                time.sleep(0.5)

        else:
            raise Exception("Locust is not running. Please start Locust first.")

    def block_until_end_of_swarm(self, timeout_in_seconds: int, check_every_n_seconds: int = 5):
        if self._is_locust_running:
            import time
            start_time = time.time()
            while True:
                if self._locust_client.swarm_is_active():
                    print(f"Locust swarm is running checking again in another: {check_every_n_seconds}.")
                elif time.time() - start_time > timeout_in_seconds:
                    raise Exception("Timeout waiting for Locust to warm up.")
                else:
                    print("Locust swarm has finished.")
                    break

                time.sleep(check_every_n_seconds)
        else:
            raise Exception("Locust is not running. Please start Locust first.")

    def save_artifacts(self, save_directory: str | Path = "artifacts", file_prefix: str = ""):
        if self._is_locust_running:
            # ensure directory exists
            save_dir = Path(save_directory)
            save_dir.mkdir(parents=True, exist_ok=True)
            csv_export_dict = self._locust_client.get_csv_exports()
            html_report = self._locust_client.get_html_report()
            time_prefix = int(time.time())
            for export_name, export_content in csv_export_dict.items():
                with open(str(save_dir / f"{file_prefix}{time_prefix}_{export_name}.csv"), 'w') as f:
                    f.write(export_content)
            with open(str(save_dir / f"{file_prefix}{time_prefix}_report.html"), 'w') as f:
                f.write(html_report)
        else:
            raise Exception("Locust is not running. Please start Locust first.")

    def display_report_snapshot(self):
        if self._is_locust_running:
            import IPython
            display_html = IPython.get_ipython().user_ns["displayHTML"]
            html_content = self._locust_client.get_html_report()
            display_html(html_content)
        else:
            raise Exception("Locust is not running. Please start Locust first.")

    def stop_swarm(self):
        if self._is_locust_running:
            self._locust_client.stop_swarm()
        else:
            raise Exception("Locust is not running. Please start Locust first.")
