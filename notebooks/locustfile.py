from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 10)

    @task
    def hello_world(self):
        self.client.get("/")