from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ClientAuthenticationScheme(OpenApiAuthenticationExtension):
    """Describe the two headers required by ClientAuthentication."""

    target_class = "app.client_management.authentication.ClientAuthentication"
    name = ["clientId", "clientSecret"]

    def get_security_definition(self, auto_schema):
        return [
            {
                "type": "apiKey",
                "in": "header",
                "name": "X-Client-ID",
                "description": "Client identifier issued by create_client.",
            },
            {
                "type": "apiKey",
                "in": "header",
                "name": "X-Client-Secret",
                "description": "Client secret issued once when the client is created or rotated.",
            },
        ]
