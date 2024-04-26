# Implement the rules engine to classify emails

## Motivation for the change

While models do an amazing job with scoring emails - we still
want to have a possibility to decide if the email is good/bad
based on heuristics predefined by humans.

The RulesEngine class will help define such rules.

You would want to use this class if you need to:
* Make a decision about an email if the model is "unsure".
* Specify hard rules which don't take into account the model.
For example - if you want to check if the email comes from the
list of known bad email domains.

## Summary

The RulesEngine class implemented in the `rules_engine.py` file.

The tests for the class are implemented in the `tests/test.py` file.

The class can accept the rules that execute on:
* The email subject.
* The email body.
* The sender's email and email domain.

It is able to make the full-text match and the regex match.
The class also supports executing SQL queries to see if the 
email matches the rule.
For now - we are using the SQLite database, which can be replaced 
in the future with PostgreSQL. 

The class will return an error as early as possible to make sure
that we don't introduce any unnecessary delays.

## Testing

Unit tests were added to the PR which should cover most of the cases.
The class was also tested locally in python console.