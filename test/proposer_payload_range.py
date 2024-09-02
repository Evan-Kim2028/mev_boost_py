import os

from mev_boost_py.proposer_payload import ProposerPayloadFetcher
from mev_boost_py.proposer_payload import Network

# Fetch a 500 slot range on mainnet
fetcher = ProposerPayloadFetcher(
    network=Network.MAINNET,
    # 500 slot range on mainnet
    start_slot=8447969,
    end_slot=8448469,
    directory="data/mainnet"
)

# Run the fetcher to fetch and save data
fetcher.run()

# Output to verify if the data has been saved
output_file_path = os.path.join(fetcher.directory, fetcher.filename)
if os.path.exists(output_file_path):
    print(f"Output file created successfully at: {output_file_path}")
else:
    print("Failed to create output file.")