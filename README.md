# Operations Catalog


## API Actions
### Adding a catalog entry
```
curl -X POST http://localhost:5000/catalog \
  -H "Content-Type: application/json" \
  -d @post_entry.json
```

### Deleting a catalog entry
NOTE that this will delete duplicate entries if there are any
```
curl -X DELETE "http://localhost:5000/catalog/name/yourServiceName"
```

### MODIFYING AN ENTRY

TBD
