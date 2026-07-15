from .utils import generate_a_bogus, generate_fake_webid, generate_msToken, generate_webid, splice_url


class Params:
    def __init__(self):
        self.params = {}

    def with_platform(self):
        self.params.update(
            {
                "device_platform": "webapp",
                "aid": "6383",
                "channel": "channel_pc_web",
                "pc_client_type": "1",
                "update_version_code": "170400",
                "version_code": "170400",
                "version_name": "17.4.0",
                "cookie_enabled": "true",
                "screen_width": "1707",
                "screen_height": "960",
                "browser_language": "zh-CN",
                "browser_platform": "Win32",
                "browser_name": "Edge",
                "browser_version": "125.0.0.0",
                "browser_online": "true",
                "engine_name": "Blink",
                "engine_version": "125.0.0.0",
                "os_name": "Windows",
                "os_version": "10",
                "cpu_core_num": "32",
                "device_memory": "8",
                "platform": "PC",
                "downlink": "10",
                "effective_type": "4g",
                "round_trip_time": "100",
            }
        )
        return self

    def update_params(self, params):
        self.params.update(params)
        return self

    def with_web_id(self, auth=None, url="", fake=False):
        self.params["webid"] = generate_fake_webid() if fake else generate_webid(auth, url)
        return self

    def with_a_bogus(self, data=None):
        query = splice_url(self.get())
        data_str = splice_url(data) if data is not None else ""
        self.add_param("a_bogus", generate_a_bogus(query, data_str))
        return self

    def with_ms_token(self):
        self.params["msToken"] = generate_msToken()
        return self

    def add_param(self, key, value):
        self.params[key] = value
        return self

    def get(self):
        return self.params

    def toString(self):
        return "&".join([f"{k}={v}" for k, v in self.params.items()])
