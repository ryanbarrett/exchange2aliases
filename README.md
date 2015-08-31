# exchange2aliases
This script converts Active Directory mail settings to the aliases file format for sendmail/postfix/linux mail server.

Super Alpha version (read: It works in my environment.)

Takes data from

csvde -f test.csv


Converts it to alias file format.


In theory, If you have all the email accounts set up on your linux server(or an external service with a different domain), this should transition email groups from exchange/AD to the aliases file for your linux server.


usage: ad2aliases.py [-h] --csvfile CSVFILE [--outfile OUTFILE]

Arguments that may be parsed.

optional arguments:
  -h, --help            show this help message and exit
  --csvfile CSVFILE, -f CSVFILE
                        The CSV file generated with "csvde -f adfile.csv"
  --outfile OUTFILE, -o OUTFILE
                        outfile if required, otherwise will output as
                        "aliases"
