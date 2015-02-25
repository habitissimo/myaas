# Client example

This is a fabric interface for this service, run `fab -l` to get a list of available commands.

Maybe you will need to install some dependencies first, run `pip install -r requirements.txt`.

# Configuration

You will need to export an environment variable with the url to the launcher service.

```
export DB_URL=http://replicator.example.com:5001
fab db.ls
```
