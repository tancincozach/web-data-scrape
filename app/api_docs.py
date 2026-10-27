import json

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_GET


@require_GET
def scalar_docs(request):
    """Render the Scalar API reference for the generated OpenAPI schema."""
    schema_url = getattr(settings, "SCALAR_OPENAPI_URL", None) or reverse("api-schema")
    title = escape(settings.SCALAR_TITLE)
    scalar_js_url = settings.SCALAR_JS_URL

    html = f"""<!doctype html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="robots" content="noindex" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module">
      import {{ createApiReference }} from {json.dumps(scalar_js_url)}

      createApiReference('#app', {{
        url: {json.dumps(schema_url)},
      }})
    </script>
  </body>
</html>"""
    return HttpResponse(html, content_type="text/html")
