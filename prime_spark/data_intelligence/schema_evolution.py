"""
Schema Evolution Management

Manages schema changes, versioning, compatibility checking, and automated migrations
with support for backward and forward compatibility.
"""

import logging
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import copy

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Supported field types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"
    OBJECT = "object"


class CompatibilityMode(Enum):
    """Schema compatibility modes"""
    BACKWARD = "backward"  # New schema can read old data
    FORWARD = "forward"    # Old schema can read new data
    FULL = "full"          # Both backward and forward compatible
    NONE = "none"          # No compatibility required


class ChangeType(Enum):
    """Types of schema changes"""
    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"
    RENAME_FIELD = "rename_field"
    CHANGE_TYPE = "change_type"
    ADD_CONSTRAINT = "add_constraint"
    REMOVE_CONSTRAINT = "remove_constraint"
    CHANGE_DEFAULT = "change_default"


@dataclass
class Field:
    """Schema field definition"""
    name: str
    field_type: FieldType
    nullable: bool = True
    default_value: Any = None
    constraints: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Schema:
    """Data schema definition"""
    schema_id: str
    version: int
    name: str
    fields: List[Field]
    created_at: datetime
    created_by: str
    description: str
    checksum: str


@dataclass
class SchemaChange:
    """Schema change record"""
    change_id: str
    change_type: ChangeType
    from_version: int
    to_version: int
    field_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    applied_by: str
    rollback_script: Optional[str] = None


@dataclass
class Migration:
    """Schema migration"""
    migration_id: str
    from_schema_id: str
    to_schema_id: str
    from_version: int
    to_version: int
    changes: List[SchemaChange]
    created_at: datetime
    applied_at: Optional[datetime]
    status: str  # pending, applied, failed, rolled_back


