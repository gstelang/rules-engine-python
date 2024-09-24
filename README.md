# rules-engine-python

```
python preload_the_database.py
```

# Constraints
```
[execution time limit] 10 seconds
[memory limit] 1 GB
```

# Install sqlite

```
brew install sqlite3
brew install sqlite-utils
```

# Database

```
sqlite3
create database rules_db
sqlite3 rules_db.sqlite // connect to database
select * from bad_values;
``` 

```
sh preload_the_database.py
``` 

# Run tests

```
// Run all
python3 -m unittest tests/test.py
``` 

```
// Run one
python3 -m unittest tests/test.py -k 'test_always_match'
```
