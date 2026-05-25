# Operations Catalog


## API Actions
### Adding a catalog entry
```
curl -X POST http://localhost:5000/catalog \
  -H "Content-Type: application/json" \
  -d @template_entry.json
```

### Deleting a catalog entry
NOTE that this will delete duplicate entries if there are any
```
curl -X DELETE "http://localhost:5000/catalog/name/yourServiceName"
```
### Adding a new field to all entries
sqlite3 catalog.db "UPDATE catalog SET <NEW_FIELD> = '<VALUE_FOR_ALL_FIELDS>';"


### MODIFYING AN ENTRY

TBD
