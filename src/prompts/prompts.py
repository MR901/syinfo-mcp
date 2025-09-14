# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""
MCP PROMPTS - ALTERNATIVE IMPLEMENTATION

Comprehensive prompt system for FogLAMP MCP server providing clear instructions
and guidance for LLMs to effectively use Tools and Resources.

This implementation provides:
- Proper MCP prompt integration
- Structured prompt templates with parameters
- Comprehensive coverage of FogLAMP capabilities
- Best practices for prompt design
- External visibility and accessibility
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


# ============================================================================
# PROMPT ENUMERATIONS
# ============================================================================

class FogLAMPPrompts(str, Enum):
    """Enumeration of available FogLAMP prompts."""

    SYSTEM_OVERVIEW = "system-overview"
    ASSET_ANALYSIS = "asset-analysis"
    ASSET_EXPLORATION = "asset-exploration"
    SERVICE_MANAGEMENT = "service-management"
    CONFIGURATION_MANAGEMENT = "configuration-management"
    SYSTEM_MONITORING = "system-monitoring"
    AUDIT_ANALYSIS = "audit-analysis"
    ERROR_TROUBLESHOOTING = "error-troubleshooting"
    DATA_ANALYSIS = "data-analysis"
    PLUGIN_MANAGEMENT = "plugin-management"
    NOTIFICATION_SETUP = "notification-setup"
    DATABASE_HEALTH = "database-health"
    SYSLOG_TROUBLESHOOTING = "syslog-troubleshooting"
    EGRESS_BACKLOG_ANALYSIS = "egress-backlog-analysis"
    USER_ADMINISTRATION = "user-administration"
    PLATFORM_DIAGNOSTICS = "platform-diagnostics"
    LLM_EDA = "llm-eda"
    LLM_ANOMALY_DETECTION = "llm-anomaly-detection"
    LLM_FORECASTING = "llm-forecasting"
    LLM_DATA_QUALITY = "llm-data-quality"


class PromptArguments(str, Enum):
    """Enumeration of prompt arguments."""

    ASSET_NAME = "asset_name"
    SERVICE_NAME = "service_name"
    CONFIG_CATEGORY = "config_category"
    TIME_RANGE = "time_range"
    SEVERITY_LEVEL = "severity_level"
    ANALYSIS_TYPE = "analysis_type"
    PLUGIN_TYPE = "plugin_type"
    NOTIFICATION_TYPE = "notification_type"


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_OVERVIEW_PROMPT_TEMPLATE = """
You are an AI assistant with comprehensive access to FogLAMP, an industrial IoT data management platform.
You can help users query and analyze IoT data, monitor system status, manage configurations, and perform advanced data analysis.

## Available Capabilities:

### Data Querying and Analysis
- Query audit logs with filtering by source, severity, and time
- Get system statistics and performance metrics
- Retrieve asset readings and tracking information
- Perform advanced data analysis on asset datapoints
- Access configuration settings and manage them

### System Monitoring and Health
- Monitor service status and health in real-time
- Check system logs and error messages
- Track data ingestion rates and performance
- Analyze asset data flows and patterns
- Monitor system resources and capacity

### Service and Plugin Management
- Manage south services (data ingestion)
- Manage north services (data egress)
- Install and configure plugins
- Monitor service performance and statistics
- Handle service lifecycle operations

### Configuration Management
- View and analyze configuration categories
- Monitor configuration changes
- Update system and service settings
- Understand configuration impact on operations
- Manage data retention and purge policies

### Advanced Data Analysis (LLM-driven)
- Use tools only to retrieve raw data and metadata
- Perform all computations and reasoning yourself
- Detect anomalies and summarize trends using LLM intelligence
- Generate concise summaries and recommended actions

## Usage Guidelines:
1. Use specific tools for data retrieval rather than making assumptions
2. Provide context and explanations for technical data
3. Suggest follow-up queries when appropriate
4. Handle errors gracefully and provide helpful error messages
5. Format responses clearly with relevant data highlighted
6. Use tools only for data retrieval; perform analysis with LLM reasoning
7. Provide actionable insights and recommendations

## Example Interactions:
- "Show me the last 5 error logs from the system"
- "What are the current statistics for data ingestion?"
- "Get configuration details for the storage category"
- "List all assets and their current status"
- "Analyze the temperature sensor data for anomalies"
- "Create a statistical summary of humidity readings"
- "Load asset data and perform trend analysis"
"""

