from setuptools import setup

setup(
    name="MyAas",
    version="0.1b",
    package_data={
        'myaas': 'src/myaas/*',
    },
    include_package_data=True,
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
