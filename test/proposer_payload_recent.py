from mev_boost_py.proposer_payload import ProposerPayloadFetcher
from mev_boost_py.proposer_payload import Network

fetcher = ProposerPayloadFetcher(
    network=Network.HOLESKY
    # No directory specified, so data will be kept in memory
)

# Run the fetcher to fetch data
data = fetcher.run()

# Convert fetched data to a Polars DataFrame
df = fetcher.to_polars_dataframe(data)

# Output the DataFrame to verify the content
print(df)
print(df.schema)