ASSET_ANALYSIS_PROMPT_TEMPLATE = """
You are tasked with performing comprehensive analysis of FogLAMP asset data using only LLM intelligence. Use tools only to fetch raw data; perform all computation and reasoning yourself.

<asset_name>
{asset_name}
</asset_name>

<analysis_type>
{analysis_type}
</analysis_type>

## Analysis Objectives (LLM-only):

### Data Retrieval
1. Fetch recent readings for the asset (bounded by time/limit)
2. If needed and allowed, fetch historical windows via database queries
3. Confirm data availability via asset timespans

### Statistical Analysis
1. Compute descriptive statistics (min, max, mean, std, count)
2. Analyze distributions and percentiles
3. Identify trends/seasonality qualitatively from the series
4. Calculate KPIs relevant to the analysis_type

### Anomaly Detection (LLM-side)
1. Apply simple methods (z-score/IQR/rolling) on returned data
2. Flag timestamps/values as potential outliers
3. Provide short explanations and confidence

### Insights
1. Summarize patterns and operational implications
2. Suggest follow-up data to collect or checks to run
3. Recommend monitoring thresholds if applicable

## Data Retrieval Guidance (no tool names):
- Discover assets and verify availability windows
- Retrieve recent readings with clear limits/time ranges
- If permitted, fetch historical windows in bounded slices

## Workflow:
1. Locate the asset and confirm data availability
2. Fetch a bounded sample (e.g., last N minutes or last 300 points)
3. Perform the analysis steps purely in LLM
4. Produce a concise JSON summary with key metrics and any anomalies
"""

SERVICE_MANAGEMENT_PROMPT_TEMPLATE = """
You are tasked with managing FogLAMP services and ensuring optimal system operation.

<service_name>
{service_name}
</service_name>

<management_action>
{management_action}
</management_action>

## Service Management Objectives:

### Service Discovery and Status
1. List all available services in the system
2. Check current service status and health
3. Identify service types (south, north, core, etc.)
4. Monitor service performance metrics

### Service Configuration
1. Review service configuration settings
2. Update service parameters as needed
3. Configure service schedules and intervals
4. Set up service dependencies and relationships

### Service Lifecycle Management
1. Enable/disable services as required
2. Restart services when necessary
3. Monitor service startup and shutdown
4. Handle service failures and recovery

### Performance Optimization
1. Monitor service performance metrics
2. Identify performance bottlenecks
3. Optimize service configurations
4. Balance system resources

## Available Tools:
- list_services_by_type: List all services with details (optionally by type)
- list_southbound_services: Get detailed south service information
- list_northbound_services: Get detailed north service information
- get_schedule_by_id: Get schedule information for services
- update_schedule_state: Enable/disable service schedules
- get_system_statistics: Monitor service performance

## Management Workflow:
1. Identify the target service and its current state
2. Assess service health and performance
3. Perform the required management action
4. Verify the action was successful
5. Monitor for any issues or side effects
6. Document the changes made

Please begin by identifying the service and assessing its current state.
"""

CONFIGURATION_MANAGEMENT_PROMPT_TEMPLATE = """
You are tasked with managing FogLAMP configuration settings and categories.

<config_category>
{config_category}
</config_category>

<config_action>
{config_action}
</config_action>

## Configuration Management Objectives:

### Configuration Discovery
1. List all available configuration categories
2. Understand configuration structure and hierarchy
3. Identify configuration dependencies
4. Review current configuration values

### Configuration Analysis
1. Analyze current configuration settings
2. Identify configuration issues or conflicts
3. Assess configuration impact on system performance
4. Review security and compliance settings

### Configuration Updates
1. Update configuration values safely
2. Validate configuration changes
3. Monitor system behavior after changes
4. Rollback changes if necessary

### Configuration Documentation
1. Document configuration changes
2. Maintain configuration history
3. Create configuration templates
4. Provide configuration guidance

## Data Retrieval and Change Guidance (no tool names):
- List configuration categories and retrieve details
- Update specific configuration items safely
- Create new configuration categories when needed
- Review related configuration changes from audit trails

## Configuration Workflow:
1. Identify the configuration category and current settings
2. Analyze the impact of proposed changes
3. Make configuration updates safely
4. Verify the changes were applied correctly
5. Monitor system behavior after changes
6. Document the configuration changes

Please begin by examining the current configuration for the specified category.
"""

SYSTEM_MONITORING_PROMPT_TEMPLATE = """
You are tasked with monitoring FogLAMP system health and performance.

<monitoring_focus>
{monitoring_focus}
</monitoring_focus>

<time_range>
{time_range}
</time_range>

## System Monitoring Objectives:

### Health Assessment
1. Check overall system health and status
2. Monitor system uptime and availability
3. Assess system resource utilization
4. Identify potential health issues

### Performance Monitoring
1. Track system performance metrics
2. Monitor data ingestion and processing rates
3. Analyze system throughput and capacity
4. Identify performance bottlenecks

### Data Flow Analysis
1. Monitor data flow through the system
2. Track asset data ingestion rates
3. Analyze north service data transmission
4. Identify data flow issues or delays

### Resource Management
1. Monitor system resource usage
2. Track storage utilization and growth
3. Analyze memory and CPU usage
4. Identify resource constraints

## Data Retrieval Guidance (no tool names):
- Check system health and status
- Retrieve current and historical performance statistics
- Review performance rates for key metrics
- Enumerate services and their status context
- Review recent system activity

## Monitoring Workflow:
1. Assess overall system health and status
2. Monitor key performance indicators
3. Analyze data flow and processing rates
4. Identify any issues or anomalies
5. Provide recommendations for optimization
6. Document monitoring findings

Please begin by checking the overall system health and status.
"""

