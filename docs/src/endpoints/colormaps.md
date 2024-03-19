In addition to the `/cog`, `/stac` and `/mosaicjson` endpoints, the `titiler.application` package FastAPI application commes with additional metadata endpoints.

# Algorithms

## API

| Method | URL                          | Output | Description
| ------ | ---------------------------- |--------|--------------
| `GET`  | `/colormaps`                 | JSON   | retrieve the list of available colormaps
| `GET`  | `/colormaps/{colormapId}`    | JSON   | retrieve the metadata or image of the specified colormap.

## Description


### List colormaps

`:endpoint:/colormaps` - Get the list of supported ColorMaps

```bash
$ curl https://myendpoint/colormaps | jq

{
  "colormaps": [
    "dense_r",
    "delta",
    ...
  ],
  "links": [
    {
      "href": "http://myendpoint/colormaps",
      "rel": "self",
      "type": "application/json",
      "title": "List of available colormaps"
    },
    {
      "href": "http://myendpoint/colormaps/{colormapId}",
      "rel": "data",
      "type": "application/json",
      "templated": true,
      "title": "Retrieve colormap metadata"
    },
    {
      "href": "http://myendpoint/colormaps/{colormapId}?format=png",
      "rel": "data",
      "type": "image/png",
      "templated": true,
      "title": "Retrieve colormap as image"
    }
  ]
}
```

### Get ColorMap metadata or as image

`:endpoint:/colormaps/{colormapId}` - Get the ColorMap metadata or image

- PathParams:
    - **colormapId**: colormap name

- QueryParams:
    - **format** (str): output image format (PNG/JPEG...). Defaults to JSON output.
    - **orientation** (["vertical", "horizontal"]): image orientation. Defaults to `horizontal`.
    - **height** (int): output image height. Default to 20px for horizontal or 256px for vertical.
    - **width** (int): output image width. Defaults to 256px for horizontal or 20px for vertical.

```bash
$ curl http://myendpoint/colormaps/viridis | jq

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
curl http://myendpoint/colormaps/viridis?format=png
```

```
curl http://myendpoint/colormaps/viridis?format=png&orientation=vertical
```

```
curl http://myendpoint/colormaps/viridis?format=png&orientation=vertical&width=100&height=1000
```
