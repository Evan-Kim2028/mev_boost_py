from mev_boost_py import ProposerPayloadFetcher

# Create a fetcher instance
fetcher = ProposerPayloadFetcher(start_slot=2447969, end_slot=2448969)

# Run the fetcher
fetcher.run()