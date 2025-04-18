import logging
from locust import events
from locust.env import Environment


@events.cpu_warning.add_listener
def handle_cpu_warning(*args, environment: Environment, cpu_usage: float, **kwargs):
    logging.error(f"CPU OVER UTILIZATION: {cpu_usage}%")
    logging.error("STOPPING SWARM EARLY...")
    logging.error("Please use larger instance type, distributed or reduce the number of users.")
    environment.runner.quit()
