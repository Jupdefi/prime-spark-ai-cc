"""
VPN Manager - Monitor and manage WireGuard VPN connections
"""
import asyncio
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class PeerStatus:
    """VPN peer status information"""
    name: str
    ip: str
    public_key: str
    endpoint: Optional[str]
    latest_handshake: Optional[datetime]
    transfer_rx: int  # bytes received
    transfer_tx: int  # bytes transmitted
    is_connected: bool


class VPNManager:
    """Manage WireGuard VPN connections"""

    def __init__(self, interface: str = "wg0"):
        self.interface = interface
        self._peer_names = {
            "10.8.0.2": "control-pc",
            "10.8.0.3": "spark-agent",
            "10.8.0.11": "primecore1",
            "10.8.0.12": "primecore2",
            "10.8.0.13": "primecore3",
            "10.8.0.14": "primecore4",
        }

    async def is_vpn_active(self) -> bool:
        """Check if VPN interface is active"""
        try:
            result = await asyncio.create_subprocess_exec(
                "wg", "show", self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def get_peer_status(self) -> List[PeerStatus]:
        """Get status of all VPN peers"""
        try:
            result = await asyncio.create_subprocess_exec(
                "wg", "show", self.interface, "dump",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return []

            peers = []
            lines = stdout.decode().strip().split("\n")

            # Skip the first line (interface info)
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) >= 5:
                    public_key = parts[0]
                    endpoint = parts[2] if parts[2] != "(none)" else None
                    latest_handshake_timestamp = int(parts[4])
                    transfer_rx = int(parts[5])
                    transfer_tx = int(parts[6])

                    # Parse allowed IPs to get peer IP
                    allowed_ips = parts[3]
                    ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", allowed_ips)
                    peer_ip = ip_match.group(1) if ip_match else "unknown"

                    # Get peer name
                    peer_name = self._peer_names.get(peer_ip, f"unknown-{peer_ip}")

                    # Convert timestamp to datetime
                    latest_handshake = None
                    is_connected = False
                    if latest_handshake_timestamp > 0:
                        latest_handshake = datetime.fromtimestamp(latest_handshake_timestamp)
                        # Consider connected if handshake within last 3 minutes
                        time_since_handshake = (datetime.now() - latest_handshake).total_seconds()
                        is_connected = time_since_handshake < 180

                    peers.append(PeerStatus(
                        name=peer_name,
                        ip=peer_ip,
                        public_key=public_key,
                        endpoint=endpoint,
                        latest_handshake=latest_handshake,
                        transfer_rx=transfer_rx,
                        transfer_tx=transfer_tx,
                        is_connected=is_connected
                    ))

            return peers

        except Exception as e:
            print(f"Error getting peer status: {e}")
            return []

    async def start_vpn(self) -> bool:
        """Start WireGuard VPN interface"""
        try:
            result = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "start", f"wg-quick@{self.interface}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception as e:
            print(f"Error starting VPN: {e}")
            return False

    async def stop_vpn(self) -> bool:
        """Stop WireGuard VPN interface"""
        try:
            result = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "stop", f"wg-quick@{self.interface}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception as e:
            print(f"Error stopping VPN: {e}")
            return False

    async def restart_vpn(self) -> bool:
        """Restart WireGuard VPN interface"""
        try:
            result = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "restart", f"wg-quick@{self.interface}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception as e:
            print(f"Error restarting VPN: {e}")
            return False

    async def get_vpn_status(self) -> Dict:
        """Get comprehensive VPN status"""
        is_active = await self.is_vpn_active()
        peers = await self.get_peer_status() if is_active else []

        connected_peers = [p for p in peers if p.is_connected]
        total_rx = sum(p.transfer_rx for p in peers)
        total_tx = sum(p.transfer_tx for p in peers)

        return {
            "interface": self.interface,
            "is_active": is_active,
            "total_peers": len(peers),
            "connected_peers": len(connected_peers),
            "total_transfer_rx_bytes": total_rx,
            "total_transfer_tx_bytes": total_tx,
            "peers": [
                {
                    "name": p.name,
                    "ip": p.ip,
                    "endpoint": p.endpoint,
                    "is_connected": p.is_connected,
                    "latest_handshake": p.latest_handshake.isoformat() if p.latest_handshake else None,
                    "transfer_rx_mb": round(p.transfer_rx / 1024 / 1024, 2),
                    "transfer_tx_mb": round(p.transfer_tx / 1024 / 1024, 2),
                }
                for p in peers
            ]
        }

    async def ping_peer(self, peer_ip: str, count: int = 3) -> bool:
        """Ping a VPN peer to check connectivity"""
        try:
            result = await asyncio.create_subprocess_exec(
                "ping", "-c", str(count), "-W", "2", peer_ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        except Exception as e:
            print(f"Error pinging peer {peer_ip}: {e}")
            return False


async def main():
    """CLI for VPN management"""
    import sys

    manager = VPNManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            status = await manager.get_vpn_status()
            print("\n=== VPN Status ===")
            print(f"Interface: {status['interface']}")
            print(f"Active: {status['is_active']}")
            print(f"Peers: {status['connected_peers']}/{status['total_peers']} connected")
            print(f"Total Transfer: RX {status['total_transfer_rx_bytes']/1024/1024:.2f} MB, "
                  f"TX {status['total_transfer_tx_bytes']/1024/1024:.2f} MB")
            print("\nPeer Details:")
            for peer in status['peers']:
                status_icon = "✓" if peer['is_connected'] else "✗"
                print(f"  {status_icon} {peer['name']} ({peer['ip']})")
                if peer['latest_handshake']:
                    print(f"    Last handshake: {peer['latest_handshake']}")
                print(f"    Transfer: RX {peer['transfer_rx_mb']} MB, TX {peer['transfer_tx_mb']} MB")

        elif command == "start":
            success = await manager.start_vpn()
            print("VPN started successfully" if success else "Failed to start VPN")

        elif command == "stop":
            success = await manager.stop_vpn()
            print("VPN stopped successfully" if success else "Failed to stop VPN")

        elif command == "restart":
            success = await manager.restart_vpn()
            print("VPN restarted successfully" if success else "Failed to restart VPN")

        elif command == "ping":
            if len(sys.argv) > 2:
                peer_ip = sys.argv[2]
                success = await manager.ping_peer(peer_ip)
                print(f"Ping to {peer_ip}: {'SUCCESS' if success else 'FAILED'}")
            else:
                print("Usage: python manager.py ping <peer_ip>")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: status, start, stop, restart, ping <ip>")
    else:
        print("Usage: python manager.py <command>")
        print("Commands: status, start, stop, restart, ping <ip>")


if __name__ == "__main__":
    asyncio.run(main())
