# HQ ARCHITECTURE: THE MASTER MAP

## Overview
The Global HQ is a distributed dashboard system serving as the central nervous system for Alpha. It consists of multiple specialized modules providing real-time visibility into agent states, organizational data, research, and mission-critical operations.

## Directory Structure
- `/` - Root landing page.
- `/mission-control/` - High-level operational oversight.
- `/office/` - Real-time agent status and interaction logs.
- `/org/` & `/org2/` - Organizational structure and technical documentation.
- `/posts/` - Published content and internal communications.
- `/schedule/` - Time-based event tracking.
- `/security/` - Surveillance and system hardening status.
- `/usage/` - Resource consumption metrics.
- `/vault/` - Secure storage and sensitive data access.
- `/briefing/` - Daily morning briefings (Managed separately).

## Data Flow & Hydration
- **Static Assets:** HTML templates and CSS are served directly.
- **Dynamic Data:** Hydrated via local JSON files (`agent_data.json`, `status.json`, `posts_data.json`) or direct database queries.
- **Background Processes:** Python scripts (`update_status.py`, etc.) bridge the gap between agent state and the HQ frontend.

## Infrastructure
- **Server:** Local Gateway.
- **Database:** `chiefos.db` (Primary state store).
- **Update Mechanism:** Periodic script execution or event-driven updates.
