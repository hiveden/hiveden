# Specification: Automated Backups

## Context
Data integrity and recovery are critical for any server management system. This track aims to implement a robust backup solution for both the PostgreSQL database used by Hiveden and the application's critical data.

## Goals
1.  **PostgreSQL Backup:**
    -   Automate the backup process for PostgreSQL databases.
    -   Ensure backups are stored securely.
    -   Provide a mechanism to restore from these backups.

2.  **Application Data Backup:**
    -   Identify and backup critical Hiveden application data (configuration files, etc.).
    -   Ensure data can be restored in case of corruption or loss.

3.  **Automation & Scheduling:**
    -   Allow users to schedule backups (e.g., daily, weekly).
    -   Integrate with the existing job scheduling system if available, or implement a new one.

## Requirements
-   **CLI Commands:**
    -   `hiveden backup create`: Trigger an immediate backup.
    -   `hiveden backup list`: List available backups.
    -   `hiveden backup restore <backup_id>`: Restore from a specific backup.
    -   `hiveden backup schedule`: Configure backup schedules.
-   **API Endpoints:**
    -   Corresponding endpoints for triggering, listing, restoring, and scheduling backups.
-   **Storage:**
    -   Backups should be stored in a configurable local directory initially.
    -   Future support for remote storage (S3, etc.) should be considered in the design.
-   **Retention Policy:**
    -   Implement a basic retention policy (e.g., keep last N backups) to manage storage usage.

## Technical Considerations
-   Use `pg_dump` and `pg_restore` for PostgreSQL operations.
-   Use standard file archiving tools (e.g., `tar`, `zip`) for application data.
-   Ensure operations are atomic where possible to prevent partial backups.
-   Leverage `hiveden.config` for storing backup settings.
