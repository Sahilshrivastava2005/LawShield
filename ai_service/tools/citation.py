from langchain_core.tools import tool

@tool
def format_citation(case_name: str, volume: str, reporter: str, first_page: str, year: str) -> str:
    """
    Formats a legal case citation into standard Bluebook format.
    Provide the case name, reporter volume, reporter abbreviation, first page, and year.
    Example: format_citation("Smith v. Jones", "123", "F.3d", "456", "2010") -> "Smith v. Jones, 123 F.3d 456 (2010)"
    """
    return f"{case_name}, {volume} {reporter} {first_page} ({year})"
