Service: boardly-backend
Window: 2026-10-22T23:02:40.030044+00:00 to 2026-10-22T23:17:40.030044+00:00

Requests by route and status code (last 15m):
- /board -> 200: 27.22
- /cards -> 201: 27.22
- /cards/{card_id} -> 200: 27.3, 204: 25.25
- /cards/{card_id}/move -> 200: 65.73, 404: 0.0, 500: 22.16

Routes seen failing in logs: PATCH /cards/{card_id}/move

Error log lines:
- 2026-10-22T23:15:42.244185+00:00 PATCH /cards/{card_id}/move -> 500 card_id=0494a882-419b-4cdd-97b1-2a89aa3df08e trace_id=23079eb60e537fb1ba471c00de16da84: board api request
- 2026-10-22T23:17:14.473762+00:00 PATCH /cards/{card_id}/move -> 500 card_id=04cae680-aac5-4874-a07e-6862d602b71e trace_id=33442aabec14cf3e6e8c224b44aeaaca: board api request
- 2026-10-22T23:15:42.155208+00:00 PATCH /cards/{card_id}/move -> 500 card_id=1737e046-6f04-4df5-bdcc-c6e606486cbf trace_id=6adea5b8f1ede475366a29e16602eb1e: board api request
- 2026-10-22T23:15:42.332133+00:00 PATCH /cards/{card_id}/move -> 500 card_id=18cf6a69-7a29-4a64-976a-dc04939472d8 trace_id=62dfeabb68f7afcd7b541d16f7ead6ee: board api request
- 2026-10-22T23:15:42.596464+00:00 PATCH /cards/{card_id}/move -> 500 card_id=23e35cde-982d-45f7-9e9b-6b6b9afdebad trace_id=eeafb6dcd7e71197edc519f370c78fc7: board api request
- 2026-10-22T23:17:14.371130+00:00 PATCH /cards/{card_id}/move -> 500 card_id=2bb48e26-5a9d-4f76-9449-9f4a83d6d077 trace_id=21c156faa7871e6fb8d6ebcfdb6b7143: board api request
- 2026-10-22T23:15:43.473397+00:00 PATCH /cards/{card_id}/move -> 500 card_id=2fffb5f8-271b-4681-92e4-64f3278fd883 trace_id=62ea426b7ed01d074f952b709096328f: board api request
- 2026-10-22T23:15:43.297601+00:00 PATCH /cards/{card_id}/move -> 500 card_id=31e6ab94-7293-4859-972b-0f2b3ee4718e trace_id=db0c9818b20d56031546d6d5ad83a9d5: board api request
- 2026-10-22T23:15:43.648571+00:00 PATCH /cards/{card_id}/move -> 500 card_id=32b1b791-7541-497a-96cd-7d53da1a1460 trace_id=6a877f2b32b35a8e7c3860422a98d78e: board api request
- 2026-10-22T23:16:13.116066+00:00 PATCH /cards/{card_id}/move -> 500 card_id=48e235b8-031b-41a4-833f-03de7d85a900 trace_id=00e2c0b996b361d2b781d1a8c6f1b4be: board api request
- 2026-10-22T23:15:42.427002+00:00 PATCH /cards/{card_id}/move -> 500 card_id=4bcff6a7-ff29-431e-8212-0861dfde3e2b trace_id=357695965e707dd5de39a156bbc8cdc1: board api request
- 2026-10-22T23:15:43.561703+00:00 PATCH /cards/{card_id}/move -> 500 card_id=5ac6ad12-79ad-46eb-819c-830f21e6e1b3 trace_id=27785dd83ae167197c3cc2b0520ff36f: board api request
- 2026-10-22T23:17:14.270999+00:00 PATCH /cards/{card_id}/move -> 500 card_id=65ed22dc-ce7e-475b-ad48-99281ff9ff00 trace_id=da5c5ceb2321a096fc3206a1eb985b75: board api request
- 2026-10-22T23:15:43.024826+00:00 PATCH /cards/{card_id}/move -> 500 card_id=6ca6c4b8-c556-428f-ad04-f3c0a6084f28 trace_id=19a2418c6d8fd076838b20f549e5836f: board api request
- 2026-10-22T23:15:42.682737+00:00 PATCH /cards/{card_id}/move -> 500 card_id=7a7900bc-0420-4d4d-a476-9622b01008ee trace_id=5978495ce2c0c4446c116e64d5d785ca: board api request
- 2026-10-22T23:15:43.210656+00:00 PATCH /cards/{card_id}/move -> 500 card_id=85a68c95-5eca-4995-8edc-986437d64ec6 trace_id=3da40e4e22e39ffe9f47d0b5f88a0cca: board api request
- 2026-10-22T23:16:43.851460+00:00 PATCH /cards/{card_id}/move -> 500 card_id=8c8c660d-0167-4047-af75-0632a207f78b trace_id=d2205f363772ce944e67b893ea486d72: board api request
- 2026-10-22T23:15:43.110444+00:00 PATCH /cards/{card_id}/move -> 500 card_id=8fc94c10-f78d-4e92-959c-243cdc6ad6d5 trace_id=6bd32daba790d9666e3273d12b0a9ca6: board api request
- 2026-10-22T23:15:42.768017+00:00 PATCH /cards/{card_id}/move -> 500 card_id=a0b6bcc3-4ae6-4a00-9bf5-f0da59f8ae76 trace_id=6d1c11da4c27418e829a5ba371e555c2: board api request
- 2026-10-22T23:16:43.513973+00:00 PATCH /cards/{card_id}/move -> 500 card_id=b2b20572-1440-4a18-a2a7-4a396789fc23 trace_id=36bd4ca8d7aa44ad8e6739c30999bf73: board api request

Error trace IDs (Tempo): 41502acc19cb7afef38eeba8f355790, fa798f77c2560e5a48a8f8ba08b5f90, 19a2418c6d8fd076838b20f549e5836f, 1a68f3276abb6dce6757c4ab34d65794, 23079eb60e537fb1ba471c00de16da84