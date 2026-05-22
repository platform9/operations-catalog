# operational_catalog


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

## Local development
### Starting local API
```
cd local_build/operational_catalog
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Wipe and re-seed the database
```
rm -f catalog.db
python seed.py
```

### Restart the server
```
python app.py
```

### Open local UI
```
open index.html
```