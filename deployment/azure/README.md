### Function

TiTiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi), a modern, fast, Python web framework for building APIs. We can make our FastAPI application work as an Azure Function by wrapping it within the [Azure Function Python worker](https://github.com/Azure/azure-functions-python-worker).

If you are not familiar with **Azure functions** we recommend checking https://docs.microsoft.com/en-us/azure/azure-functions/ first.

Minimal TiTiler Azure function code:
```python
import azure.functions as func
from titiler.application.main import cog, mosaic, stac, tms
from fastapi import FastAPI


app = FastAPI()
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])
app.include_router(
    stac.router, prefix="/stac", tags=["SpatioTemporal Asset Catalog"]
)
app.include_router(mosaic.router, prefix="/mosaicjson", tags=["MosaicJSON"])
app.include_router(tms.router, tags=["TileMatrixSets"])


async def main(
    req: func.HttpRequest, context: func.Context,
) -> func.HttpResponse:
    return await func.AsgiMiddleware(app).handle_async(req, context)
```

#### Requirements
- Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
- Azure Function Tool: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local

#### Deployment

See: https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser#create-supporting-azure-resources-for-your-function

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler/deployment/azure

$ az login
$ az group create --name AzureFunctionsTiTiler-rg --location eastus
$ az storage account create --name titilerstorage --sku Standard_LRS -g AzureFunctionsTiTiler-rg
$ az functionapp create --consumption-plan-location eastus --runtime python --runtime-version 3.8 --functions-version 3 --name titiler --os-type linux -g AzureFunctionsTiTiler-rg -s titilerstorage
$ func azure functionapp publish titiler
```

or

use VScode: https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python#publish-the-project-to-azure

##### Docs
- https://docs.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies
- https://docs.microsoft.com/en-us/azure/azure-functions/functions-triggers-bindings
- https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python



