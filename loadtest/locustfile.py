from locust import HttpUser, task, between
import random

TOKENS_CACHE = []
SLUGS_CACHE = []
LANGS_CACHE = []

class PatientUser(HttpUser):
    wait_time = between(0.3, 2.0)

    def on_start(self):
        global TOKENS_CACHE, SLUGS_CACHE, LANGS_CACHE
        # Fetch lightweight lists from server (simple endpoints are already public)
        if not TOKENS_CACHE:
            r = self.client.get("/admin/login/?next=/")  # warm TLS/headers
        # we can't list tokens without admin; so accept preset env var or seed some manual URLs
        # You can paste a few tokens here for quick start:
        # TOKENS_CACHE = ["abc", "def"]
        # Fall back to hits on portal home/subtopic/video for a fixed clinic & language if you prefer.

    @task(3)
    def open_token(self):
        if not TOKENS_CACHE:
            return
        t = random.choice(TOKENS_CACHE)
        self.client.get(f"/s/{t}/")

    @task(2)
    def browse_home(self):
        if not all([SLUGS_CACHE, LANGS_CACHE]):
            return
        slug = random.choice(SLUGS_CACHE); lang = random.choice(LANGS_CACHE)
        self.client.get(f"/p/{slug}/{lang}/")

    @task(2)
    def browse_subtopic_video(self):
        # hit a couple of fixed pages if you know slugs
        pass  # fill in quickly once you know a few subtopic/video slugs