AUDIT_ANALYSIS_PROMPT_TEMPLATE = """
You are tasked with analyzing FogLAMP audit logs for system insights and troubleshooting.

<severity_level>
{severity_level}
</severity_level>

<time_range>
{time_range}
</time_range>

## Audit Analysis Objectives:

### Log Review and Filtering
1. Retrieve audit logs for the specified time range
2. Filter logs by severity level and source
3. Identify relevant log entries for analysis
4. Organize logs by category and importance

### Pattern Analysis
1. Identify patterns in system events
2. Analyze error frequency and distribution
3. Track service lifecycle events
4. Monitor configuration changes

### Issue Identification
1. Identify system issues and errors
2. Analyze error root causes
3. Assess impact of issues on operations
4. Prioritize issues by severity

### Trend Analysis
1. Analyze trends in system behavior
2. Monitor system stability over time
3. Identify recurring issues
4. Assess system improvement areas

## Data Retrieval Guidance (no tool names):
- Retrieve filtered audit logs for the given criteria
- Query system logs for corroborating evidence
- Correlate findings with system statistics and service status

## Analysis Workflow:
1. Retrieve audit logs for the specified criteria
2. Analyze log patterns and trends
3. Identify issues and their root causes
4. Assess impact and prioritize issues
5. Provide recommendations for resolution
6. Document analysis findings

Please begin by retrieving audit logs for the specified criteria.
"""

ERROR_TROUBLESHOOTING_PROMPT_TEMPLATE = """
You are tasked with troubleshooting FogLAMP system errors and issues.

<error_context>
{error_context}
</error_context>

<system_component>
{system_component}
</system_component>

## Troubleshooting Objectives:

### Error Analysis
1. Identify the type and severity of the error
2. Determine the affected system components
3. Assess the impact on system operations
4. Check for related error patterns

### Root Cause Investigation
1. Investigate the root cause of the error
2. Check system configuration and settings
3. Review recent changes or updates
4. Analyze system logs and audit trails

### Resolution Planning
1. Develop a resolution plan
2. Identify required actions and steps
3. Assess risks and dependencies
4. Plan for error prevention

### Implementation and Verification
1. Implement the resolution plan
2. Verify the error is resolved
3. Monitor system behavior after resolution
4. Document the resolution process

## Data Retrieval Guidance (no tool names):
- Check system health and connectivity
- Review system activity and errors from logs
- Monitor system performance metrics
- Verify service status and health

## Troubleshooting Workflow:
1. Assess the current system state and error impact
2. Investigate the root cause using available tools
3. Develop and implement a resolution plan
4. Verify the error is resolved
5. Monitor system behavior to prevent recurrence
6. Document the troubleshooting process

Please begin by assessing the current system state and error impact.
"""

DATA_ANALYSIS_PROMPT_TEMPLATE = """
You are tasked with performing advanced data analysis on FogLAMP asset data using only LLM intelligence. Use tools strictly to fetch raw data; all analysis is performed by you.

<analysis_scope>
{analysis_scope}
</analysis_scope>

<data_requirements>
{data_requirements}
</data_requirements>

## Data Analysis Objectives (LLM-only):

### Data Retrieval
1. Retrieve asset readings by time windows or limits
2. Use database-backed retrieval only when necessary and allowed
3. Subsample if payload is large; iterate in chunks if needed

### EDA and Statistics
1. Compute descriptive statistics and percentiles
2. Explore distributions, correlations (pairwise where applicable)
3. Identify trends and seasonality qualitatively

### Anomalies and Forecasting (lightweight)
1. Use simple rolling/stationary heuristics for anomaly flags
2. Provide baseline forecasts (moving average, naive, or simple exponential smoothing logic described)
3. State assumptions and uncertainty clearly

### Output
1. Return a compact JSON summary of findings and metrics
2. Provide actionable recommendations and follow-ups

## Data Retrieval Guidance (no tool names):
- Discover assets and their timespans
- Retrieve time-bounded readings with sensible limits
- Use database-backed retrieval only when permitted and bounded

## Workflow:
1. Bound the data request (time/limit)
2. Pull readings and perform EDA/analysis purely in LLM
3. Produce a JSON summary and short narrative
"""

