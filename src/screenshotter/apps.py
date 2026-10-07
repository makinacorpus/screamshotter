from django.apps import AppConfig


class WebConfig(AppConfig):
    name = 'screenshotter'

    def ready(self):
        # Register current process as a subreaper on Linux
        # so orphaned child processes are re-parented to this process instead of leaking to PID 1
        try:
            import ctypes
            libc = ctypes.CDLL('libc.so.6')
            PR_SET_CHILD_SUBREAPER = 36
            libc.prctl(PR_SET_CHILD_SUBREAPER, 1)
        except Exception:
            pass