class SchemaEvolutionManager:
    """
    Schema Evolution Management System

    Features:
    - Schema versioning and history
    - Compatibility checking (backward, forward, full)
    - Automatic migration generation
    - Schema diff and comparison
    - Rollback support
    - Change validation
    - Multiple schema registry support
    """

    def __init__(
        self,
        compatibility_mode: CompatibilityMode = CompatibilityMode.BACKWARD,
        auto_apply_migrations: bool = False,
    ):
        self.compatibility_mode = compatibility_mode
        self.auto_apply_migrations = auto_apply_migrations

        # Schema registry
        self.schemas: Dict[str, List[Schema]] = {}  # name -> list of versions

        # Migration history
        self.migrations: List[Migration] = []

        # Active schema versions
        self.active_versions: Dict[str, int] = {}

        logger.info(
            f"Initialized SchemaEvolutionManager "
            f"(compatibility: {compatibility_mode.value})"
        )

    def register_schema(
        self,
        name: str,
        fields: List[Field],
        description: str,
        created_by: str = "system",
    ) -> Schema:
        """
        Register a new schema or new version of existing schema

        Args:
            name: Schema name
            fields: List of field definitions
            description: Schema description
            created_by: Creator identifier

        Returns:
            Schema object
        """
        # Determine version number
        if name in self.schemas:
            version = len(self.schemas[name]) + 1

            # Check compatibility with previous version
            prev_schema = self.schemas[name][-1]
            is_compatible, issues = self._check_compatibility(
                prev_schema, fields
            )

            if not is_compatible:
                raise ValueError(
                    f"Schema not compatible with previous version: {', '.join(issues)}"
                )
        else:
            version = 1
            self.schemas[name] = []

        # Generate schema ID and checksum
        schema_id = f"{name}-v{version}"
        checksum = self._calculate_checksum(fields)

        # Create schema
        schema = Schema(
            schema_id=schema_id,
            version=version,
            name=name,
            fields=fields,
            created_at=datetime.now(),
            created_by=created_by,
            description=description,
            checksum=checksum,
        )

        # Store schema
        self.schemas[name].append(schema)
        self.active_versions[name] = version

        logger.info(f"Registered schema: {schema_id}")

        # Generate migration if not first version
        if version > 1:
            migration = self._generate_migration(prev_schema, schema)
            self.migrations.append(migration)

            if self.auto_apply_migrations:
                self._apply_migration(migration)

        return schema

    def get_schema(
        self,
        name: str,
        version: Optional[int] = None,
    ) -> Optional[Schema]:
        """Get schema by name and version"""
        if name not in self.schemas:
            return None

        if version is None:
            # Return latest version
            return self.schemas[name][-1]

        # Return specific version
        for schema in self.schemas[name]:
            if schema.version == version:
                return schema

        return None

    def compare_schemas(
        self,
        schema1: Schema,
        schema2: Schema,
    ) -> List[SchemaChange]:
        """Compare two schemas and return differences"""
        changes = []

        # Build field maps
        fields1 = {f.name: f for f in schema1.fields}
        fields2 = {f.name: f for f in schema2.fields}

        # Find added fields
        for name, field in fields2.items():
            if name not in fields1:
                changes.append(SchemaChange(
                    change_id=f"change-{len(changes)}",
                    change_type=ChangeType.ADD_FIELD,
                    from_version=schema1.version,
                    to_version=schema2.version,
                    field_name=name,
                    old_value=None,
                    new_value=field,
                    timestamp=datetime.now(),
                    applied_by="system",
                ))

        # Find removed fields
        for name, field in fields1.items():
            if name not in fields2:
                changes.append(SchemaChange(
                    change_id=f"change-{len(changes)}",
                    change_type=ChangeType.REMOVE_FIELD,
                    from_version=schema1.version,
                    to_version=schema2.version,
                    field_name=name,
                    old_value=field,
                    new_value=None,
                    timestamp=datetime.now(),
                    applied_by="system",
                ))

        # Find changed fields
        for name in fields1.keys() & fields2.keys():
            field1 = fields1[name]
            field2 = fields2[name]

            if field1.field_type != field2.field_type:
                changes.append(SchemaChange(
                    change_id=f"change-{len(changes)}",
                    change_type=ChangeType.CHANGE_TYPE,
                    from_version=schema1.version,
                    to_version=schema2.version,
                    field_name=name,
                    old_value=field1.field_type.value,
                    new_value=field2.field_type.value,
                    timestamp=datetime.now(),
                    applied_by="system",
                ))

            if field1.default_value != field2.default_value:
                changes.append(SchemaChange(
                    change_id=f"change-{len(changes)}",
                    change_type=ChangeType.CHANGE_DEFAULT,
                    from_version=schema1.version,
                    to_version=schema2.version,
                    field_name=name,
                    old_value=field1.default_value,
                    new_value=field2.default_value,
                    timestamp=datetime.now(),
                    applied_by="system",
                ))

        return changes

    def _check_compatibility(
        self,
        prev_schema: Schema,
        new_fields: List[Field],
    ) -> tuple:
        """Check if new schema is compatible with previous schema"""
        issues = []

        prev_fields = {f.name: f for f in prev_schema.fields}
        new_field_map = {f.name: f for f in new_fields}

        # Check based on compatibility mode
        if self.compatibility_mode in [CompatibilityMode.BACKWARD, CompatibilityMode.FULL]:
            # Backward compatibility: new schema can read old data

            # Check for removed required fields
            for name, field in prev_fields.items():
                if name not in new_field_map and not field.nullable:
                    issues.append(
                        f"Cannot remove required field '{name}' (breaks backward compatibility)"
                    )

            # Check for type changes
            for name in prev_fields.keys() & new_field_map.keys():
                prev_type = prev_fields[name].field_type
                new_type = new_field_map[name].field_type

                if not self._is_compatible_type_change(prev_type, new_type):
                    issues.append(
                        f"Incompatible type change for field '{name}': "
                        f"{prev_type.value} -> {new_type.value}"
                    )

        if self.compatibility_mode in [CompatibilityMode.FORWARD, CompatibilityMode.FULL]:
            # Forward compatibility: old schema can read new data

            # Check for added required fields
            for name, field in new_field_map.items():
                if name not in prev_fields and not field.nullable and field.default_value is None:
                    issues.append(
                        f"Cannot add required field '{name}' without default "
                        f"(breaks forward compatibility)"
                    )

        return len(issues) == 0, issues

    def _is_compatible_type_change(
        self,
        from_type: FieldType,
        to_type: FieldType,
    ) -> bool:
        """Check if type change is compatible"""
        # Same type is always compatible
        if from_type == to_type:
            return True

        # Compatible type promotions
        compatible_changes = {
            FieldType.INTEGER: [FieldType.FLOAT, FieldType.STRING],
            FieldType.FLOAT: [FieldType.STRING],
            FieldType.BOOLEAN: [FieldType.STRING],
        }

        return to_type in compatible_changes.get(from_type, [])

    def _generate_migration(
        self,
        from_schema: Schema,
        to_schema: Schema,
    ) -> Migration:
        """Generate migration between two schemas"""
        changes = self.compare_schemas(from_schema, to_schema)

        migration = Migration(
            migration_id=f"migration-{from_schema.version}-to-{to_schema.version}",
            from_schema_id=from_schema.schema_id,
            to_schema_id=to_schema.schema_id,
            from_version=from_schema.version,
            to_version=to_schema.version,
            changes=changes,
            created_at=datetime.now(),
            applied_at=None,
            status="pending",
        )

        return migration

    def _apply_migration(self, migration: Migration) -> bool:
        """Apply a migration"""
        try:
            logger.info(
                f"Applying migration from v{migration.from_version} "
                f"to v{migration.to_version}"
            )

            # In production, this would:
            # 1. Generate SQL/NoSQL migration scripts
            # 2. Apply schema changes to database
            # 3. Migrate existing data
            # 4. Validate migration

            migration.applied_at = datetime.now()
            migration.status = "applied"

            logger.info(f"Migration applied successfully: {migration.migration_id}")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration.status = "failed"
            return False

    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration"""
        migration = next(
            (m for m in self.migrations if m.migration_id == migration_id),
            None
        )

        if not migration:
            logger.error(f"Migration not found: {migration_id}")
            return False

        if migration.status != "applied":
            logger.error(f"Migration not applied: {migration_id}")
            return False

        try:
            logger.info(f"Rolling back migration: {migration_id}")

            # Reverse the changes
            # In production, execute rollback scripts

            migration.status = "rolled_back"
            logger.info(f"Migration rolled back successfully: {migration_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _calculate_checksum(self, fields: List[Field]) -> str:
        """Calculate schema checksum"""
        # Create deterministic representation
        schema_repr = json.dumps(
            [
                {
                    'name': f.name,
                    'type': f.field_type.value,
                    'nullable': f.nullable,
                }
                for f in sorted(fields, key=lambda x: x.name)
            ],
            sort_keys=True
        )

        return hashlib.sha256(schema_repr.encode()).hexdigest()[:16]

    def get_schema_history(self, name: str) -> List[Schema]:
        """Get version history for a schema"""
        return self.schemas.get(name, [])

    def get_migration_path(
        self,
        name: str,
        from_version: int,
        to_version: int,
    ) -> List[Migration]:
        """Get migration path between two versions"""
        migrations = [
            m for m in self.migrations
            if m.from_version >= from_version and m.to_version <= to_version
        ]

        # Sort by version
        migrations.sort(key=lambda m: m.from_version)

        return migrations

    def validate_data_against_schema(
        self,
        data: Dict,
        schema: Schema,
    ) -> tuple:
        """Validate data against schema"""
        errors = []

        # Check required fields
        for field in schema.fields:
            if not field.nullable and field.name not in data:
                errors.append(f"Missing required field: {field.name}")

        # Check field types
        for field in schema.fields:
            if field.name in data:
                value = data[field.name]

                if value is not None and not self._validate_field_type(
                    value, field.field_type
                ):
                    errors.append(
                        f"Invalid type for field {field.name}: "
                        f"expected {field.field_type.value}"
                    )

        return len(errors) == 0, errors

    def _validate_field_type(self, value: Any, expected_type: FieldType) -> bool:
        """Validate value against expected type"""
        type_validators = {
            FieldType.STRING: lambda v: isinstance(v, str),
            FieldType.INTEGER: lambda v: isinstance(v, int),
            FieldType.FLOAT: lambda v: isinstance(v, (int, float)),
            FieldType.BOOLEAN: lambda v: isinstance(v, bool),
            FieldType.JSON: lambda v: isinstance(v, (dict, list)),
            FieldType.ARRAY: lambda v: isinstance(v, list),
            FieldType.OBJECT: lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(expected_type)
        return validator(value) if validator else True

    def get_statistics(self) -> Dict:
        """Get schema evolution statistics"""
        total_schemas = sum(len(versions) for versions in self.schemas.values())
        total_migrations = len(self.migrations)

        applied_migrations = sum(
            1 for m in self.migrations if m.status == "applied"
        )

        pending_migrations = sum(
            1 for m in self.migrations if m.status == "pending"
        )

        return {
            'total_schema_names': len(self.schemas),
            'total_schema_versions': total_schemas,
            'total_migrations': total_migrations,
            'applied_migrations': applied_migrations,
            'pending_migrations': pending_migrations,
            'compatibility_mode': self.compatibility_mode.value,
            'active_schemas': len(self.active_versions),
        }