ASSET_EXPLORATION_PROMPT_TEMPLATE = """
You are tasked with exploring FogLAMP assets and their data availability using existing tools.

<asset_name>
{asset_name}
</asset_name>

## Exploration Objectives:

### Asset Inventory
1. List all assets present in the system
2. Identify whether the target asset exists
3. Review available datapoints for the asset

### Data Availability
1. Fetch newest and oldest timestamps for the asset
2. Check approximate volume via statistics or counts
3. Determine whether data is being ingested recently

### Readings Preview
1. Retrieve recent readings for the asset
2. Optionally filter by datapoint
3. Present a concise sample for inspection

## Data Retrieval Guidance (no tool names):
- Enumerate assets and locate the target
- Check oldest/newest timestamps for availability
- Retrieve a small sample of recent readings (limit/filters)
- Cross-check system-level metrics if needed

## Workflow:
1. List and locate the asset
2. Check timespan coverage
3. Fetch a small sample of readings
4. Summarize what data is available and when
"""

PLUGIN_MANAGEMENT_PROMPT_TEMPLATE = """
You are tasked with managing FogLAMP plugins and their installation.

<plugin_type>
{plugin_type}
</plugin_type>

<management_action>
{management_action}
</management_action>

## Plugin Management Objectives:

### Plugin Discovery
1. List available plugins by type
2. Check plugin compatibility and requirements
3. Review plugin documentation and capabilities
4. Assess plugin dependencies

### Plugin Installation
1. Install plugins safely and correctly
2. Verify plugin installation success
3. Configure plugin settings
4. Test plugin functionality

### Plugin Configuration
1. Configure plugin parameters
2. Set up plugin dependencies
3. Configure plugin schedules
4. Test plugin integration

### Plugin Maintenance
1. Monitor plugin performance
2. Update plugins when needed
3. Troubleshoot plugin issues
4. Remove unused plugins

## Data Retrieval and Action Guidance (no tool names):
- Discover available plugins and compatibility
- Install and verify plugins when appropriate
- List installed plugins and versions
- Determine platform compatibility

## Management Workflow:
1. Identify the required plugin and its requirements
2. Check system compatibility and dependencies
3. Install and configure the plugin
4. Test plugin functionality
5. Monitor plugin performance
6. Document plugin configuration

Please begin by identifying the required plugin and checking system compatibility.
"""

DATABASE_HEALTH_PROMPT_TEMPLATE = """
You are tasked with checking FogLAMP database health and accessibility.

## Objectives:
1. Verify database connections and plugin types
2. List available tables and counts where supported
3. Check total readings and per-asset distributions (where feasible)
4. Identify any connectivity or permission issues

## Data Retrieval Guidance (no tool names):
- Check database plugin type, connectivity, and available tables
- Retrieve reading counts and per-asset breakdown
- Probe sample rows to validate access

## Workflow:
1. Run database status and capture plugin and health
2. Fetch statistics and summarize counts
3. Optionally query a small sample to validate read access
4. Report issues and recommended actions
"""

SYSLOG_TROUBLESHOOTING_PROMPT_TEMPLATE = """
You are tasked with investigating system-level issues through syslog.

## Objectives:
1. Retrieve recent syslog entries filtered by keywords
2. Correlate with FogLAMP audit logs when applicable
3. Identify errors, warnings, or crash loops affecting services

## Data Retrieval Guidance (no tool names):
- Query system logs by text/severity
- Correlate with audit logs
- Verify service status/context

## Workflow:
1. Pull recent syslog entries with relevant keywords
2. Cross-reference audit logs for matching timestamps
3. Identify likely root causes and suggest next steps
"""

EGRESS_BACKLOG_ANALYSIS_PROMPT_TEMPLATE = """
You are tasked with analyzing north egress backlog and transmission health.

## Objectives:
1. Inspect UNSENT/SENT statistics and trends
2. List northbound services and destinations
3. Identify bottlenecks or outages in egress

## Data Retrieval Guidance (no tool names):
- Retrieve UNSENT/SENT and related metrics
- Review recent history of statistics
- Inspect north services and destinations

## Workflow:
1. Fetch statistics and highlight UNSENT trends
2. List active north services and their status
3. Recommend actions based on backlog severity
"""

USER_ADMINISTRATION_PROMPT_TEMPLATE = """
You are tasked with reviewing FogLAMP users and access configuration.

## Objectives:
1. List current users and roles
2. Identify authentication mode and potential security gaps
3. Summarize user inventory for audit

## Data Retrieval Guidance (no tool names):
- Retrieve users/roles/access methods
- Inspect authentication mode if relevant

## Workflow:
1. List users and summarize roles and methods
2. Check auth mode to contextualize posture
3. Provide audit-ready summary
"""

