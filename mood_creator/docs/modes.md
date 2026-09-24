# Mode Definition Specification

A **Mode** is a versioned JSON file specifying metadata and a sequential list of automation actions.

## Schema Specification (`schema_version: 1`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | integer | Yes | Mode schema version (default: `1`) |
| `id` | string | Yes | Unique mode identifier (e.g., `guitar_mode`) |
| `name` | string | Yes | User display name |
| `description` | string | No | Mode explanation |
| `icon` | string | No | Emoji or icon string (default: `⚡`) |
| `hotkey` | string | No | Global hotkey string (e.g. `CTRL+ALT+G`) |
| `enabled` | boolean | No | Whether mode is active (default: `true`) |
| `actions` | list | Yes | Array of ActionConfig objects |

## ActionConfig Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `type` | string | Yes | Registered action type string |
| `name` | string | No | Custom step title |
| `params` | object | Yes | Action parameter map |
| `on_failure` | string | No | Failure policy: `"stop"`, `"continue"`, or `"retry"` |
| `retry_count` | integer | No | Retries if failure policy is `"retry"` |
