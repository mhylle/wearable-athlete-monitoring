"""Prompt templates for LLM-powered athlete analysis."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a sports science analyst. Provide concise, actionable insights "
    "based on the athlete data provided. Use bullet points. "
    "Avoid medical diagnoses — focus on training, recovery, and performance optimization."
)

ANALYSIS_TYPES = {
    "recovery_analysis": {
        "label": "Recovery Analysis",
        "description": "Recovery state assessment and readiness recommendations",
    },
    "training_load": {
        "label": "Training Load Analysis",
        "description": "Load management and injury risk assessment",
    },
    "sleep_analysis": {
        "label": "Sleep Analysis",
        "description": "Sleep pattern analysis and improvement recommendations",
    },
    "wellness_trends": {
        "label": "Wellness Trends",
        "description": "Mood, fatigue, and soreness pattern analysis",
    },
    "fitness_progression": {
        "label": "Fitness Progression",
        "description": "Fitness trajectory and goal-setting insights",
    },
}


def build_prompt(analysis_type: str, data: dict) -> str:
    """Build a prompt for a specific analysis type with athlete data context."""
    cfg = ANALYSIS_TYPES[analysis_type]
    data_block = _format_data(data)

    prompts = {
        "recovery_analysis": (
            f"Analyze this athlete's recovery status and readiness to train.\n\n"
            f"## Athlete Data\n{data_block}\n\n"
            f"Focus on:\n"
            f"- Current recovery score and what it means\n"
            f"- HRV trends relative to baseline\n"
            f"- Sleep quality and its impact on recovery\n"
            f"- Readiness recommendation (full training / modified / rest day)\n"
            f"Keep it under 200 words."
        ),
        "training_load": (
            f"Analyze this athlete's training load and injury risk.\n\n"
            f"## Athlete Data\n{data_block}\n\n"
            f"Focus on:\n"
            f"- ACWR zone and what it implies for programming\n"
            f"- Recent load trend (ramping up, maintaining, deloading)\n"
            f"- Injury risk factors based on load patterns\n"
            f"- Specific load adjustment recommendations\n"
            f"Keep it under 200 words."
        ),
        "sleep_analysis": (
            f"Analyze this athlete's sleep patterns.\n\n"
            f"## Athlete Data\n{data_block}\n\n"
            f"Focus on:\n"
            f"- Sleep duration vs recommended 7-9 hours\n"
            f"- Sleep stage distribution (deep, REM, light)\n"
            f"- Sleep quality trends over the past week\n"
            f"- Practical sleep hygiene recommendations\n"
            f"Keep it under 200 words."
        ),
        "wellness_trends": (
            f"Analyze this athlete's wellness trends.\n\n"
            f"## Athlete Data\n{data_block}\n\n"
            f"Focus on:\n"
            f"- Mood and fatigue patterns\n"
            f"- Soreness hotspots or recurring patterns\n"
            f"- Correlation between subjective wellness and objective metrics\n"
            f"- Wellness management recommendations\n"
            f"Keep it under 200 words."
        ),
        "fitness_progression": (
            f"Analyze this athlete's fitness progression.\n\n"
            f"## Athlete Data\n{data_block}\n\n"
            f"Focus on:\n"
            f"- Overall fitness score trajectory\n"
            f"- Which components are improving vs declining\n"
            f"- Key metrics driving fitness changes\n"
            f"- Specific goals and training focus recommendations\n"
            f"Keep it under 200 words."
        ),
    }

    return prompts[analysis_type]


def build_combined_prompt(analysis_results: dict[str, str]) -> str:
    """Build a combined summary prompt from all individual analysis results."""
    sections = []
    for atype, result in analysis_results.items():
        label = ANALYSIS_TYPES.get(atype, {}).get("label", atype)
        sections.append(f"### {label}\n{result}")

    combined = "\n\n".join(sections)

    return (
        f"You have the following individual analyses for an athlete. "
        f"Create a concise executive summary (under 250 words) that:\n"
        f"- Highlights the top 3 most important findings\n"
        f"- Identifies any conflicting signals between analyses\n"
        f"- Provides a clear action plan with priorities\n\n"
        f"## Individual Analyses\n{combined}"
    )


def _format_data(data: dict) -> str:
    """Format data dict into readable text for the LLM prompt."""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"**{key}:**")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"**{key}:** {len(value)} entries")
            for item in value[:5]:  # Show first 5
                if isinstance(item, dict):
                    summary = ", ".join(f"{k}={v}" for k, v in item.items())
                    lines.append(f"  - {summary}")
                else:
                    lines.append(f"  - {item}")
            if len(value) > 5:
                lines.append(f"  - ... and {len(value) - 5} more")
        else:
            lines.append(f"**{key}:** {value}")
    return "\n".join(lines)
