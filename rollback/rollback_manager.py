"""
Core rollback management functionality.
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class RollbackPoint:
    """
    Represents a point-in-time snapshot for rollback.
    """
    id: str
    timestamp: str
    description: str
    services: List[str]
    docker_images: Dict[str, str]
    config_hashes: Dict[str, str]
    volumes: List[str]
    metadata: Dict[str, Any]
    created_by: str = "system"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RollbackPoint':
        """Create from dictionary"""
        return cls(**data)


class RollbackManager:
    """
    Manages rollback points and orchestrates rollback operations.

    Features:
    - Create deployment snapshots
    - Store Docker image tags and configs
    - Rollback to previous state
    - List available rollback points
    - Cleanup old rollback points
    """

    def __init__(
        self,
        backup_dir: str = "rollback/backups",
        max_rollback_points: int = 10,
        project_root: str = "."
    ):
        """
        Initialize rollback manager.

        Args:
            backup_dir: Directory to store rollback data
            max_rollback_points: Maximum number of rollback points to keep
            project_root: Root directory of the project
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_rollback_points = max_rollback_points
        self.project_root = Path(project_root)
        self.rollback_index = self.backup_dir / "rollback_index.json"

        # Initialize logging if available
        try:
            from logging import ChangeLogger, ChangeType
            self.logger = ChangeLogger(agent_id="rollback-manager")
            self.logging_enabled = True
        except ImportError:
            self.logger = None
            self.logging_enabled = False

    def create_rollback_point(
        self,
        description: str,
        services: Optional[List[str]] = None,
        include_volumes: bool = False
    ) -> RollbackPoint:
        """
        Create a new rollback point.

        Args:
            description: Description of this rollback point
            services: List of services to snapshot (None = all)
            include_volumes: Whether to backup volume data

        Returns:
            Created RollbackPoint
        """
        rollback_id = self._generate_rollback_id()
        timestamp = datetime.utcnow().isoformat()

        print(f"Creating rollback point: {rollback_id}")
        print(f"Description: {description}")

        # Get current Docker state
        docker_images = self._get_current_docker_images(services)
        print(f"Captured {len(docker_images)} Docker image states")

        # Backup configuration files
        config_hashes = self._backup_configs(rollback_id)
        print(f"Backed up {len(config_hashes)} configuration files")

        # Backup volumes if requested
        volumes = []
        if include_volumes:
            volumes = self._backup_volumes(rollback_id, services)
            print(f"Backed up {len(volumes)} volumes")

        # Get service list
        if services is None:
            services = self._get_all_services()

        # Create rollback point
        rollback_point = RollbackPoint(
            id=rollback_id,
            timestamp=timestamp,
            description=description,
            services=services,
            docker_images=docker_images,
            config_hashes=config_hashes,
            volumes=volumes,
            metadata={
                "include_volumes": include_volumes,
                "git_commit": self._get_git_commit(),
                "hostname": os.uname().nodename
            }
        )

        # Save rollback point
        self._save_rollback_point(rollback_point)

        # Cleanup old rollback points
        self._cleanup_old_rollback_points()

        # Log if logging is enabled
        if self.logging_enabled and self.logger:
            self.logger.log_agent_decision(
                decision=f"Created rollback point: {rollback_id}",
                reasoning=description,
                context=rollback_point.to_dict()
            )

        print(f"✓ Rollback point created: {rollback_id}")
        return rollback_point

    def rollback(self, rollback_id: str, dry_run: bool = False) -> bool:
        """
        Rollback to a specific rollback point.

        Args:
            rollback_id: ID of rollback point to restore
            dry_run: If True, only show what would be done

        Returns:
            True if successful, False otherwise
        """
        # Load rollback point
        rollback_point = self._load_rollback_point(rollback_id)
        if not rollback_point:
            print(f"✗ Rollback point not found: {rollback_id}")
            return False

        print(f"\n{'DRY RUN: ' if dry_run else ''}Rolling back to: {rollback_id}")
        print(f"Description: {rollback_point.description}")
        print(f"Created: {rollback_point.timestamp}")
        print(f"Services: {', '.join(rollback_point.services)}")

        if dry_run:
            print("\nDry run - no changes will be made")
            self._show_rollback_plan(rollback_point)
            return True

        # Confirm rollback (unless automated)
        if not self._confirm_rollback(rollback_point):
            print("Rollback cancelled")
            return False

        try:
            # Log rollback start
            if self.logging_enabled and self.logger:
                self.logger.log_agent_decision(
                    decision=f"Starting rollback to: {rollback_id}",
                    reasoning=f"Restoring to state: {rollback_point.description}",
                    context=rollback_point.to_dict()
                )

            # Stop services
            print("\nStopping services...")
            self._stop_services(rollback_point.services)

            # Restore configurations
            print("Restoring configurations...")
            self._restore_configs(rollback_point)

            # Restore Docker images
            print("Restoring Docker images...")
            self._restore_docker_images(rollback_point)

            # Restore volumes if backed up
            if rollback_point.volumes:
                print("Restoring volumes...")
                self._restore_volumes(rollback_point)

            # Start services
            print("Starting services...")
            self._start_services(rollback_point.services)

            # Verify rollback
            print("Verifying rollback...")
            if self._verify_rollback(rollback_point):
                print(f"\n✓ Rollback to {rollback_id} completed successfully")

                # Log rollback success
                if self.logging_enabled and self.logger:
                    self.logger.log_agent_decision(
                        decision=f"Rollback completed: {rollback_id}",
                        reasoning="Successfully restored to previous state",
                        context={"rollback_id": rollback_id, "success": True}
                    )

                return True
            else:
                print(f"\n⚠ Rollback completed with warnings")
                return True

        except Exception as e:
            print(f"\n✗ Rollback failed: {e}")

            # Log rollback failure
            if self.logging_enabled and self.logger:
                from logging.change_logger import LogLevel
                self.logger.log(
                    change_type=self.logger.ChangeType.DEPLOYMENT,
                    description=f"Rollback failed: {rollback_id}",
                    metadata={"error": str(e), "rollback_id": rollback_id},
                    level=LogLevel.ERROR
                )

            return False

    def list_rollback_points(self) -> List[RollbackPoint]:
        """
        List all available rollback points.

        Returns:
            List of RollbackPoint objects
        """
        index = self._load_index()
        rollback_points = []

        for entry in index.get("rollback_points", []):
            rp = RollbackPoint.from_dict(entry)
            rollback_points.append(rp)

        return sorted(rollback_points, key=lambda x: x.timestamp, reverse=True)

    def delete_rollback_point(self, rollback_id: str) -> bool:
        """
        Delete a specific rollback point.

        Args:
            rollback_id: ID of rollback point to delete

        Returns:
            True if successful
        """
        # Load index
        index = self._load_index()

        # Find and remove rollback point
        rollback_points = index.get("rollback_points", [])
        found = False

        for i, entry in enumerate(rollback_points):
            if entry["id"] == rollback_id:
                rollback_points.pop(i)
                found = True
                break

        if not found:
            return False

        # Save updated index
        index["rollback_points"] = rollback_points
        self._save_index(index)

        # Delete rollback data directory
        rollback_dir = self.backup_dir / rollback_id
        if rollback_dir.exists():
            shutil.rmtree(rollback_dir)

        print(f"✓ Deleted rollback point: {rollback_id}")
        return True

    def _generate_rollback_id(self) -> str:
        """Generate unique rollback ID"""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{timestamp}-{os.urandom(8).hex()}"
        return f"rb-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def _get_current_docker_images(self, services: Optional[List[str]]) -> Dict[str, str]:
        """Get current Docker image tags for services"""
        images = {}

        try:
            # Get running containers
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                # Parse container info
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            service = container.get("Service")
                            image = container.get("Image")

                            if service and image:
                                if services is None or service in services:
                                    images[service] = image
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            print(f"Warning: Could not get Docker images: {e}")

        return images

    def _backup_configs(self, rollback_id: str) -> Dict[str, str]:
        """Backup configuration files"""
        config_dir = self.backup_dir / rollback_id / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_files = [
            "docker-compose.yml",
            "docker-compose.enterprise.yml",
            ".env",
            "deployment/prometheus.yml"
        ]

        hashes = {}

        for config_file in config_files:
            src_path = self.project_root / config_file
            if src_path.exists():
                # Calculate hash
                file_hash = self._hash_file(src_path)
                hashes[config_file] = file_hash

                # Copy file
                dst_path = config_dir / config_file.replace("/", "_")
                shutil.copy2(src_path, dst_path)

        return hashes

    def _backup_volumes(self, rollback_id: str, services: Optional[List[str]]) -> List[str]:
        """Backup Docker volumes"""
        volumes_dir = self.backup_dir / rollback_id / "volumes"
        volumes_dir.mkdir(parents=True, exist_ok=True)

        backed_up = []

        try:
            # Get volume list
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                for volume in result.stdout.strip().split('\n'):
                    if volume and "prime-spark" in volume:
                        # Backup volume using docker run
                        backup_file = volumes_dir / f"{volume}.tar.gz"

                        backup_cmd = [
                            "docker", "run", "--rm",
                            "-v", f"{volume}:/data",
                            "-v", f"{volumes_dir}:/backup",
                            "alpine",
                            "tar", "czf", f"/backup/{volume}.tar.gz", "-C", "/data", "."
                        ]

                        result = subprocess.run(backup_cmd, capture_output=True)
                        if result.returncode == 0:
                            backed_up.append(volume)

        except Exception as e:
            print(f"Warning: Volume backup failed: {e}")

        return backed_up

    def _get_all_services(self) -> List[str]:
        """Get list of all services from docker-compose"""
        try:
            result = subprocess.run(
                ["docker-compose", "config", "--services"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                return result.stdout.strip().split('\n')

        except Exception:
            pass

        # Fallback
        return ["redis", "api", "prometheus", "grafana"]

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        return None

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _save_rollback_point(self, rollback_point: RollbackPoint):
        """Save rollback point to index"""
        index = self._load_index()

        # Add rollback point
        rollback_points = index.get("rollback_points", [])
        rollback_points.append(rollback_point.to_dict())

        index["rollback_points"] = rollback_points
        index["last_updated"] = datetime.utcnow().isoformat()

        self._save_index(index)

    def _load_rollback_point(self, rollback_id: str) -> Optional[RollbackPoint]:
        """Load a specific rollback point"""
        index = self._load_index()

        for entry in index.get("rollback_points", []):
            if entry["id"] == rollback_id:
                return RollbackPoint.from_dict(entry)

        return None

    def _load_index(self) -> Dict:
        """Load rollback index"""
        if self.rollback_index.exists():
            with open(self.rollback_index, 'r') as f:
                return json.load(f)

        return {"rollback_points": []}

    def _save_index(self, index: Dict):
        """Save rollback index"""
        with open(self.rollback_index, 'w') as f:
            json.dump(index, f, indent=2)

    def _cleanup_old_rollback_points(self):
        """Remove oldest rollback points if limit exceeded"""
        rollback_points = self.list_rollback_points()

        if len(rollback_points) > self.max_rollback_points:
            # Remove oldest
            to_remove = rollback_points[self.max_rollback_points:]
            for rp in to_remove:
                self.delete_rollback_point(rp.id)
                print(f"Cleaned up old rollback point: {rp.id}")

    def _stop_services(self, services: List[str]):
        """Stop Docker services"""
        cmd = ["docker-compose", "stop"] + services
        subprocess.run(cmd, cwd=self.project_root, check=True)

    def _start_services(self, services: List[str]):
        """Start Docker services"""
        cmd = ["docker-compose", "up", "-d"] + services
        subprocess.run(cmd, cwd=self.project_root, check=True)

    def _restore_configs(self, rollback_point: RollbackPoint):
        """Restore configuration files"""
        config_dir = self.backup_dir / rollback_point.id / "configs"

        for config_file in rollback_point.config_hashes.keys():
            src_path = config_dir / config_file.replace("/", "_")
            dst_path = self.project_root / config_file

            if src_path.exists():
                # Create parent directory if needed
                dst_path.parent.mkdir(parents=True, exist_ok=True)

                # Restore file
                shutil.copy2(src_path, dst_path)
                print(f"  Restored: {config_file}")

    def _restore_docker_images(self, rollback_point: RollbackPoint):
        """Restore Docker images to previous tags"""
        for service, image in rollback_point.docker_images.items():
            print(f"  {service}: {image}")

            # Pull image if not local
            try:
                subprocess.run(
                    ["docker", "pull", image],
                    capture_output=True,
                    check=False
                )
            except Exception:
                pass

    def _restore_volumes(self, rollback_point: RollbackPoint):
        """Restore Docker volumes"""
        volumes_dir = self.backup_dir / rollback_point.id / "volumes"

        for volume in rollback_point.volumes:
            backup_file = volumes_dir / f"{volume}.tar.gz"

            if backup_file.exists():
                # Restore volume
                restore_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{volume}:/data",
                    "-v", f"{volumes_dir}:/backup",
                    "alpine",
                    "sh", "-c",
                    f"rm -rf /data/* && tar xzf /backup/{volume}.tar.gz -C /data"
                ]

                result = subprocess.run(restore_cmd, capture_output=True)
                if result.returncode == 0:
                    print(f"  Restored volume: {volume}")

    def _verify_rollback(self, rollback_point: RollbackPoint) -> bool:
        """Verify rollback was successful"""
        # Check that services are running
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            return result.returncode == 0

        except Exception:
            return False

    def _show_rollback_plan(self, rollback_point: RollbackPoint):
        """Show what would be done in rollback"""
        print("\nRollback plan:")
        print(f"  1. Stop services: {', '.join(rollback_point.services)}")
        print(f"  2. Restore {len(rollback_point.config_hashes)} configuration files")
        print(f"  3. Restore Docker images:")
        for service, image in rollback_point.docker_images.items():
            print(f"     - {service}: {image}")
        if rollback_point.volumes:
            print(f"  4. Restore {len(rollback_point.volumes)} volumes")
        print(f"  5. Start services")

    def _confirm_rollback(self, rollback_point: RollbackPoint) -> bool:
        """Confirm rollback operation"""
        # Auto-confirm in non-interactive mode
        if not os.isatty(0):
            return True

        print("\n⚠️  WARNING: This will rollback the system to a previous state")
        print(f"Rollback point: {rollback_point.description}")
        print(f"Created: {rollback_point.timestamp}")

        response = input("\nProceed with rollback? [yes/no]: ")
        return response.lower() in ["yes", "y"]
