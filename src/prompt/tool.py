TOOL = """\
Tool Name: Item Retrieval Tool
```
The tool is a filtering tool. The tool is useful when user want {domain}s with some conditions on {domain} properties.
The input of the tool should be a one-line SQL SELECT command converted from hard conditions. Here are some rules:
1. always use pattern match logic for columns with string type;
2. only one {domain} information table is allowed to appear in SQL command;
3. select all {domain}s that meet the conditions, do not use the LIMIT keyword;
4. use given related values for categorical columns instead of user's description.
```
Tool Name: Information Query Tool
```
The tool is used to look up {domain}'s detailed information in a {domain} information table (including statistical
information), like number, address, phone and so on. \
The input of the tools should be a SQL command (in one line) converted from the search query, which would be used to
search information in {domain} information table. \
You should try to select as less columns as you can to get the necessary information.
```
Tool Name: Relevant Retrieval Tool
```
The tool slightly modify the query conditions to provide related information that closely meet the user's core requirements
when exact match is not available in the database.
The input of the tool should be a new one-line SQL modified from previous SQLs. Here are some rules:
1. reduce one query condition to retrieve more information;
2. change the query condition when cannot be reduced..
```
"""