PLATFORM_DIAGNOSTICS_PROMPT_TEMPLATE = """
You are tasked with gathering platform diagnostics for plugin and package operations.

## Objectives:
1. Detect OS and architecture
2. List installed FogLAMP packages
3. Prepare information for plugin installation decisions

## Data Retrieval Guidance (no tool names):
- Detect OS and architecture
- List installed FogLAMP packages and versions
- Explore available plugins when relevant

## Workflow:
1. Detect platform information
2. List installed packages and versions
3. Optionally search repository for compatible plugins
"""

NOTIFICATION_SETUP_PROMPT_TEMPLATE = """
You are tasked with setting up FogLAMP notification systems.

<notification_type>
{notification_type}
</notification_type>

<setup_requirements>
{setup_requirements}
</setup_requirements>

## Notification Setup Objectives:

### Notification Planning
1. Define notification requirements
2. Choose appropriate notification types
3. Plan notification delivery methods
4. Set up notification schedules

### Configuration Setup
1. Configure notification rules
2. Set up delivery channels
3. Configure notification thresholds
4. Test notification functionality

### Integration Setup
1. Integrate with external systems
2. Configure authentication and security
3. Set up monitoring and logging
4. Test end-to-end functionality

### Maintenance and Monitoring
1. Monitor notification delivery
2. Track notification performance
3. Update notification settings
4. Troubleshoot notification issues

## Available Tools:
- list_services_by_type: Check notification service status
- get_configuration: Configure notification settings
- search_audit_logs: Monitor notification activity
- list_configuration_categories: Review notification configuration

## Setup Workflow:
1. Define notification requirements and scope
2. Configure notification rules and thresholds
3. Set up delivery channels and integration
4. Test notification functionality
5. Monitor and optimize performance
6. Document notification configuration

Please begin by defining the notification requirements and scope.
"""

# ---------------------------------------------------------------------------
# New LLM-centric prompts for analysis-related use cases
# ---------------------------------------------------------------------------

LLM_EDA_PROMPT_TEMPLATE = """
You are tasked with performing Exploratory Data Analysis (EDA) using only your own reasoning. Use tools strictly to fetch raw data; compute everything yourself.

<asset_name>
{asset_name}
</asset_name>

<time_window>
{time_window}
</time_window>

## Objectives:
1. Fetch a bounded dataset for the asset
2. Compute descriptive stats and percentiles
3. Identify missingness/outliers (approach explicitly stated)
4. Summarize trends and provide concise insights

## Data Retrieval Guidance (no tool names):
- Check asset timespan
- Retrieve bounded readings (limit/time)
- Use database-backed retrieval if permitted

## Output Contract (JSON):
{
  "asset": "...",
  "window": {"from": "...", "to": "...", "count": N},
  "stats": {"datapoint": {"min": x, "max": y, "mean": z, "std": s, "count": n}},
  "anomalies": [{"ts": "...", "dp": "...", "value": v, "reason": "..."}],
  "notes": ["..."],
  "recommendations": ["..."]
}
"""

LLM_ANOMALY_DETECTION_PROMPT_TEMPLATE = """
You are tasked with detecting anomalies using only LLM reasoning on raw readings. Use tools strictly to fetch data.

<asset_name>
{asset_name}
</asset_name>

<datapoint>
{datapoint}
</datapoint>

## Objectives:
1. Retrieve recent/bounded readings
2. Apply simple anomaly strategies (z-score/IQR/rolling)
3. Output flagged points with brief rationale and uncertainty

## Data Retrieval Guidance (no tool names):
- Retrieve bounded readings (limit/time)
- Use database-backed retrieval if permitted

## Output Contract (JSON):
{
  "asset": "...",
  "datapoint": "...",
  "method": "zscore|iqr|rolling",
  "flags": [{"ts": "...", "value": v, "score": s, "reason": "..."}],
  "confidence": "low|medium|high",
  "followups": ["..."]
}
"""

LLM_FORECASTING_PROMPT_TEMPLATE = """
You are tasked with producing a lightweight forecast using only LLM reasoning on recent readings.

<asset_name>
{asset_name}
</asset_name>

<datapoint>
{datapoint}
</datapoint>

<horizon>
{horizon}
</horizon>

## Objectives:
1. Retrieve recent time series window
2. Provide a simple baseline forecast (naive/MA/SES) and justify choice
3. State assumptions and uncertainty clearly

## Data Retrieval Guidance (no tool names):
- Retrieve a recent time series window
- Use database-backed retrieval if permitted

## Output Contract (JSON):
{
  "asset": "...",
  "datapoint": "...",
  "method": "naive|moving_average|ses",
  "horizon": "...",
  "forecast": [{"ts": "...", "value": v}],
  "uncertainty": {"qualitative": "..."},
  "assumptions": ["..."]
}
"""

