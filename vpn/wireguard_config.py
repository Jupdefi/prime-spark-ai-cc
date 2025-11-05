"""
WireGuard VPN Configuration Generator
Generates configs for edge devices and cloud VMs
"""
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Peer:
    """WireGuard peer configuration"""
    name: str
    ip: str
    public_key: str
    private_key: str
    endpoint: str = ""  # For clients, this is the server endpoint
    persistent_keepalive: int = 25


class WireGuardConfig:
    """Generate WireGuard configurations for Prime Spark AI"""

    def __init__(self, subnet: str = "10.8.0.0/24", port: int = 51820):
        self.subnet = subnet
        self.port = port
        self.peers: Dict[str, Peer] = {}

    def generate_keypair(self) -> Tuple[str, str]:
        """Generate WireGuard public/private key pair"""
        try:
            # Generate private key
            private_key = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            # Generate public key from private key
            public_key = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            return private_key, public_key
        except subprocess.CalledProcessError:
            # Fallback: generate keys using Python if wg command not available
            print("Warning: 'wg' command not found. Install WireGuard tools.")
            return "PRIVATE_KEY_PLACEHOLDER", "PUBLIC_KEY_PLACEHOLDER"

    def add_peer(self, name: str, ip: str, endpoint: str = "") -> Peer:
        """Add a peer to the VPN"""
        private_key, public_key = self.generate_keypair()
        peer = Peer(
            name=name,
            ip=ip,
            public_key=public_key,
            private_key=private_key,
            endpoint=endpoint
        )
        self.peers[name] = peer
        return peer

    def generate_server_config(self, server_name: str, listen_port: int = 51820) -> str:
        """Generate server (hub) configuration"""
        server = self.peers.get(server_name)
        if not server:
            raise ValueError(f"Server {server_name} not found in peers")

        config = f"""[Interface]
# Prime Spark AI VPN - {server_name} (Server)
Address = {server.ip}/24
ListenPort = {listen_port}
PrivateKey = {server.private_key}

# Enable IP forwarding
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

"""
        # Add all other peers
        for peer_name, peer in self.peers.items():
            if peer_name != server_name:
                config += f"""
[Peer]
# {peer_name}
PublicKey = {peer.public_key}
AllowedIPs = {peer.ip}/32
PersistentKeepalive = {peer.persistent_keepalive}
"""

        return config

    def generate_client_config(self, client_name: str, server_peer: Peer, dns: str = "1.1.1.1") -> str:
        """Generate client configuration"""
        client = self.peers.get(client_name)
        if not client:
            raise ValueError(f"Client {client_name} not found in peers")

        config = f"""[Interface]
# Prime Spark AI VPN - {client_name} (Client)
Address = {client.ip}/24
PrivateKey = {client.private_key}
DNS = {dns}

[Peer]
# Server: {server_peer.name}
PublicKey = {server_peer.public_key}
Endpoint = {server_peer.endpoint}
AllowedIPs = 10.8.0.0/24
PersistentKeepalive = {client.persistent_keepalive}
"""
        return config

    def save_configs(self, output_dir: Path):
        """Save all configurations to files"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Assuming first peer added is the server (Control PC)
        server_name = list(self.peers.keys())[0]
        server_peer = self.peers[server_name]

        # Save server config
        server_config_path = output_dir / f"{server_name}.conf"
        with open(server_config_path, "w") as f:
            f.write(self.generate_server_config(server_name, self.port))
        print(f"Generated server config: {server_config_path}")

        # Save client configs
        for peer_name in list(self.peers.keys())[1:]:
            client_config_path = output_dir / f"{peer_name}.conf"
            with open(client_config_path, "w") as f:
                f.write(self.generate_client_config(peer_name, server_peer))
            print(f"Generated client config: {client_config_path}")


def generate_prime_spark_vpn():
    """Generate VPN configs for Prime Spark AI infrastructure"""
    vpn = WireGuardConfig(subnet="10.8.0.0/24", port=51820)

    # Edge devices (Control PC is the VPN server/hub)
    control_pc = vpn.add_peer(
        "control-pc",
        "10.8.0.2",
        endpoint=""  # Server doesn't need endpoint
    )

    spark_agent = vpn.add_peer(
        "spark-agent",
        "10.8.0.3",
        endpoint="192.168.1.100:51820"  # Control PC's LAN IP
    )

    # Cloud VMs - they need the public IP of the edge network
    # NOTE: Update this with your actual public IP or dynamic DNS
    edge_public_endpoint = "YOUR_PUBLIC_IP:51820"

    primecore1 = vpn.add_peer(
        "primecore1",
        "10.8.0.11",
        endpoint=edge_public_endpoint
    )

    primecore2 = vpn.add_peer(
        "primecore2",
        "10.8.0.12",
        endpoint=edge_public_endpoint
    )

    primecore3 = vpn.add_peer(
        "primecore3",
        "10.8.0.13",
        endpoint=edge_public_endpoint
    )

    primecore4 = vpn.add_peer(
        "primecore4",
        "10.8.0.14",
        endpoint=edge_public_endpoint
    )

    # Save all configs
    output_dir = Path(__file__).parent / "configs"
    vpn.save_configs(output_dir)

    print("\n" + "="*60)
    print("VPN Configuration Generated Successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Update edge_public_endpoint in this script with your public IP")
    print("2. Copy control-pc.conf to /etc/wireguard/wg0.conf on Control PC")
    print("3. Copy spark-agent.conf to /etc/wireguard/wg0.conf on Spark Agent")
    print("4. Copy primecore*.conf to /etc/wireguard/wg0.conf on respective VMs")
    print("5. Enable and start WireGuard: sudo systemctl enable --now wg-quick@wg0")
    print("6. Verify connectivity: ping 10.8.0.X")
    print("\nIMPORTANT: Ensure UDP port 51820 is forwarded on your router to Control PC")


if __name__ == "__main__":
    generate_prime_spark_vpn()
