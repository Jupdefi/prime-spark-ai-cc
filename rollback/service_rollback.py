"""
Service-specific rollback operations.
"""

import subprocess
import time
from typing import Dict, List, Optional
from pathlib import Path


class ServiceRollback:
    """
    Base class for service-specific rollback operations.
    """

    def __init__(self, service_name: str, project_root: str = "."):
        """
        Initialize service rollback.

        Args:
            service_name: Name of the service
            project_root: Project root directory
        """
        self.service_name = service_name
        self.project_root = Path(project_root)

    def pre_rollback(self) -> bool:
        """
        Operations to perform before rollback.

        Returns:
            True if successful
        """
        print(f"  [{self.service_name}] Pre-rollback checks...")
        return True

    def rollback(self, target_version: Optional[str] = None) -> bool:
        """
        Perform service rollback.

        Args:
            target_version: Target version to rollback to

        Returns:
            True if successful
        """
        print(f"  [{self.service_name}] Rolling back...")
        return True

    def post_rollback(self) -> bool:
        """
        Operations to perform after rollback.

        Returns:
            True if successful
        """
        print(f"  [{self.service_name}] Post-rollback verification...")
        return True

    def verify_health(self) -> bool:
        """
        Verify service health after rollback.

        Returns:
            True if healthy
        """
        print(f"  [{self.service_name}] Health check...")

        try:
            # Check if container is running
            result = subprocess.run(
                ["docker-compose", "ps", self.service_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            return result.returncode == 0 and "Up" in result.stdout

        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
            return False


class RedisRollback(ServiceRollback):
    """Redis service rollback"""

    def __init__(self, project_root: str = "."):
        super().__init__("redis", project_root)

    def pre_rollback(self) -> bool:
        """Backup Redis data before rollback"""
        print(f"  [{self.service_name}] Backing up Redis data...")

        try:
            # Trigger Redis save
            subprocess.run(
                ["docker-compose", "exec", "-T", "redis", "redis-cli", "SAVE"],
                capture_output=True,
                cwd=self.project_root,
                timeout=30
            )

            return True

        except Exception as e:
            print(f"  ⚠ Warning: Redis backup failed: {e}")
            return True  # Continue anyway

    def verify_health(self) -> bool:
        """Verify Redis is responding"""
        print(f"  [{self.service_name}] Health check...")

        try:
            # Ping Redis
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "redis", "redis-cli", "PING"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )

            if result.returncode == 0 and "PONG" in result.stdout:
                print(f"  ✓ Redis is healthy")
                return True

        except Exception as e:
            print(f"  ✗ Health check failed: {e}")

        return False


class APIRollback(ServiceRollback):
    """API service rollback"""

    def __init__(self, project_root: str = "."):
        super().__init__("api", project_root)

    def pre_rollback(self) -> bool:
        """Check API dependencies before rollback"""
        print(f"  [{self.service_name}] Checking dependencies...")

        # Ensure Redis is available
        redis_check = subprocess.run(
            ["docker-compose", "ps", "redis"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )

        if "Up" not in redis_check.stdout:
            print(f"  ⚠ Warning: Redis is not running")

        return True

    def post_rollback(self) -> bool:
        """Wait for API to be ready after rollback"""
        print(f"  [{self.service_name}] Waiting for API to be ready...")

        # Wait up to 30 seconds for API to start
        for i in range(30):
            try:
                result = subprocess.run(
                    ["docker-compose", "exec", "-T", "api", "curl", "-f", "http://localhost:8000/health"],
                    capture_output=True,
                    cwd=self.project_root,
                    timeout=2
                )

                if result.returncode == 0:
                    print(f"  ✓ API is ready")
                    return True

            except Exception:
                pass

            time.sleep(1)

        print(f"  ⚠ Warning: API did not become ready within timeout")
        return True

    def verify_health(self) -> bool:
        """Verify API health endpoint"""
        print(f"  [{self.service_name}] Health check...")

        try:
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "api", "curl", "-f", "http://localhost:8000/health"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )

            if result.returncode == 0:
                print(f"  ✓ API is healthy")
                return True

        except Exception as e:
            print(f"  ✗ Health check failed: {e}")

        return False


class PrometheusRollback(ServiceRollback):
    """Prometheus service rollback"""

    def __init__(self, project_root: str = "."):
        super().__init__("prometheus", project_root)

    def post_rollback(self) -> bool:
        """Reload Prometheus configuration"""
        print(f"  [{self.service_name}] Reloading configuration...")

        try:
            # Send reload signal to Prometheus
            subprocess.run(
                ["docker-compose", "exec", "-T", "prometheus", "kill", "-HUP", "1"],
                capture_output=True,
                cwd=self.project_root,
                timeout=5
            )

            time.sleep(2)
            return True

        except Exception as e:
            print(f"  ⚠ Warning: Config reload failed: {e}")
            return True

    def verify_health(self) -> bool:
        """Verify Prometheus is responding"""
        print(f"  [{self.service_name}] Health check...")

        try:
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "prometheus", "wget", "-q", "-O-", "http://localhost:9090/-/healthy"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )

            if result.returncode == 0 and "Prometheus" in result.stdout:
                print(f"  ✓ Prometheus is healthy")
                return True

        except Exception as e:
            print(f"  ✗ Health check failed: {e}")

        return False


class GrafanaRollback(ServiceRollback):
    """Grafana service rollback"""

    def __init__(self, project_root: str = "."):
        super().__init__("grafana", project_root)

    def post_rollback(self) -> bool:
        """Wait for Grafana to initialize"""
        print(f"  [{self.service_name}] Waiting for Grafana to initialize...")

        time.sleep(5)
        return True

    def verify_health(self) -> bool:
        """Verify Grafana is responding"""
        print(f"  [{self.service_name}] Health check...")

        try:
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "grafana", "curl", "-f", "http://localhost:3000/api/health"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )

            if result.returncode == 0:
                print(f"  ✓ Grafana is healthy")
                return True

        except Exception as e:
            print(f"  ✗ Health check failed: {e}")

        return False


def get_service_rollback(service_name: str, project_root: str = ".") -> ServiceRollback:
    """
    Factory function to get appropriate service rollback handler.

    Args:
        service_name: Name of service
        project_root: Project root directory

    Returns:
        ServiceRollback instance
    """
    rollback_classes = {
        "redis": RedisRollback,
        "api": APIRollback,
        "prometheus": PrometheusRollback,
        "grafana": GrafanaRollback
    }

    rollback_class = rollback_classes.get(service_name, ServiceRollback)
    return rollback_class(project_root)
