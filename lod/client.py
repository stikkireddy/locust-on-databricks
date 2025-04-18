from typing import Optional, Literal, Dict

import requests


class LocustClient:
    """
    Designed entirely based on the code here; https://github.com/locustio/locust/blob/master/locust/web.py
    """

    def __init__(self, server_host: str = "0.0.0.0", server_port: int = 8089):
        self._session = requests.Session()
        self._server_host = server_host
        self._server_port = server_port
        self._base_url = f"http://{server_host}:{server_port}"

    def swarm(self,
              host: str,
              user_count: int,
              spawn_rate: int,
              run_time: str = "5m") -> requests.Response:
        """
        Start a Locust swarm against the specified host.

        Args:
            host: Target URL to test against (required)
            user_count: Number of simulated users
            spawn_rate: Rate at which users spawn per second
            run_time: How long the test should run (e.g. '5m', '30s')

        Returns:
            Response from the Locust server
        """
        endpoint = f"{self._base_url}/swarm"

        data = {
            'user_count': user_count,
            'spawn_rate': spawn_rate,
            'host': host,
            'run_time': run_time
        }

        try:
            response = self._session.post(endpoint, data=data)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            print(f"Swarm started successfully: {response.text}")
            return response
        except requests.RequestException as e:
            print(f"Error starting swarm: {str(e)}")
            raise

    def stop_swarm(self) -> requests.Response:
        """
        Stop the Locust swarm.

        Returns:
            Response from the Locust server
        """
        endpoint = f"{self._base_url}/stop"

        try:
            response = self._session.get(endpoint)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            print(f"Swarm stopped successfully: {response.text}")
            return response
        except requests.RequestException as e:
            print(f"Error stopping swarm: {str(e)}")
            raise

    def get_state(self) -> Optional[str]:
        """
        Get the current state of the Locust swarm.

        Returns:
            Optional[str]: The current state of the swarm (e.g., 'running', 'stopped'),
                          or None if the state cannot be determined.

        Raises:
            requests.RequestException: If there is an error communicating with the Locust server.
        """
        endpoint = f"{self._base_url}/stats/requests"

        try:
            response = self._session.get(endpoint)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            resp_json = response.json()

            return resp_json.get("state", None)
        except requests.RequestException as e:
            print(f"Error getting swarm state: {str(e)}")
            raise

    def swarm_is_active(self) -> bool:
        """
        Check if the Locust swarm is currently running.

        Returns:
            bool: True if the swarm is in the 'running' state, False otherwise.

        Raises:
            requests.RequestException: If there is an error communicating with the Locust server.
        """
        state = self.get_state()
        return state is not None and state.lower() in ["running", "spawning"]

    def get_html_report(self) -> Optional[str]:
        """
        Get the HTML report of the Locust test.

        Returns:
            Optional[str]: The HTML report as a string, or None if there is an error.
        """
        endpoint = f"{self._base_url}/stats/report"

        try:
            response = self._session.get(endpoint)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.text
        except requests.RequestException as e:
            print(f"Error starting swarm: {str(e)}")
            raise

    def get_csv_export(self, option: Literal["requests", "requests_full_history", "failures", "exceptions"]):
        """
        Get the CSV export of the specified type.

        Args:
            option: The type of CSV export to retrieve. Must be one of "requests", "requests_full_history", "failures", or "exceptions".

        Returns:
            str: The CSV export as a string.

        Raises:
            requests.RequestException: If there is an error communicating with the Locust server.
        """
        if option in ["requests", "failures"]:
            endpoint = f"{self._base_url}/stats/{option}/csv"
        elif option in ["exceptions", "requests_full_history"]:
            endpoint = f"{self._base_url}/{option}/csv"

        try:
            response = self._session.get(endpoint)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.text
        except requests.RequestException as e:
            print(f"Error starting swarm: {str(e)}")
            raise

    def get_csv_exports(self, options: list[Literal["requests", "failures", "exceptions", "stats_history"]] = None) -> Optional[
        Dict[str, str]]:
        """
        Get multiple CSV exports.

        Args:
            options: A list of CSV export types to retrieve. Defaults to ["requests", "failures", "exceptions", "stats_history"].

        Returns:
            dict: A dictionary where the keys are the export types and the values are the CSV exports as strings.
        """
        options = options or ["requests", "failures", "exceptions", "stats_history"]
        return {option: self.get_csv_export(option) for option in options}
