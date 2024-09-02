from mev_boost_py.proposer_payload import ProposerPayloadFetcher
from mev_boost_py.proposer_payload import Network

# Fetch last 200 slots and save to data/holesky.
fetcher = ProposerPayloadFetcher(
    network=Network.HOLESKY,
    # directory="data/holesky",
    save_to_file=False  # Do not save to file; keep data in memory
)

# Run the fetcher to fetch data
data = fetcher.run()

# Convert fetched data to a Polars DataFrame
df = fetcher.to_polars_dataframe(data)

# Output the DataFrame to verify the content
print(df)
print(df.schema)