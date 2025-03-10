import requests

class LocustClient:

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