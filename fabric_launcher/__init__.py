"""Fabric Launcher - A simple hello world package."""

__version__ = "0.1.0"


def hello_world():
    """Print a hello world message."""
    print("Hello, World from fabric-launcher!")


def main():
    """Main entry point for the package."""
    hello_world()


if __name__ == "__main__":
    main()
