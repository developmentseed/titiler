In addition to the `/cog`, `/stac` and `/mosaicjson` endpoints, the `titiler.application` package FastAPI application commes with additional metadata endpoints.

# Algorithms

## API

| Method | URL                          | Output | Description
| ------ | ---------------------------- |--------|--------------
| `GET`  | `/colorMaps`                 | JSON   | retrieve the list of available colorMaps
| `GET`  | `/colorMaps/{colorMapId}`    | JSON   | retrieve the metadata or image of the specified colorMap.

## Description


### List colormaps

`:endpoint:/colorMaps` - Get the list of supported ColorMaps

```bash
$ curl https://myendpoint/colorMaps | jq

{
  "colorMaps": [
    "dense_r",
    "delta",
    ...
  ],
  "links": [
    {
      "href": "http://myendpoint/colorMaps",
      "rel": "self",
      "type": "application/json",
      "title": "List of available colormaps"
    },
    {
      "href": "http://myendpoint/colorMaps/{colorMapId}",
      "rel": "data",
      "type": "application/json",
      "templated": true,
      "title": "Retrieve colormap metadata"
    },
    {
      "href": "http://myendpoint/colorMaps/{colorMapId}?format=png",
      "rel": "data",
      "type": "image/png",
      "templated": true,
      "title": "Retrieve colormap as image"
    }
  ]
}
```

### Get ColorMap metadata or as image

`:endpoint:/colorMaps/{colorMapId}` - Get the ColorMap metadata or image

- PathParams:
    - **colorMapId**: colormap name

- QueryParams:
    - **format** (str): output image format (PNG/JPEG...). Defaults to JSON output.
    - **orientation** (["vertical", "horizontal"]): image orientation. Defaults to `horizontal`.
    - **height** (int): output image height. Default to 20px for horizontal or 256px for vertical.
    - **width** (int): output image width. Defaults to 256px for horizontal or 20px for vertical.

```bash
$ curl http://myendpoint/colorMaps/viridis | jq

{
  "0": [
    68,
    1,
    84,
    255
  ],
  ...
  "255": [
    253,
    231,
    36,
    255
  ]
}
```

```
curl http://myendpoint/colorMaps/viridis?format=png
```

```
curl http://myendpoint/colorMaps/viridis?format=png&orientation=vertical
```

```
curl http://myendpoint/colorMaps/viridis?format=png&orientation=vertical&width=100&height=1000
```
