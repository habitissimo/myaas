# Client example

This is a fabric interface for this service, run `fab -l` to get a list of available commands.

Maybe you will need to install some dependencies first, run `pip install -r requirements.txt`.

# Configuration

You will need to export an environment variable with the url to the myaas service.

```
export DB_URL=http://localhost:5001

# show created databases
fab db.ls

# show available templates for new databases
fab db.templates

# create a new database foo from template bar
fab db.new:bar,foo

# delete the database
fab db.rm:bar,foo
```