LLM_DATA_QUALITY_PROMPT_TEMPLATE = """
You are tasked with assessing data quality using only LLM reasoning.

<asset_name>
{asset_name}
</asset_name>

## Objectives:
1. Retrieve recent/bounded readings
2. Detect missingness, duplicates, spikes/flatlines
3. Provide simple quality scores and actionable guidance

## Data Retrieval Guidance (no tool names):
- Check asset timespan
- Retrieve recent/bounded readings

## Output Contract (JSON):
{
  "asset": "...",
  "coverage": {"oldest": "...", "newest": "...", "recent_activity": true},
  "issues": [{"type": "missing|duplicate|spike|flatline", "evidence": "..."}],
  "quality_score": 0.0,
  "actions": ["..."]
}
"""


# ============================================================================
# PROMPT REGISTRATION FUNCTION
# ============================================================================

def register_prompts(mcp_server, config: Optional[Dict[str, Any]] = None):
    """Register all FogLAMP prompts with the MCP server.

    NEW EXPERT AGENT ARCHITECTURE:
    Instead of 20 fragmented prompts, we now use 5 EXPERT AGENTS that embody
    different professional personas with deep domain expertise:
    
    1. OPERATIONS_EXPERT - Senior FogLAMP Operations Engineer
    2. DATA_SCIENTIST - Industrial Data Scientist + OT Expert  
    3. SYSTEM_ENGINEER - Platform & Infrastructure Specialist
    4. DIAGNOSTICS_SPECIALIST - Root Cause Analysis Expert
    5. CONFIGURATION_MANAGER - Settings & Service Config Expert

    Args:
        mcp_server: The MCP server instance to register prompts with
        config: Configuration dictionary for prompt settings
    """
    
    # Import and register the new expert agent system
    from .prompts_persona import register_expert_agents
    register_expert_agents(mcp_server, config)

    # Legacy prompts kept for backward compatibility (can be removed later)
    @mcp_server.prompt()
    def get_system_overview_prompt() -> str:
        """Get the main system overview prompt for FogLAMP MCP interactions.

        Provides comprehensive guidance for LLMs on how to interact with
        FogLAMP system, including available capabilities, usage guidelines,
        and example interactions.

        Returns:
            str: System overview prompt for LLM interactions
        """
        return SYSTEM_OVERVIEW_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_asset_analysis_prompt() -> str:
        """Get prompt for comprehensive asset data analysis.

        Provides detailed guidance for analyzing FogLAMP asset data,
        including data loading, statistical analysis, anomaly detection,
        and visualization.

        Returns:
            str: Asset analysis prompt template
        """
        return ASSET_ANALYSIS_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_service_management_prompt() -> str:
        """Get prompt for service management operations.

        Provides guidance for managing FogLAMP services including
        discovery, configuration, lifecycle management, and optimization.

        Returns:
            str: Service management prompt template
        """
        return SERVICE_MANAGEMENT_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_configuration_management_prompt() -> str:
        """Get prompt for configuration management operations.

        Provides guidance for managing FogLAMP configuration settings,
        including discovery, analysis, updates, and documentation.

        Returns:
            str: Configuration management prompt template
        """
        return CONFIGURATION_MANAGEMENT_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_system_monitoring_prompt() -> str:
        """Get prompt for system monitoring and health assessment.

        Provides guidance for monitoring FogLAMP system health,
        performance, data flow, and resource utilization.

        Returns:
            str: System monitoring prompt template
        """
        return SYSTEM_MONITORING_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_audit_analysis_prompt() -> str:
        """Get prompt for audit log analysis and system insights.

        Provides guidance for analyzing FogLAMP audit logs to identify
        patterns, issues, and system trends.

        Returns:
            str: Audit analysis prompt template
        """
        return AUDIT_ANALYSIS_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_error_troubleshooting_prompt() -> str:
        """Get prompt for error troubleshooting and resolution.

        Provides guidance for troubleshooting FogLAMP system errors,
        including analysis, root cause investigation, and resolution.

        Returns:
            str: Error troubleshooting prompt template
        """
        return ERROR_TROUBLESHOOTING_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_data_analysis_prompt() -> str:
        """Get prompt for advanced data analysis operations.

        Provides guidance for performing advanced data analysis on
        FogLAMP asset data using statistical and machine learning methods.

        Returns:
            str: Data analysis prompt template
        """
        return DATA_ANALYSIS_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_plugin_management_prompt() -> str:
        """Get prompt for plugin management operations.

        Provides guidance for managing FogLAMP plugins including
        discovery, installation, configuration, and maintenance.

        Returns:
            str: Plugin management prompt template
        """
        return PLUGIN_MANAGEMENT_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_notification_setup_prompt() -> str:
        """Get prompt for notification system setup.

        Provides guidance for setting up FogLAMP notification systems
        including planning, configuration, integration, and monitoring.

        Returns:
            str: Notification setup prompt template
        """
        return NOTIFICATION_SETUP_PROMPT_TEMPLATE

    # New prompts leveraging currently available tools
    @mcp_server.prompt()
    def get_asset_exploration_prompt() -> str:
        """Get prompt for asset discovery and data availability exploration."""
        return ASSET_EXPLORATION_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_database_health_prompt() -> str:
        """Get prompt for database health and access verification."""
        return DATABASE_HEALTH_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_syslog_troubleshooting_prompt() -> str:
        """Get prompt for syslog-driven troubleshooting."""
        return SYSLOG_TROUBLESHOOTING_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_egress_backlog_analysis_prompt() -> str:
        """Get prompt for analyzing north egress backlog and health."""
        return EGRESS_BACKLOG_ANALYSIS_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_user_administration_prompt() -> str:
        """Get prompt for user inventory and authentication posture review."""
        return USER_ADMINISTRATION_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_platform_diagnostics_prompt() -> str:
        """Get prompt for platform diagnostics for plugin/package operations."""
        return PLATFORM_DIAGNOSTICS_PROMPT_TEMPLATE

    # New LLM-only analysis prompts
    @mcp_server.prompt()
    def get_llm_eda_prompt() -> str:
        """Get prompt for LLM-only EDA."""
        return LLM_EDA_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_llm_anomaly_detection_prompt() -> str:
        """Get prompt for LLM-only anomaly detection."""
        return LLM_ANOMALY_DETECTION_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_llm_forecasting_prompt() -> str:
        """Get prompt for LLM-only lightweight forecasting."""
        return LLM_FORECASTING_PROMPT_TEMPLATE

    @mcp_server.prompt()
    def get_llm_data_quality_prompt() -> str:
        """Get prompt for LLM-only data quality assessment."""
        return LLM_DATA_QUALITY_PROMPT_TEMPLATE

    _logger.info("FogLAMP MCP Prompts registered successfully")


