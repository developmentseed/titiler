window.BENCHMARK_DATA = {
  "lastUpdate": 1690464642157,
  "repoUrl": "https://github.com/developmentseed/titiler",
  "entries": {
    "TiTiler performance Benchmarks": [
      {
        "commit": {
          "author": {
            "email": "vincent.sarago@gmail.com",
            "name": "Vincent Sarago",
            "username": "vincentsarago"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "e0803c459891325e83bd81eeb91a1620ca601425",
          "message": "add benchmark comparison (#676)\n\n* add benchmark comparison\r\n\r\n* fix",
          "timestamp": "2023-07-27T15:24:49+02:00",
          "tree_id": "7f8c4083580feff65b9e26df03ffe4c9d481d1a1",
          "url": "https://github.com/developmentseed/titiler/commit/e0803c459891325e83bd81eeb91a1620ca601425"
        },
        "date": 1690464400830,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "WebMercator data_transferred",
            "value": 5.29,
            "unit": "Megabytes"
          },
          {
            "name": "WebMercator response_time",
            "value": 0.04,
            "unit": "s"
          },
          {
            "name": "WebMercator longest_transaction",
            "value": 0.07,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad elapsed_time",
            "value": 5.77,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad data_transferred",
            "value": 5.18,
            "unit": "Megabytes"
          },
          {
            "name": "WGS1984Quad response_time",
            "value": 0.06,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad longest_transaction",
            "value": 0.07,
            "unit": "s"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "vincent.sarago@gmail.com",
            "name": "vincentsarago",
            "username": "vincentsarago"
          },
          "committer": {
            "email": "vincent.sarago@gmail.com",
            "name": "vincentsarago",
            "username": "vincentsarago"
          },
          "distinct": true,
          "id": "f23c5da86800b5880a15cacd72c96c6f15f0f6fd",
          "message": "add benchmark doc",
          "timestamp": "2023-07-27T15:28:43+02:00",
          "tree_id": "6d178803600186b2ce626658008b0b2a10ddbcef",
          "url": "https://github.com/developmentseed/titiler/commit/f23c5da86800b5880a15cacd72c96c6f15f0f6fd"
        },
        "date": 1690464641150,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "WebMercator data_transferred",
            "value": 5.29,
            "unit": "Megabytes"
          },
          {
            "name": "WebMercator response_time",
            "value": 0.04,
            "unit": "s"
          },
          {
            "name": "WebMercator longest_transaction",
            "value": 0.07,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad elapsed_time",
            "value": 5.72,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad data_transferred",
            "value": 5.18,
            "unit": "Megabytes"
          },
          {
            "name": "WGS1984Quad response_time",
            "value": 0.06,
            "unit": "s"
          },
          {
            "name": "WGS1984Quad longest_transaction",
            "value": 0.08,
            "unit": "s"
          }
        ]
      }
    ]
  }
}