"""View generation for improveit-dashboard."""

from improveit_dashboard.views.dashboard import generate_dashboard
from improveit_dashboard.views.reports import generate_user_reports

__all__ = [
    "generate_dashboard",
    "generate_user_reports",
]
