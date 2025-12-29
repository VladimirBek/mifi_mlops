import random
from locust import HttpUser, task, between


PAYLOAD = {
    "LIMIT_BAL": 200000,
    "SEX": 2,
    "EDUCATION": 2,
    "MARRIAGE": 1,
    "AGE": 35,
    "PAY_0": 0,
    "PAY_2": 0,
    "PAY_3": 0,
    "PAY_4": 0,
    "PAY_5": 0,
    "PAY_6": 0,
    "BILL_AMT1": 50000,
    "BILL_AMT2": 48000,
    "BILL_AMT3": 47000,
    "BILL_AMT4": 46000,
    "BILL_AMT5": 45000,
    "BILL_AMT6": 44000,
    "PAY_AMT1": 2000,
    "PAY_AMT2": 2000,
    "PAY_AMT3": 2000,
    "PAY_AMT4": 2000,
    "PAY_AMT5": 2000,
    "PAY_AMT6": 2000,
}


class PredictUser(HttpUser):
    wait_time = between(0.0, 0.01)  # почти без паузы

    @task
    def predict(self):
        # небольшая рандомизация, чтобы не был один и тот же запрос
        p = dict(PAYLOAD)
        p["LIMIT_BAL"] = p["LIMIT_BAL"] + random.randint(-50000, 50000)
        p["AGE"] = max(18, min(80, p["AGE"] + random.randint(-5, 5)))

        with self.client.post("/predict", json=p, catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
