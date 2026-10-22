"""
Command-line entry point for Copper.

Everything the user types and sees goes through this module. It should stay thin: read input, call into the core, display results.
No agent logic lives here.

"""

GREETING = "Hi, my name is Copper. How can I help you?"

def main() -> int:
    """
    Entry point for the 'copper' command.
    
    Returns the process exit code: 0 for success, non-zero for errors.
    """

    print(GREETING)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
