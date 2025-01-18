"""Shared utilities for FireScraper."""


class Colors:
    """ANSI color codes for terminal output."""

    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def format_error(message: str) -> str:
    """Format an error message with color."""
    return f"{Colors.RED}Error: {message}{Colors.RESET}"


def format_success(message: str) -> str:
    """Format a success message with color."""
    return f"{Colors.GREEN}{message}{Colors.RESET}"


def format_info(message: str) -> str:
    """Format an info message with color."""
    return f"{Colors.BLUE}{message}{Colors.RESET}"


def format_warning(message: str) -> str:
    """Format a warning message with color."""
    return f"{Colors.YELLOW}{message}{Colors.RESET}"
