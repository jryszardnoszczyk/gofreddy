"""Entry point: python -m harness"""

from harness.config import Config


def main() -> None:
    config = Config.from_cli_and_env()
    # Imported here to avoid circular imports once run.py exists
    from harness.run import run  # noqa: C0415

    run(config)


if __name__ == "__main__":
    main()
