import requests
import json
import concurrent.futures
from threading import Lock, BoundedSemaphore
import time
import argparse
from dataclasses import dataclass, field
import os
from enum import Enum
import polars as pl
from typing import List, Dict, Optional, Any

class Network(Enum):
    """
    Enum class to define supported networks for fetching proposer payloads.
    """
    HOLESKY = "holesky"
    MAINNET = "mainnet"

class Relay(Enum):
    """
    Enum class to define supported relays for fetching proposer payloads.
    """
    ALL = "all"
    AESTUS = "aestus"
    BOOST_RELAY = "boost-relay"
    TITANRELAY = "titanrelay"
    AGNOSTIC = "agnostic"
    BLOXROUTE_MAX_PROFIT = "bloxroute-max-profit"
    BLOXROUTE_REGULATED = "bloxroute-regulated"
    ULTRASOUND = "ultrasound"

    @staticmethod
    def get_urls(relay: 'Relay', network: 'Network') -> List[str]:
        """
        Get the list of base URLs for the specified relay and network.

        Args:
            relay (Relay): The relay enum value.
            network (Network): The network enum value.

        Returns:
            List[str]: The list of base URLs for the specified relay and network.

        Raises:
            ValueError: If the relay or network is not supported.
        """
        urls = {
            Network.HOLESKY: {
                Relay.AESTUS: ["https://holesky.aestus.live/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.BOOST_RELAY: ["https://boost-relay-holesky.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.TITANRELAY: ["https://holesky.titanrelay.xyz/relay/v1/data/bidtraces/proposer_payload_delivered"],
            },
            Network.MAINNET: {
                Relay.AESTUS: ["https://aestus.live/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.BOOST_RELAY: ["https://boost-relay.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.TITANRELAY: ["https://titanrelay.xyz/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.AGNOSTIC: ["https://agnostic-relay.net/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.BLOXROUTE_MAX_PROFIT: ["https://bloxroute.max-profit.blxrbdn.com/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.BLOXROUTE_REGULATED: ["https://bloxroute.regulated.blxrbdn.com/relay/v1/data/bidtraces/proposer_payload_delivered"],
                Relay.ULTRASOUND: ["https://relay-analytics.ultrasound.money/relay/v1/data/bidtraces/proposer_payload_delivered"],
            }
        }

        if relay == Relay.ALL:
            all_urls = []
            for r in urls[network].values():
                all_urls.extend(r)
            return all_urls
        else:
            return urls[network].get(relay, [])

@dataclass
class ProposerPayloadFetcher:
    """
    A class to fetch proposer payloads for Ethereum slots from the Flashbots relay.

    Attributes:
        start_slot (Optional[int]): The starting slot number for fetching data.
        end_slot (Optional[int]): The ending slot number for fetching data.
        rate_limit (int): The rate limit for concurrent requests.
        filename (str): The name of the file to save the fetched payloads.
        directory (Optional[str]): The directory to save the output file.
        network (Network): The network to fetch data from.
        relay (Relay): The relay to fetch data from.
        lock (Lock): A threading lock to synchronize file access.
        rate_limiter (BoundedSemaphore): A semaphore to control the rate of concurrent requests.
    """
    start_slot: Optional[int] = None
    end_slot: Optional[int] = None
    rate_limit: int = 15  # Limit to 15 requests per second
    filename: str = "block_payloads.json"
    directory: Optional[str] = None
    network: Network = Network.MAINNET
    relay: Relay = Relay.ALL
    lock: Lock = field(default_factory=Lock)
    rate_limiter: BoundedSemaphore = field(init=False)

    def __post_init__(self) -> None:
        """
        Post-initialization to set up the rate limiter and ensure the output directory exists if needed.
        """
        self.rate_limiter = BoundedSemaphore(self.rate_limit)

        if self.start_slot and self.end_slot:
            assert self.end_slot > self.start_slot, "End slot must be greater than start slot."

        if self.directory:
            self._ensure_directory()

    def _ensure_directory(self) -> None:
        """
        Ensure the specified directory exists; create it if it doesn't.
        """
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            print(f"Created directory {self.directory}")
        else:
            print(f"Using existing directory {self.directory}")

    def fetch_with_backoff(self, url: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
        """
        Fetch data with an exponential backoff strategy for handling rate limits.

        Args:
            url (str): The URL to fetch data from.
            max_retries (int): The maximum number of retries if rate limited.

        Returns:
            Optional[Dict[str, Any]]: The JSON response data or None if the request failed.
        """
        delay = 30  # Start with a 30 second delay
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)  # Adding a timeout to handle non-responsive endpoints
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print(f"Rate limit exceeded for {url}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                    break  # Break if status code is not 429 (e.g., 404, 500)
            except requests.exceptions.RequestException as e:
                print(f"Network error occurred while fetching data from {url}: {e}")
                break  # Exit retry loop if there's a network error
        print(f"Max retries reached. Failed to fetch data from {url}.")
        return None

    def fetch_proposer_payloads(self, slot: int, relay_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch proposer payloads for a specific slot from a specific relay.

        Args:
            slot (int): The slot number to fetch data for.
            relay_url (str): The relay URL to fetch data from.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the proposer payloads or None if no data/error.
        """
        url = f"{relay_url}?slot={slot}"
        with self.rate_limiter:
            payload = self.fetch_with_backoff(url)
            if payload:
                for entry in payload:
                    entry['relay'] = relay_url
            return payload

    def cast_payload_types(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cast the types of payload fields to match the specified schema.

        Args:
            payload (Dict[str, Any]): The payload entry to cast.

        Returns:
            Dict[str, Any]: The payload entry with casted types.
        """
        try:
            payload['slot'] = int(payload['slot']) if payload['slot'] is not None else None
            payload['parent_hash'] = str(payload['parent_hash']) if payload['parent_hash'] is not None else None
            payload['block_hash'] = str(payload['block_hash']) if payload['block_hash'] is not None else None
            payload['builder_pubkey'] = str(payload['builder_pubkey']) if payload['builder_pubkey'] is not None else None
            payload['proposer_pubkey'] = str(payload['proposer_pubkey']) if payload['proposer_pubkey'] is not None else None
            payload['proposer_fee_recipient'] = str(payload['proposer_fee_recipient']) if payload['proposer_fee_recipient'] is not None else None
            payload['gas_limit'] = int(payload['gas_limit']) if payload['gas_limit'] is not None else None
            payload['gas_used'] = int(payload['gas_used']) if payload['gas_used'] is not None else None
            payload['value'] = float(payload['value']) if payload['value'] is not None else None
            payload['block_number'] = int(payload['block_number']) if payload['block_number'] is not None else None
            payload['num_tx'] = int(payload['num_tx']) if payload['num_tx'] is not None else None
            payload['relay'] = str(payload['relay']) if payload['relay'] is not None else None
        except ValueError as e:
            print(f"Error casting payload types: {e}")
        return payload

    def save_payloads_to_file(self, payloads: List[Dict[str, Any]]) -> None:
        """
        Save proposer payloads to a JSON file in a list format.

        Args:
            payloads (List[Dict[str, Any]]): The list of payload entries to save.
        """
        if self.lock:
            self.lock.acquire()

        filepath = os.path.join(self.directory, self.filename)

        # Cast payload types before saving
        casted_payloads = [self.cast_payload_types(payload) for payload in payloads]

        try:
            with open(filepath, "w") as f:
                json.dump(casted_payloads, f, indent=2)
            print(f"Payloads saved to {filepath}")
        except Exception as e:
            print(f"An error occurred while saving to file: {e}")
        finally:
            if self.lock:
                self.lock.release()

    def fetch_range(self) -> pl.DataFrame:
        """
        Fetch proposer payloads for a range of slots.

        Returns:
            pl.DataFrame: The Polars DataFrame containing the fetched payload data.
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
            "relay": None  # Add relay field
        }

        slots = range(self.start_slot, self.end_slot)
        slots_iter = iter(slots)
        relay_urls = Relay.get_urls(self.relay, self.network)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.rate_limit) as executor:
            future_to_slot = {}

            while True:
                try:
                    for _ in range(self.rate_limit):
                        slot = next(slots_iter)
                        for relay_url in relay_urls:
                            future = executor.submit(self.fetch_proposer_payloads, slot, relay_url)
                            future_to_slot[future] = (slot, relay_url)

                    for future in concurrent.futures.as_completed(future_to_slot):
                        slot, relay_url = future_to_slot[future]
                        slot_data = future.result()

                        if slot_data:
                            print(f"Fetched payloads for slot {slot} from {relay_url}")
                            payloads_list.extend(slot_data)
                        else:
                            print(f"No data for slot {slot} from {relay_url}, adding null entry.")
                            null_entry = null_entry_template.copy()
                            null_entry["slot"] = str(slot)
                            null_entry["relay"] = relay_url
                            payloads_list.append(null_entry)

                    future_to_slot.clear()
                    time.sleep(1)

                except StopIteration:
                    break

        if self.directory:
            self.save_payloads_to_file(payloads_list)

        return self.to_polars_dataframe(payloads_list)

    def fetch_latest(self) -> pl.DataFrame:
        """
        Fetch the latest 200 proposer payloads from each relay.

        Returns:
            pl.DataFrame: The Polars DataFrame containing the fetched payload data.
        """
        payloads_list = []
        relay_urls = Relay.get_urls(self.relay, self.network)

        for relay_url in relay_urls:
            payloads = self.fetch_with_backoff(relay_url)
            if payloads:
                for entry in payloads:
                    entry['relay'] = relay_url
                payloads_list.extend(payloads)
            else:
                print(f"Skipping relay {relay_url} due to fetch failure.")

        if self.directory:
            self.save_payloads_to_file(payloads_list)

        return self.to_polars_dataframe(payloads_list)

    def run(self) -> Optional[pl.DataFrame]:
        """
        Run the fetch process based on provided slot range or fetch the latest slots.

        Returns:
            Optional[pl.DataFrame]: The Polars DataFrame containing the fetched payload data, or None.
        """
        if self.start_slot is not None and self.end_slot is not None:
            return self.fetch_range()
        else:
            return self.fetch_latest()

    def to_polars_dataframe(self, data: List[Dict[str, Any]]) -> pl.DataFrame:
        """
        Convert fetched data to a Polars DataFrame.

        Args:
            data (List[Dict[str, Any]]): The list of payload entries.

        Returns:
            pl.DataFrame: The Polars DataFrame containing the payload data.
        """
        if data:
            casted_data = [self.cast_payload_types(row) for row in data]
            df = pl.DataFrame(casted_data)
            return df
        else:
            print("No data available to convert.")
            return pl.DataFrame([])

# Main entry point when running the script directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch proposer payloads for a slot range.")
    parser.add_argument('--start_slot', type=int, help='Starting slot number')
    parser.add_argument('--end_slot', type=int, help='Ending slot number')
    parser.add_argument('--directory', type=str, default=None, help='Directory to save the .json file')
    parser.add_argument('--network', type=str, choices=[n.value for n in Network], default=Network.MAINNET.value,
                        help='Network to fetch data from (holesky or mainnet)')
    parser.add_argument('--relay', type=str, choices=[r.value for r in Relay], default=Relay.ALL.value,
                        help='Relay to fetch data from (all, aestus, boost-relay, titanrelay, etc.)')

    args = parser.parse_args()

    fetcher = ProposerPayloadFetcher(
        start_slot=args.start_slot,
        end_slot=args.end_slot,
        directory=args.directory,
        network=Network(args.network),
        relay=Relay(args.relay)
    )

    fetcher.run()
