# mev-boost-py

Python wrapper for querying mev-boost data. This tool provides easy access to Ethereum proposer payload data from Flashbots relays, allowing users to query both "holesky" and "mainnet" networks. It supports fetching data for specific slot ranges or the most recent slots. This is most useful for streaming the most recent 200 mev-boost slots directly to a json file.

## Features
- Fetch proposer payloads from Flashbots relays
- Supports both "holesky" and "mainnet" networks
- Specify slot ranges or fetch the most recent data
- Save data to JSON files for flexible analysis

## Installation
To install `mev-boost-py`, use pip `pip install mev-boost-py`


# Usage Instructions:
## Run from CLI:
```python src/mev_boost_py/proposer_payload.py --network mainnet --start_slot 2447969 --end_slot 2448969 --directory output_folder```
This command will fetch proposer payloads from the "mainnet" network for the specified slot range and save them in the "output_folder". If output_folder is not specified, it will default to "data" folder.

## Run from Python Code:
```python
from mev_boost_py.proposer_payload import ProposerPayloadFetcher, Network

# Create an instance with the desired configuration
fetcher = ProposerPayloadFetcher(
    network=Network.HOLESKY,
    start_slot=2447969,
    end_slot=2448969,
    directory="output_folder"
)

# Execute the fetch operation
fetcher.run()
```

## Example Json File:
```[
  {
    "slot": 2447969,
    "parent_hash": "0x...",
    "block_hash": "0x...",
    "builder_pubkey": "0x...",
    "proposer_pubkey": "0x...",
    "proposer_fee_recipient": "0x...",
    "gas_limit": 30000000,
    "gas_used": 21000,
    "value": 1000000000000000000,
    "num_tx": 1,
    "block_number": 12345678
  },
  ...
]
```

## Example DataFrame Output:

Schema:
```Schema({'slot': String, 'parent_hash': String, 'block_hash': String, 'builder_pubkey': String, 'proposer_pubkey': String, 'proposer_fee_recipient': String, 'gas_limit': String, 'gas_used': String, 'value': String, 'num_tx': String, 'block_number': String})```

Data:
```┌─────────┬─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┬───┬──────────┬───────────────────┬────────┬──────────────┐
│ slot    ┆ parent_hash                     ┆ block_hash                      ┆ builder_pubkey                  ┆ … ┆ gas_used ┆ value             ┆ num_tx ┆ block_number │
│ ---     ┆ ---                             ┆ ---                             ┆ ---                             ┆   ┆ ---      ┆ ---               ┆ ---    ┆ ---          │
│ str     ┆ str                             ┆ str                             ┆ str                             ┆   ┆ str      ┆ str               ┆ str    ┆ str          │
╞═════════╪═════════════════════════════════╪═════════════════════════════════╪═════════════════════════════════╪═══╪══════════╪═══════════════════╪════════╪══════════════╡
│ 2451003 ┆ 0x3739ec860534152c1c16c0fe375e… ┆ 0xc52774ef565609df07506bc4693c… ┆ 0xa3ad1da9373ae97c21274629668d… ┆ … ┆ 5874398  ┆ 9193837799832420  ┆ 39     ┆ 2258300      │
│ 2450989 ┆ 0xf7cab7c264373654e233db6a6124… ┆ 0x17b6a32b12b617b97867c6da88e1… ┆ 0x8cafae64383b537561650b2e3893… ┆ … ┆ 3558221  ┆ 9013912242542186  ┆ 19     ┆ 2258287      │
│ 2450982 ┆ 0x326c13991cf5b4ac6708be98ff15… ┆ 0x274271bb3c0b60c9fd99b05e51ae… ┆ 0x9400cb1e7c0fa7120ea0e4a7fcce… ┆ … ┆ 5751748  ┆ 18445048399967342 ┆ 35     ┆ 2258281      │
│ 2450974 ┆ 0xb0587362a27183e4a0e67a76fd81… ┆ 0x3e5776f98ccd447f478b150b7c7e… ┆ 0xa3ad1da9373ae97c21274629668d… ┆ … ┆ 4211778  ┆ 6062918999738481  ┆ 29     ┆ 2258274      │
│ 2450966 ┆ 0x24148e3b1ae003c5cb981653fd62… ┆ 0x7a8e508c671808cf25c835a67632… ┆ 0x9400cb1e7c0fa7120ea0e4a7fcce… ┆ … ┆ 4765098  ┆ 16225500999853000 ┆ 32     ┆ 2258267      │
│ …       ┆ …                               ┆ …                               ┆ …                               ┆ … ┆ …        ┆ …                 ┆ …      ┆ …            │
│ 2449791 ┆ 0x99a3d7228237038aff3b0f7cd55d… ┆ 0xfc224a4d9c0b84b35f6a55274124… ┆ 0x8cafae64383b537561650b2e3893… ┆ … ┆ 5308725  ┆ 18187345999853000 ┆ 31     ┆ 2257186      │
│ 2449787 ┆ 0x34d567e910b719e2a8fe0796b85a… ┆ 0x132fedf886b25e9018ee50f1ba58… ┆ 0x8cafae64383b537561650b2e3893… ┆ … ┆ 4510283  ┆ 17028919999853000 ┆ 29     ┆ 2257182      │
│ 2449776 ┆ 0x0606e5fdb340780a5a0e53ad7a6f… ┆ 0x387f87adfdc8e9f027c9b89d5c05… ┆ 0x9400cb1e7c0fa7120ea0e4a7fcce… ┆ … ┆ 7415437  ┆ 15136000097096026 ┆ 47     ┆ 2257171      │
│ 2449763 ┆ 0x6a5fec654d5c46905031a1e49455… ┆ 0x3fe0bc5893a0e7950426fbd018aa… ┆ 0x9400cb1e7c0fa7120ea0e4a7fcce… ┆ … ┆ 1347531  ┆ 12233676999853000 ┆ 10     ┆ 2257160      │
│ 2449762 ┆ 0x33ee162a56062162d337e71be7a5… ┆ 0x6a5fec654d5c46905031a1e49455… ┆ 0x9400cb1e7c0fa7120ea0e4a7fcce… ┆ … ┆ 4844588  ┆ 17795490999853000 ┆ 27     ┆ 2257159      │
└─────────┴─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┴───┴──────────┴───────────────────┴────────┴──────────────┘
```