# mev-boost-py

Python wrapper for querying mev-boost data. This tool provides easy access to Ethereum proposer payload data from Flashbots relays, allowing users to query both "holesky" and "mainnet" networks. It supports fetching data for specific slot ranges or the most recent slots.

## Features
- Fetch proposer payloads from Flashbots relays
- Supports both "holesky" and "mainnet" networks
- Specify slot ranges or fetch the most recent data
- Save data to JSON files for flexible analysis

## Installation
To install `mev-boost-py`, use pip `pip install mev-boost-py`



# Usage Instructions:
## Run from CLI:
```python script_name.py --network mainnet --start_slot 2447969 --end_slot 2448969 --directory output_folder```
This command will fetch proposer payloads from the "mainnet" network for the specified slot range and save them in the "output_folder".

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

## Example Output:
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