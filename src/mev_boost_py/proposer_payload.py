import requests
import json
import concurrent.futures
from threading import Lock, Semaphore
import time
import argparse
from dataclasses import dataclass, field

@dataclass
class ProposerPayloadFetcher:
    start_slot: int = None
    end_slot: int = None
    rate_limit: int = 100
    filename: str = "block_payloads.json"
    lock: Lock = field(default_factory=Lock)
    rate_limiter: Semaphore = field(init=False)

    def __post_init__(self):
        self.rate_limiter = Semaphore(self.rate_limit)
        if self.start_slot and self.end_slot:
            assert self.end_slot > self.start_slot, "End slot must be greater than start slot."

    def fetch_proposer_payloads(self, slot: int) -> dict:
        """
        Fetch proposer payloads for a specific slot.
        """
        with self.rate_limiter:
            url = f"https://boost-relay-holesky.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered?slot={slot}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    payloads = response.json()
                    return payloads if payloads else None
                else:
                    print(f"Failed to fetch proposer payloads for slot {slot}. Status code: {response.status_code}")
                    return None
            except Exception as e:
                print(f"An error occurred while fetching slot {slot}: {e}")
                return None

    def save_payloads_to_file(self, payloads: list):
        """
        Save proposer payloads to a .json file in a list format.
        """
        if self.lock:
            self.lock.acquire()

        try:
            with open(self.filename, "w") as f:
                json.dump(payloads, f, indent=2)
            print(f"Payloads saved to {self.filename}")
        except Exception as e:
            print(f"An error occurred while saving to file: {e}")
        finally:
            if self.lock:
                self.lock.release()

    def fetch_range(self):
        """
        Fetch proposer payloads for a range of slots.
        """
        payloads_list = []
        null_entry_template = {
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

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.rate_limit) as executor:
            future_to_slot = {
                executor.submit(self.fetch_proposer_payloads, slot): slot
                for slot in range(self.start_slot, self.end_slot)
            }

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

                time.sleep(0.05)  # Maintain rate limit

        self.save_payloads_to_file(payloads_list)

    def fetch_latest(self):
        """
        Fetch the latest 200 proposer payloads.
        """
        latest_url = "https://boost-relay-holesky.flashbots.net/relay/v1/data/bidtraces/proposer_payload_delivered"
        try:
            response = requests.get(latest_url)
            if response.status_code == 200:
                payloads = response.json()
                self.save_payloads_to_file(payloads)
            else:
                print(f"Failed to fetch latest slots. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while fetching latest slots: {e}")

    def run(self):
        """
        Run the fetch process based on provided slot range or fetch the latest.
        """
        if self.start_slot is not None and self.end_slot is not None:
            self.fetch_range()
        else:
            self.fetch_latest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch proposer payloads for a slot range.")
    parser.add_argument('--start_slot', type=int, help='Starting slot number')
    parser.add_argument('--end_slot', type=int, help='Ending slot number')

    args = parser.parse_args()

    fetcher = ProposerPayloadFetcher(start_slot=args.start_slot, end_slot=args.end_slot)
    fetcher.run()
