from langchain_core.tools import tool
from datetime import datetime, timedelta

@tool
def court_timeline(start_date: str, add_days: int) -> str:
    """
    Calculates procedural deadlines by adding a specified number of days to a start date.
    start_date should be in 'YYYY-MM-DD' format.
    Example: court_timeline("2024-01-01", 30) returns "2024-01-31"
    """
    try:
        date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        deadline = date_obj + timedelta(days=add_days)
        return deadline.strftime("%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        return f"Error calculating timeline: {str(e)}"
