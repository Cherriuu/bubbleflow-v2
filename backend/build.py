import os


def has_postgres_configuration() -> bool:
    if os.getenv("DATABASE_URL"):
        return True

    return all(
        os.getenv(variable)
        for variable in ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")
    )


def main() -> None:
    if not has_postgres_configuration():
        print("No PostgreSQL configuration found; skipping migrations and demo seed.")
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False)
    call_command("seed_demo")


if __name__ == "__main__":
    main()
