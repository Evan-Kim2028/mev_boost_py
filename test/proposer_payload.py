from mev_boost_py.proposer_payload import ProposerPayloadFetcher

# Create a fetcher instance
fetcher = ProposerPayloadFetcher(
    # Use the start_slot and end_slot arguments to specify a range of slots to fetch. If none, it will default to the most recent 200 slots.
    # start_slot=2447969, 
    # end_slot=2448969
    )

# Run the fetcher
fetcher.run()