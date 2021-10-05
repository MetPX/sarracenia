#!/usr/bin/env python3
"""comments:
    This plugin modifies the date of parent.line to a standard date fomrat: year-month-date hours:minutes:seconds
    An example of this date format is : 2021-09-06 11:09:00, which is Septemebr 6th, 2021 11:09PM
    This uses the dateparser package and parse() method. The timezone is 'UTC' by default, but the
    destination_timezone can be modified in the configs to any other timezone and will be converted to 'UTC'
    If year is not provided, this means that the file is < 6 months old, so depending on todays date, assign
    appropriate year (for todays year: jan-jun -> assign prev year, for jul-dec assign current year)
"""
class Line_date(object):
    def __init__(self, parent):
        pass

    def normalize_date_format(self, parent):
        import dateparser
        line_split = parent.line.split()
        # specify input for this routine, line format could change
        # line_mode.py format "-rwxrwxr-x 1 1000 1000 8123 24 Mar 22:54 2017-03-25-0254-CL2D-AUTO-minute-swob.xml"
        file_date = line_split[5] + " " + line_split[6] + " " + line_split[7]
        # case 1: the date contains '-' implies the date is in 1 string not 3 seperate ones, and H:M is also provided
        if "-" in file_date: file_date = line_split[5] + " " + line_split[6]
        current_date = datetime.datetime.now()
        standard_date_format = dateparser.parse(file_date,
                                                settings={
                                                    'RELATIVE_BASE': datetime.datetime(1900, 1, 1),
                                                    'TIMEZONE': parent.destination_timezone,
                                                    'TO_TIMEZONE': 'UTC'})
        if standard_date_format is not None:
            type(standard_date_format)
            # case 2: the year was not given, it is defaulted to 1900. Must find which year (this one or last one).
            if standard_date_format.year == 1900:
                if standard_date_format.month - current_date.month >= 6:
                    standard_date_format = standard_date_format.replace(year=(current_date.year - 1))
                else:
                    standard_date_format = standard_date_format.replace(year=current_date.year)
            parent.logger.debug("Oldline is: " + parent.line)
            parent.line = parent.line.replace(file_date, str(standard_date_format))
            parent.logger.debug("Newline is: " + parent.line)
        return

    def perform(self,parent):
        if hasattr(parent, 'line'):
            self.normalize_date_format(parent)
        return True

line_date = Line_date(self)
self.on_line = line_date.perform