import os

from mev_boost_py.proposer_payload import ProposerPayloadFetcher
from mev_boost_py.proposer_payload import Network

# Create an instance of ProposerPayloadFetcher
fetcher = ProposerPayloadFetcher(
    network=Network.MAINNET,
)

# Run the fetcher to fetch and save data
fetcher.run()

# Output to verify if the data has been saved
output_file_path = os.path.join(fetcher.directory, fetcher.filename)
if os.path.exists(output_file_path):
    print(f"Output file created successfully at: {output_file_path}")
else:
    print("Failed to create output file.")