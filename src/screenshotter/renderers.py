import base64

from rest_framework import renderers


class PNGRenderer(renderers.BaseRenderer):
    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class Base64JSONRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, dict):
            json_ready = data
        else:
            base64_encoded_data = base64.b64encode(data).decode('utf-8')
            json_ready = {"base64": base64_encoded_data}
        return super().render(json_ready, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
