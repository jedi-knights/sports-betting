"""Entry point for the bet CLI."""

import click


@click.group()
def main() -> None:
    """Sports betting modeling and backtesting CLI."""


if __name__ == "__main__":
    main()
