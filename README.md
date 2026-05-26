# Operations Catalog


## API Actions

### Get all catalog entries
This will return all entries sorted by the catalog id number

curl "http://localhost:5000/catalog" | jq '.[].serviceName'

### Get a catalog entry
A JSON response will be returned

NOTE: The serviceName is case sensitive
```
curl "http://localhost:5000/catalog/name/yourServiceName"
```

### Updating a field for one catalog entry
Example
```
curl -X PUT http://localhost:5000/catalog/name/<serviceName> \
  -H "Content-Type: application/json" \
  -d '{"yourField": "yourValue"}'
```

### Add a new catalog entry
```
curl -X POST http://localhost:5000/catalog \
  -H "Content-Type: application/json" \
  -d @template-entry.json
```

### Adding a new field for all catalog entries

TO-DO


Example: Adding a field called "testField" \
Connect to the postGres DB 
```
catalog=# ALTER TABLE catalog ADD COLUMN "testField" TEXT;
```

Update the schema \
Add this:
```
testField                   TEXT,
```

Update the index.html \
Add this:
```
${field('Test Field', e.testField)}
```

### Deleting a catalog entry
NOTE that this will delete duplicate entries if there are any
```
curl -X DELETE "http://localhost:5000/catalog/name/yourServiceName"
```
