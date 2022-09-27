from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, FastAPI

from saleor_app.endpoints import install, manifest
from saleor_app.schemas.core import DomainName, WebhookData
from saleor_app.schemas.manifest import Manifest
from saleor_app.webhook import WebhookRoute, WebhookRouter


class SaleorApp(FastAPI):
    def __init__(
        self,
        *,
        manifest: Manifest,
        validate_domain: Callable[[DomainName], Awaitable[bool]],
        save_app_data: Callable[[DomainName, str, WebhookData], Awaitable],
        use_insecure_saleor_http: bool = False,
        development_auth_token: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.manifest = manifest

        self.validate_domain = validate_domain
        self.save_app_data = save_app_data

        self.use_insecure_saleor_http = use_insecure_saleor_http
        self.development_auth_token = development_auth_token

        self.configuration_router = APIRouter(
            prefix="/configuration", tags=["configuration"]
        )

    def include_saleor_app_routes(self):
        self.configuration_router.get(
            "/manifest", response_model=Manifest, name="manifest", response_model_exclude_none=True
        )(manifest)
        self.configuration_router.post(
            "/install",
            responses={
                400: {"description": "Missing required header"},
                403: {"description": "Incorrect token or not enough permissions"},
            },
            name="app-install",
        )(install)

        self.include_router(self.configuration_router)

    def include_webhook_router(
        self, get_webhook_details: Callable[[DomainName], Awaitable[WebhookData]]
    ):
        self.get_webhook_details = get_webhook_details
        self.webhook_router = WebhookRouter(
            prefix="/webhook",
            responses={
                400: {"description": "Missing required header"},
                401: {"description": "Incorrect signature"},
                404: {"description": "Incorrect saleor event"},
            },
            route_class=WebhookRoute,
        )

        self.include_router(self.webhook_router)
