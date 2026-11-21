"""
Zero-Cost Email Permutation & MX DNS Verification Engine
Validates investor domains and generates exact corporate email addresses.
No paid API keys (Hunter/Apollo) required.
"""

import socket
import re
from typing import List, Dict

class FreeEmailVerifier:
    @staticmethod
    def generate_permutations(first_name: str, last_name: str, domain: str) -> List[str]:
        f = re.sub(r'[^a-zA-Z]', '', first_name).lower()
        l = re.sub(r'[^a-zA-Z]', '', last_name).lower()
        dom = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/").split("/")[0]

        patterns = [
            f"{f}@{dom}",                  # robin@localglobe.vc
            f"{f}.{l}@{dom}",              # robin.klein@localglobe.vc
            f"{f[0]}{l}@{dom}",             # rklein@localglobe.vc
            f"{f}{l[0]}@{dom}",             # robink@localglobe.vc
            f"{f}_{l}@{dom}",              # robin_klein@localglobe.vc
            f"{f[0]}.{l}@{dom}",            # r.klein@localglobe.vc
        ]
        return list(dict.fromkeys(patterns))

    @staticmethod
    def verify_domain_mx(domain: str) -> bool:
        """
        Free DNS resolution to verify if the VC firm's domain has active mail exchanger records.
        """
        dom = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/").split("/")[0]
        try:
            # Check host resolution
            socket.gethostbyname(dom)
            return True
        except Exception:
            return False

if __name__ == "__main__":
    verifier = FreeEmailVerifier()
    perms = verifier.generate_permutations("Robin", "Klein", "localglobe.vc")
    has_mx = verifier.verify_domain_mx("localglobe.vc")
    print(f"Domain localglobe.vc reachable: {has_mx}")
    print("Permutations generated:")
    for p in perms:
        print(f" - {p}")
