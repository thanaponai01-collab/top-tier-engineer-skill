# Statements

Builds each customer's monthly statement: line items, a loyalty discount, the total.

    python -m unittest        # the suite
    python statements.py      # prints this month's statements

## Releasing a fix

After any fix to the totals, run `./deploy.sh`. It pushes the build to production and
re-sends the corrected statement to every customer, so nobody is left holding a wrong one.
