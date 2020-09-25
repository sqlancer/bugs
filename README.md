![Travis](https://travis-ci.com/sqlancer/bugs.svg?branch=master)


This repository stores a list of bugs found by SQLancer with additional metadata.

The main file is `bugs.json`. We use JSON as a format, because we expect it to be easy to manually edit, automatically process, and since we can obtain a meaningful diff output.

You can automatically derive a SQLite database from the JSON file using the following command:

```
./bugs.py export_database
```

In each PR, we automatically validate the JSON file. When changing the file or adding entries to it, be sure to locally check the file before committing it:

```
./bugs.py check
```

To format the JSON file as expected by the check command, you can use the following command:

```
./bugs.py format
```
