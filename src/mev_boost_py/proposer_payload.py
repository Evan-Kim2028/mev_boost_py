import requests
import json
import concurrent.futures
from threading import Lock, BoundedSemaphore
import time
import argparse
from dataclasses import dataclass, field
import os
from enum import Enum

class Network(Enum):
    """
    Enum class to define supported networks for fetching proposer payloads.
    """
    HOLESKY = "holesky"
    MAINNET = "mainnet"

    @staticmethod
    def get_url(network):
        """
        Get the base URL for the specified network.

        Args:
            network (Network): The network enum value (HOLESKY or MAINNET).

        Returns:
            str: The base URL for the network.

        Raises:
            ValueError: If the network is not supported.
        """
        if network == Network.HOLESKY:
            return "https://boost-relay-holesky.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered"
        elif network == Network.MAINNET:
            return "https://boost-relay.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered"
        else:
            raise ValueError("Unsupported network")

@dataclass
class ProposerPayloadFetcher:
    """
    A class to fetch proposer payloads for Ethereum slots from the Flashbots relay.

    Attributes:
        start_slot (int): The starting slot number for fetching data. Defaults to None.
        end_slot (int): The ending slot number for fetching data. Defaults to None.
        rate_limit (int): The rate limit for concurrent requests. Defaults to 20.
        filename (str): The name of the file to save the fetched payloads. Defaults to 'block_payloads.json'.
        directory (str): The directory to save the output file. Defaults to 'data'.
        network (Network): The network to fetch data from. Defaults to Network.MAINNET.
        lock (Lock): A threading lock to synchronize file access.
        rate_limiter (BoundedSemaphore): A semaphore to control the rate of concurrent requests.
    """
    start_slot: int = None
    end_slot: int = None
    rate_limit: int = 15  # Limit to 20 requests per second
    filename: str = "block_payloads.json"
    directory: str = "data"  # Default directory to save the file
    network: Network = Network.MAINNET  # Default to mainnet
    lock: Lock = field(default_factory=Lock)
    rate_limiter: BoundedSemaphore = field(init=False)

    def __post_init__(self):
        """
        Post-initialization to set up the rate limiter and ensure the output directory exists.
        """
        # Initialize the semaphore for rate limiting (bounded to 20 requests at a time)
        self.rate_limiter = BoundedSemaphore(self.rate_limit)

        # Check if the slot range is valid
        if self.start_slot and self.end_slot:
            assert self.end_slot > self.start_slot, "End slot must be greater than start slot."

        # Ensure the output directory exists
        self._ensure_directory()

    def _ensure_directory(self):
        """
        Ensure the specified directory exists; create it if it doesn't.
        """
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            print(f"Created directory {self.directory}")
        else:
            print(f"Using existing directory {self.directory}")

    def fetch_with_backoff(self, url, max_retries=5):
        """
        Fetch data with an exponential backoff strategy for handling rate limits.

        Args:
            url (str): The URL to fetch data from.
            max_retries (int): The maximum number of retries if rate limited.

        Returns:
            dict: The JSON response data or None if the request failed.
        """
        delay = 30  # Start with a 30 second delay
        for attempt in range(max_retries):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"Failed to fetch data. Status code: {response.status_code}")
                    return None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
        print("Max retries reached. Failed to fetch data.")
        return None

    def fetch_proposer_payloads(self, slot: int) -> dict:
        """
        Fetch proposer payloads for a specific slot.

        Args:
            slot (int): The slot number to fetch data for.

        Returns:
            dict: A dictionary containing the proposer payloads or None if no data/error.
        """
        url = f"{Network.get_url(self.network)}?slot={slot}"
        with self.rate_limiter:  # Ensure that only `rate_limit` requests run concurrently
            return self.fetch_with_backoff(url)

    def save_payloads_to_file(self, payloads: list):
        """
        Save proposer payloads to a JSON file in a list format.

        Args:
            payloads (list): The list of payload entries to save.
        """
        if self.lock:
            self.lock.acquire()

        filepath = os.path.join(self.directory, self.filename)

        try:
            with open(filepath, "w") as f:
                json.dump(payloads, f, indent=2)
            print(f"Payloads saved to {filepath}")
        except Exception as e:
            print(f"An error occurred while saving to file: {e}")
        finally:
            if self.lock:
                self.lock.release()

    def fetch_range(self):
        """
        Fetch proposer payloads for a range of slots and save them to a file.
        """
        payloads_list = []  # List to store all fetched payloads
        null_entry_template = {  # Template for slots with no data
            "slot": None,
            "parent_hash": None,
            "block_hash": None,
            "builder_pubkey": None,
            "proposer_pubkey": None,
            "proposer_fee_recipient": None,
            "gas_limit": None,
            "gas_used": None,
            "value": None,
            "num_tx": None,
            "block_number": None,
        }

        # Control the number of requests per second
        slots = range(self.start_slot, self.end_slot)
        slots_iter = iter(slots)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.rate_limit) as executor:
            future_to_slot = {}

            while True:
                try:
                    for _ in range(self.rate_limit):  # Limit to 20 requests per second
                        slot = next(slots_iter)
                        future = executor.submit(self.fetch_proposer_payloads, slot)
                        future_to_slot[future] = slot

                    # Wait for all futures to complete before starting the next batch
                    for future in concurrent.futures.as_completed(future_to_slot):
                        slot = future_to_slot[future]
                        slot_data = future.result()

                        if slot_data is not None:
                            print(f"Fetched payloads for slot {slot}")
                            payloads_list.extend(slot_data)
                        else:
                            print(f"No data for slot {slot}, adding null entry.")
                            null_entry = null_entry_template.copy()
                            null_entry["slot"] = str(slot)
                            payloads_list.append(null_entry)

                    # Clear the future-to-slot mapping for the next batch
                    future_to_slot.clear()

                    # Sleep for 1 second to maintain the rate limit
                    time.sleep(1)

                except StopIteration:
                    break

        # Save all fetched data to the specified file
        self.save_payloads_to_file(payloads_list)

    def fetch_latest(self):
        """
        Fetch the latest 200 proposer payloads and save them to a file.
        """
        latest_url = Network.get_url(self.network)
        payloads = self.fetch_with_backoff(latest_url)
        if payloads:
            self.save_payloads_to_file(payloads)

    def run(self):
        """
        Run the fetch process based on provided slot range or fetch the latest slots.
        """
        if self.start_slot is not None and self.end_slot is not None:
            self.fetch_range()
        else:
            self.fetch_latest()

# Main entry point when running the script directly
if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Fetch proposer payloads for a slot range.")
    parser.add_argument('--start_slot', type=int, help='Starting slot number')
    parser.add_argument('--end_slot', type=int, help='Ending slot number')
    parser.add_argument('--directory', type=str, default="data", help='Directory to save the .json file')
    parser.add_argument('--network', type=str, choices=[n.value for n in Network], default=Network.MAINNET.value,
                        help='Network to fetch data from (holesky or mainnet)')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Create an instance of ProposerPayloadFetcher with the provided arguments
    fetcher = ProposerPayloadFetcher(
        start_slot=args.start_slot,
        end_slot=args.end_slot,
        directory=args.directory,
        network=Network(args.network)
    )

    # Run the fetch operation
    fetcher.run()
