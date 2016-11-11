from setuptools import setup

setup(
    name="MyAas",
    version="0.1b",
    packages=[
        "src/myaas"
    ],
    install_requires=[
        "Flask",
        "requests",
        "docker-py",
        "PyMySQL",
        "psycopg2",
        "gunicorn",
        "python-decouple",
    ],
)
