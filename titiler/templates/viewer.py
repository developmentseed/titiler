"""titiler: Viewer template."""


def viewer_template(endpoint: str) -> str:
    """Titiler viewer."""
    return f"""<!DOCTYPE html>
    <html>
      <head>
        <meta charset='utf-8' />
        <title>Titiler viewer</title>
        <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no'/>

        <script src='https://npmcdn.com/@turf/turf@3.5.1/turf.min.js'></script>

        <script src='https://api.tiles.mapbox.com/mapbox-gl-js/v1.0.0/mapbox-gl.js'> </script>
        <link href='https://api.tiles.mapbox.com/mapbox-gl-js/v1.0.0/mapbox-gl.css' rel='stylesheet'/>

        <link href="https://api.mapbox.com/mapbox-assembly/v0.23.2/assembly.min.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-assembly/v0.23.2/assembly.js"></script>

        <style>
          body {{ margin:0; padding:0; }}
          #map {{ position:absolute; top:0; bottom:0; width:100%; }}
          .loading-map {{
                position: absolute;
                width: 100%;
                height: 100%;
                color: #FFF;
                background-color: #000;
                text-align: center;
                opacity: 0.5;
                font-size: 45px;
            }}
            .loading-map.off {{
                opacity: 0;
                -o-transition: all .5s ease;
                -webkit-transition: all .5s ease;
                -moz-transition: all .5s ease;
                -ms-transition: all .5s ease;
                transition: all ease .5s;
                visibility:hidden;
            }}
            .middle-center {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            }}
            .middle-center * {{ display: block; padding: 5px; }}
        </style>
      </head>
      <body>
        <div  id='selector' class='fixed top right bottom left scroll-auto bg-darken25 z3'>
          <div class='bg-white middle-center w600 px12 py12 round'>
            <div class='txt-h5 mt6 mb6 color-black'>Enter COG url</div>
            <input id="cog" class='input wmax-full inline-block' value="" placeholder='COG url here'/>
            <button id="launch" class='btn bts--xs btn--stroke bg-darken25-on-hover inline-block mt12 '>Apply</button>
          </div>
        </div>

        <div id='map'>
          <div id='loader' class="loading-map z2">
            <div class="middle-center">
              <div class="round animation-spin animation--infinite animation--speed-1">
                <svg class='icon icon--l inline-block'><use xlink:href='#icon-satellite'/></svg>
              </div>
            </div>
          </div>
        </div>

        <script>
          var map = new mapboxgl.Map({{
              container: 'map',
              style: {{ version: 8, sources: {{}}, layers: [] }},
              center: [-119.5591, 37.715],
              zoom: 5
          }});

          const addAOI = (bounds) => {{
            const geojson = {{
                'type': 'FeatureCollection', 'features': [ turf.bboxPolygon(bounds) ]
            }}

            map.addSource('aoi', {{ 'type': 'geojson', 'data': geojson }})

            map.addLayer({{
              id: 'aoi-polygon',
              type: 'line',
              source: 'aoi',
              layout: {{ 'line-cap': 'round', 'line-join': 'round' }},
              paint: {{ 'line-color': '#3bb2d0', 'line-width': 2 }}
            }})
            return
          }}

          const addCogLayer = (cogUrl) => {{
            let tilejsonUrl = `{endpoint}/tilejson.json?url=${{cogUrl}}`

            return fetch(tilejsonUrl)
              .then(res => {{
                if (res.ok) return res.json()
                throw new Error('Network response was not ok.')
              }})
              .then(data => {{
                map.addSource('raster', {{ type: 'raster', url: tilejsonUrl }})
                map.addLayer({{ id: 'raster', type: 'raster', source: 'raster' }})

                document.getElementById('loader').classList.toggle('off')
                const bounds = data.bounds
                addAOI(bounds)
                map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])
              }})
          }}

          document.getElementById('launch').addEventListener('click', () => {{
            addCogLayer(document.getElementById('cog').value, {{}})
              .then(() => {{
                  document.getElementById('selector').classList.toggle('none')
              }})
              .catch(err => {{
                console.warn(err)
              }})
          }})

        </script>

      </body>
    </html>"""