# ============================================================================
# PROMPT UTILITY FUNCTIONS
# ============================================================================

def get_prompt_by_name(prompt_name: str) -> Optional[str]:
    """Get a specific prompt template by name.

    Provides external access to prompt templates for visibility and
    observability from outside the MCP server.

    Args:
        prompt_name (str): Name of the prompt to retrieve

    Returns:
        Optional[str]: The requested prompt template or None if not found
    """
    prompt_map = {
        FogLAMPPrompts.SYSTEM_OVERVIEW: SYSTEM_OVERVIEW_PROMPT_TEMPLATE,
        FogLAMPPrompts.ASSET_ANALYSIS: ASSET_ANALYSIS_PROMPT_TEMPLATE,
        FogLAMPPrompts.SERVICE_MANAGEMENT: SERVICE_MANAGEMENT_PROMPT_TEMPLATE,
        FogLAMPPrompts.CONFIGURATION_MANAGEMENT: CONFIGURATION_MANAGEMENT_PROMPT_TEMPLATE,
        FogLAMPPrompts.SYSTEM_MONITORING: SYSTEM_MONITORING_PROMPT_TEMPLATE,
        FogLAMPPrompts.AUDIT_ANALYSIS: AUDIT_ANALYSIS_PROMPT_TEMPLATE,
        FogLAMPPrompts.ERROR_TROUBLESHOOTING: ERROR_TROUBLESHOOTING_PROMPT_TEMPLATE,
        FogLAMPPrompts.DATA_ANALYSIS: DATA_ANALYSIS_PROMPT_TEMPLATE,
        FogLAMPPrompts.PLUGIN_MANAGEMENT: PLUGIN_MANAGEMENT_PROMPT_TEMPLATE,
        FogLAMPPrompts.NOTIFICATION_SETUP: NOTIFICATION_SETUP_PROMPT_TEMPLATE,
    }

    return prompt_map.get(prompt_name)


def list_available_prompts() -> List[str]:
    """List all available prompt names.

    Provides external visibility into available prompts for
    documentation and discovery purposes.

    Returns:
        List[str]: List of all available prompt names
    """
    return [prompt.value for prompt in FogLAMPPrompts]


