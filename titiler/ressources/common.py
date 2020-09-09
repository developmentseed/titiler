"""Commons."""

from typing import Any, Dict

from starlette.responses import Response

extensions = dict(JPEG="jpg", PNG="png", GTiff="tif", WEBP="webp", NPY="npy")

drivers = dict(jpg="JPEG", png="PNG", tif="GTiff", webp="WEBP", npy="NPY")

img_endpoint_params: Dict[str, Any] = {
    "responses": {
        200: {
            "content": {
                "image/png": {},
                "image/jpg": {},
                "image/webp": {},
                "image/tiff": {},
                "application/x-binary": {},
            },
            "description": "Return an image.",
        }
    },
    "response_class": Response,
}