def format_prompt_template(template: str, **kwargs) -> str:
    """Format a prompt template with provided parameters.

    Safely formats prompt templates with provided parameters,
    handling missing parameters gracefully.

    Args:
        template (str): The prompt template to format
        **kwargs: Parameters to substitute in the template
    
    Returns:
        str: Formatted prompt template
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        _logger.warning(f"Missing parameter in prompt template: {e}")
        # Replace missing parameters with placeholder text
        for key in kwargs:
            template = template.replace(f"{{{key}}}", str(kwargs[key]))
        return template


def get_prompt_metadata() -> Dict[str, Any]:
    """Get metadata about all available prompts.

    Provides comprehensive metadata about prompts including
    descriptions, parameters, and usage information.

    Returns:
        Dict[str, Any]: Metadata about all prompts
    """
    return {
        "total_prompts": len(FogLAMPPrompts),
        "prompts": {
            FogLAMPPrompts.SYSTEM_OVERVIEW: {
                "description": "Main system overview and capabilities guide",
                "parameters": [],
                "category": "system"
            },
            FogLAMPPrompts.ASSET_ANALYSIS: {
                "description": "Comprehensive asset data analysis guidance",
                "parameters": ["asset_name", "analysis_type"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.ASSET_EXPLORATION: {
                "description": "Explore assets, availability and preview readings",
                "parameters": ["asset_name"],
                "category": "assets"
            },
            FogLAMPPrompts.SERVICE_MANAGEMENT: {
                "description": "Service management and lifecycle operations",
                "parameters": ["service_name", "management_action"],
                "category": "service_management"
            },
            FogLAMPPrompts.CONFIGURATION_MANAGEMENT: {
                "description": "Configuration management and updates",
                "parameters": ["config_category", "config_action"],
                "category": "configuration"
            },
            FogLAMPPrompts.SYSTEM_MONITORING: {
                "description": "System health and performance monitoring",
                "parameters": ["monitoring_focus", "time_range"],
                "category": "monitoring"
            },
            FogLAMPPrompts.AUDIT_ANALYSIS: {
                "description": "Audit log analysis and system insights",
                "parameters": ["severity_level", "time_range"],
                "category": "audit"
            },
            FogLAMPPrompts.ERROR_TROUBLESHOOTING: {
                "description": "Error troubleshooting and resolution",
                "parameters": ["error_context", "system_component"],
                "category": "troubleshooting"
            },
            FogLAMPPrompts.DATA_ANALYSIS: {
                "description": "Advanced data analysis and statistics",
                "parameters": ["analysis_scope", "data_requirements"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.PLUGIN_MANAGEMENT: {
                "description": "Plugin installation and management",
                "parameters": ["plugin_type", "management_action"],
                "category": "plugin_management"
            },
            FogLAMPPrompts.NOTIFICATION_SETUP: {
                "description": "Notification system setup and configuration",
                "parameters": ["notification_type", "setup_requirements"],
                "category": "notification"
            },
            FogLAMPPrompts.LLM_EDA: {
                "description": "LLM-only exploratory data analysis",
                "parameters": ["asset_name", "time_window"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.LLM_ANOMALY_DETECTION: {
                "description": "LLM-only anomaly detection for a datapoint",
                "parameters": ["asset_name", "datapoint"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.LLM_FORECASTING: {
                "description": "LLM-only lightweight forecasting",
                "parameters": ["asset_name", "datapoint", "horizon"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.LLM_DATA_QUALITY: {
                "description": "LLM-only data quality assessment",
                "parameters": ["asset_name"],
                "category": "data_analysis"
            },
            FogLAMPPrompts.DATABASE_HEALTH: {
                "description": "Database connectivity and statistics review",
                "parameters": [],
                "category": "database"
            },
            FogLAMPPrompts.SYSLOG_TROUBLESHOOTING: {
                "description": "Investigate issues via syslog and audit correlation",
                "parameters": [],
                "category": "troubleshooting"
            },
            FogLAMPPrompts.EGRESS_BACKLOG_ANALYSIS: {
                "description": "Analyze UNSENT backlog and north service health",
                "parameters": [],
                "category": "monitoring"
            },
            FogLAMPPrompts.USER_ADMINISTRATION: {
                "description": "Review FogLAMP users and auth posture",
                "parameters": [],
                "category": "security"
            },
            FogLAMPPrompts.PLATFORM_DIAGNOSTICS: {
                "description": "Gather platform diagnostics for plugin/package ops",
                "parameters": [],
                "category": "platform"
            }
        },
        "categories": {
            "system": "System overview and general guidance",
            "data_analysis": "Data analysis and statistical operations",
            "assets": "Asset inventory and data availability",
            "service_management": "Service lifecycle and management",
            "configuration": "Configuration management and updates",
            "monitoring": "System monitoring and health assessment",
            "audit": "Audit log analysis and system insights",
            "troubleshooting": "Error troubleshooting and resolution",
            "plugin_management": "Plugin installation and management",
            "notification": "Notification system setup and configuration",
            "database": "Database health and statistics",
            "security": "Users and authentication posture",
            "platform": "OS/arch and installed packages"
        }
    }
