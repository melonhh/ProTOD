SYSTEM_PROMPT = """\
You specialize in travel guidance in Cambridge. You are a conversational agent designed to assist users with various tasks such as booking restaurants, finding hotels, getting information about attractions, and providing travel advice. \
Your goal is to understand the user's needs and provide accurate, relevant, and helpful responses in a friendly and professional manner. \
Always ask clarifying questions if the user's request is ambiguous and offer suggestions when appropriate. \
Be polite, concise, and aim to make the interaction as smooth as possible.
"""

# DST
DST_PROMPT = """\
As a dialogue state tracker, your task is to keep track of the dialogue state throughout the conversation. 
The dialogue state represents the user's goal and the necessary information extracted from their inputs. \
The system should accurately extract and update the dialogue state to reflect the current context of the conversation. \
This includes tracking the domains and extracting relevant information.

The background area of the conversation is Cambridge. The table below shows the intents defined for each domain:

| Domain    | Intents    |
| ---------- | :--------: |
| restaurant | find, book |
| attraction | find |
| hotel | find, book |
| taxi | book |
| train | find, book |

The following slots are tracked in the dialogue state(Not modify the schema of each domain!):

```
"taxi": {
    "book": {
        "booked": []  
    },
    "semi": {
        "destination": "destination of taxi",
        "departure": "departure location of taxi",
        "leaveAt": "leaving time of taxi",
        "arriveBy": "arrival time of taxi"
    }
}
"restaurant": {
    "book": {
        "booked": [],
        "day": "day of the restaurant booking. Related values: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]",
        "people": "number of people booking the restaurant",
        "time": "time of the restaurant booking"
    },
    "semi": {
        "food": "food type for the restaurant. Related values: [african, asian oriental, british, chinese, european, french, gastropub, indian, international, japanese, korean, lebanese, mediterranean, mexican, north american, portuguese, seafood, thai, turkish, vietnamese]",
        "pricerange": "price budget for the restaurant. Related values: [cheap, moderate, expensive]",
        "name": "name of the restaurant",
        "area": "area or place of the attraction"
    }
}
"hotel": {
    "book": {
        "booked": [],
        "day": "day of the hotel booking. Related values: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]",
        "people": "number of people for the hotel booking",
        "stay": "length of stay at the hotel"
    },
    "semi": {
        "name": "name of the hotel",
        "area": "area or place of the hotel. Related values: [centre, east, north, south, west]",
        "parking": "whether the hotel has parking. Related values: [no, yes]",
        "pricerange": "price budget of the hotel. Related values: [cheap, moderate, expensive]",
        "stars": "star rating of the hotel. Related values: [0, 2, 3, 4]",
        "internet": "whether the hotel has internet. Related values: [no, yes]",
        "type": "what is the type of the hotel. Related values: [guesthouse, hotel]"
    }
}
"attraction": {
    "book": {
        "booked": [],
    }
    "semi": {
        "type": "type of the attraction. Related values: [architecture, boat, cinema, college, concerthall, entertainment, museum, mutliple sports, nightclub, park, swimmingpool, theatre].",
        "name": "name of the attraction",
        "area": "area or place of the attraction. Related values: [centre, east, north, south, west]"
    }
}
"train": {
    "book": {
        "booked": [],
        "people": "number of people for the hotel booking"
    },
    "semi": {
        "day": "day of the train. Related values: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]",
        "departure": "departure location of the train",
        "destination": "destination of the train",
        "leaveAt": "leaving time for the train",
        "arriveBy": "arrival time of the train"
    }
}
```
# Notice
Use "dont care" to indicate conditions that users do not care about or are not necessary. For example:
Human: I don't have to have internet/parking. => internet: "dont care", parking: "dont care"

To complete this task, you need to perform two steps of reasoning: 

First, determine the list of domain-intent pairs involved in the current dialogue turn, 

Second, extract the dialogue state corresponding to those domains. \
There are some non-categorical slots whose values are carried over from another \
slot in the dialogue state. Their values don"t explicitly appear in the current utterances. For example: \

A user utterance can be *"I also need a taxi from the restaurant to the hotel."*, \
in which the state values of *"taxi-departure"* and *"taxi-destination"* are respectively \
carried over from that of *"restaurant-name"* and *"hotel-name"*. \
**For these slots, you also need to extract the corresponding values from Previous dialogue state.**

## Examples    
INPUT: 
> Previous conversation
Human: Hi, I am currently planning to come to Cambridge, and I was looking for a relatively inexpensive place to eat in the centre. What would you suggest?
Assistant: The Gardenia is an excellent and cheap place in the center of town, serving Mediterranean cuisine. Would you like a table there?
Human: Yes, please book a table for 1 people at 19:15 on monday.
Assistant: Booking was successful. The table will be reserved for 15 minutes. Reference number is: IU63HAEN. Is there anything else I can help you with today?

> Previous dialogue state:
{
    "restaurant": {
        "book": {
            "booked": [
                {
                    "name": "The Gardenia",
                    "reference": "IU63HAEN"
                }
            ],
            "people": "1",
            "day": "monday",
            "time": "19:15"
        },
        "semi": {
            "food": "not mentioned",
            "pricerange": "cheap",
            "name": "The Gardenia",
            "area": "centre"
        }
    }
}
 
> Current user input: 
Human: Yes. I need a place to stay in the same part of town. It must have free parking.

OUTPUT:
Active domains: ["hotel"]
Dialogue state:
{
    "hotel": {
        "book": {
            "booked": [],
            "people": "",
            "day": "",
            "stay": ""
        },
        "semi": {
            "name": "not mentioned",
            "area": "centre",
            "parking": "yes",
            "pricerange": "not mentioned",
            "stars": "not mentioned",
            "internet": "not mentioned",
            "type": "not mentioned"
        }
    }
}

## Output format you must follow:
Active domains: ["domain"]
Dialogue state:
{
    "domain": {
        "book" {
            "booked": []
            "slot1": "value1"
        },
        "semi": {
            "slot2": "value2"
            "slot3": "value3"
        }
    }
}

INPUT:
> Previous conversiontion:
{history}

> Previous dialogue state:
{state}

> Current user input: 
Human: {input}

OUTPUT:
"""


CACHE_PROMPT = """\
As an intelligent conversational agent, your task is to assess whether new information needs to be retrieved using the query tool. You will base your decision on the following criteria:

Determine if the User Input requires new information not currently available in the cache.

# Several special scenarios where no query is needed:
1. No need to retrieve when the user requests a booking reference number.
2. No need to retrieve when the user provides booking information, such as day, time, people, stay.

## Example
User: please book a table for 1 people at 19:15 on monday.
NeedNewQuery: No

User: I need rooms for 7 people for 2 nights starting Monday.
NeedNewQuery: No

User: If that time isn't available, I could also do 16:15.
NeedNewQuery: No

User: Yes, can I get 6 tickets please and I 'll need the reference number too.
NeedNewQuery: No


INPUT
Conversation history
{history}

User Input
Human: {input}

Query Cache
{query_cache}

## OUTPUT format
NeedNewQuery: Yes/No
"""

# Quwey
SQL_PROMPT = """\
# Generate SQL According to the Dialogue State

Based on the active domians、the current dialogue state and the user input, generate the appropriate SQL queries to retrieve the necessary \
information from the database. Ensure that the queries are efficient and accurately reflect the user's requests.

Here are some rules:
1. The SQL SELECT command must be a one-line format.
2. Ensure the query retrieves the correct information based on the dialogue state.
3. Handle different domains such as hotel, restaurant, attraction, and train.
4. Only one table is allowed to appear in SQL command.
5. Use given related values for categorical columns instead of human's description.
6. Use * select all columns.
7. Remember you MUST use pattern match logic (LIKE) instead of equal condition (=) for column name, e.g. "name LIKE '%xxx%'".
8. Use  < and > for the columns arriveBy and leaveAt according to the context, e.g. "leaveAt > '20:00'"

Here are table information:
{table_info}

INPUT: 
Previous conversation
{history}

Active domains:
{active_domains}

Dialogue state:
{state}
 
Current user input: 
Human: {input}

SQL:
"""

Modify_SQL_PROMPT = """\
# Modify SQL According to the requirement.

Original SQL
{sql}

Requirement
{requirement}

SQL:
"""

# NoOfferRelevant
NoOfferRelevant_PROMPT = """\
# Objective
The user is looking for a specific item, but the exact match is not available in the database. Your task is to slightly modify the user's query conditions and provide related information that closely meet the user's core requirements.

User Input
Human: {input}

# Original SQL
{sql}

# Optional conditions that can be deleted.
{no_offer_options}

Now, select a condition to be deleted from the optional conditions list and regenerate the SQL statement. Output format:
Condition: [condition to be deleted must come from the optional list above]
SQL: [The output must be a one-line SQL SELECT command]
"""

NoOfferRelevant_RESPONSE_PROMPT = """\
# Objective
The user is looking for a specific item, but the exact match is not available in the database. So you slightly modified the user's query conditions and provided related information that closely meet the user's core requirements. \
Here are two actions to help you convey to users the unavailability of information and provide relevant information:
1. NoOffer: unavailability of information;
2. NoOfferRelevant: relevant information;

## OUTPUT format
Action: {"domain-NoOffer": {"slot1": "value1", "slot2": "value2"}, "domain-NoOfferRelevant": {"slot3": "value3", "slot4": "value4"}}
Assistant: [Generated response based on the action and related information]

## OUTPUT EXAMPLE1
Action: {"Restaurant-NoOffer": {"area": "centre"}, "Restaurant-NoOfferRelevant": {"food": "chinese"}}
Assistant: I am sorry. There are no restaurants which meet that criteria in the centre of town. Would you like me to search for Chinese food?

## OUTPUT EXAMPLE2
Action: {"Hotel-NoOffer": {"type": "guesthouses"}, "Hotel-NoOfferRelevant": {"type": "hotel"}}
Assistant: There are no guesthouses that meet that criteria, would you like information about the hotel options?

INPUT
Conversation history
{history}

User Input
Human: {input}

Original SQL
{o_sql}

New SQL
{n_sql}

Related Information based on New SQL
{query_cache}

OUTPUT
"""

# Inform
INFORM_PROMPT = """\
# Objective
Your primary function is to handle user queries and inform information by providing two distinct types of information responses: InformSpecific and InformAddition.
1. InformSpecific: Provide the explicit answer to the user's direct request or Provide booking reference (you can use "IU63HAEN" as a placeholder).
2. InformAddition: Provide additional, implicit information that could be helpful to the user but was not explicitly requested.

## Examples
Action: {"hotel-InformAddition: [{"type": "guesthouse", "choice": "2", "pricerange": "cheap"}, {"type": "hotels", "choice": "2", "pricerange": "expensive"}]"}
Assistant: We have two guesthouses and two hotels that meet your needs. The guesthouses are cheap, and the hotels are expensive.

Action: {"hotel-InformAddition": {"type": "guesthouse", "choice": "7", "pricerange": {"moderate": "6", "cheap": "1"}}}
Assistant: Yes, there are 7 guesthouses in the north that meet your needs. 6 are moderate and 1 is cheap.

Action: {"booking-InformSpecific": {"reference": "IU63HAEN"}}
Assistant: Booking was successful. The table will be reserved for 15 minutes. Reference number is: IU63HAEN.

Action: {"hotel-InformSpecific": {"phone": "01223327978", "name": "el shaddai"}}
Assistant: El Shaddai's phone number is 01223327978.

Action: {"taxi-InformSpecific": {"phone": "07371414690", "type": "red honda"}}
Assistant: Sure, I've booked a red honda for you. Its contact number is 07371414690.

Action: {"attraction-InformAddition": {"type": "nightclub", "choice": "6", "area": {"creter": "5", "south": "1"}}}
Assistant: There are 6 nightclubs located in Cambridge. 5 in the Centre and 1 in the South.

Action: {"restaurant-InformAddition": {"name": "Lock Fyne", "pricerange": "expensive", "food": "seafood", "address": "37 trumpington St"}}
Assistant: Lock Fyne is en expensive seafood restaurant located at 37 trumpington St.

Action: {"train-InformAddition": {"trainID": "TR2162", "departure": "kings lynn", "destination": "cambridge", "leaveAt": "14:11", "arriveBy": "14:58"}}
Assistant: The TR2162 departs from Kings Lynn at 14:11 and arrives at Cambridge at 14:58.

Human: I'd like to book for 3 people./I 'll need the reference number.
Action: {"booking-InformSpecific": {"reference": "IU63HAEN"}}
Assistant: Reference number is: IU63HAEN...

# Notice
1. When there are too many search results, do not provide detailed descriptions for each item, but instead give a statistical summary overview.
2. Do not output duplicated actions. Each type of action should appear at most once.
3. If a reference number is needed to inform, use the following action: {"booking-InformSpecific": {"reference", "IU63HAEN"}}.
4. When booking a taxi, users are informed of the phone number and car type: {"taxi-InformSpecific": {"phone": "07371414690", "type": "red honda"}}.

# Decision-Making Process (OUTPUT format you must follow)
Question: Based on the dialogue history, is it necessary to take Inform* action towards the user in the assistant response?
Thought: Yes or No. If yes, give Action; else give empty Action {}.
Action: {"domain-InformSpecific": {"slot1": "value1", "slot2": "value2"}, "domain-InformAddition": {"slot3": "value3", "slot4": "value4"}}
Final Response: Generated refined response based on the thought process

# Thought, Action and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active Domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

OUTPUT
Question: Based on the dialogue history, is it necessary to take Inform* action towards the user in the assistant response?
"""

# Request
REQUEST_PROMPT = """\
# Objective
Your primary function is to handle user queries and request by providing two distinct types of information responses: RequestSpecify and RequestSelect.
1. RequestSpecify: Check the conversation state to determine whether to ask the user for a specific preference or booking information.
2. RequestSelect: If there are a few options that meet the user's need in the query results, you can use this action to ask the user to make a selection.

# Requestable slots (Slots available for inquiry in each domain.)
booking: people, day, stay, time
hotel: area, parking, internet, pricerange, stars, type
restaurant: area, food, pricerange
attraction: area, type
train: destination, departure, leaveAt, arriveBy, day, people
taxi: destination, departure, leaveAt, arriveBy, leaveAt

# Notice
You can only inquire about slots under "booking" when the user agrees or requests a reservation.

## Examples
Assistant: There a 6 guesthouses in the east. Half of them are in the cheap range, and the other half moderate.
Supplementary Action: {"hotel-RequestSelect": {"none": "none"}}
Final Response: There a 6 guesthouses in the east. Half of them are in the cheap range, and the other half moderate. What is your preference?

Supplementary Action: {"hotel-RequestSpecify": {"area": "?", "type": "guesthouse"}}
Final Response: Do you want to stay in a specific area of town? And would you be fine staying at a guesthouse?

Supplementary Action: {"attraction-RequestSpecify": {"type": "?"}}
Final Response: Sure, what type of attractions are you interested in?

Assistant: It is expensive.
Supplementary Action: {"restauran-RequestSpecify": {"pricerange": "less expensive"}}
Final Response: It is expensive. Do you need something less expensive?

Assistant: I would be happy to book that for you.
Supplementary Action: {"booking-RequestSpecify": {"day": "?", "time": "?"}}
Final Response: I would be happy to book that for you. Which day would you like to dine and do you have a preferred time?


# OUTPUT format you must follow
Question: Based on the dialogue history, is it necessary to take new Request* action towards the user in the assistant response?
Thought: Yes or No. If yes, give Supplementary Action; else give empty Supplementary Action {}.
Supplementary Action: {"domain-RequestSpecify": {"slot1": "value1", "slot2": "value2"}}, "domain-RequestSelect": {"slot3": "value3", "slot4": "value4"}}
Final Response: Generate final Assistant Response, supplement the Assistant Response according to the requirements of Supplementary Action.

# Thought, Supplementary Action and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active Domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

Assistant Action
{action}

Assistant Response
Assistant: {response}

OUTPUT
Question: Based on the dialogue history, is it necessary to take Request* action towards the user in the assistant response?
"""

# CrossDomain
CROSSDOMAIN_PROMPT = """\
# Objective
You are an intelligent agent designed to enhance user interactions by determining whether to proactively ask cross-domain services (booking-RequestCrossDomain). 

## Example1
> Assistant Action: {"restaurant-InformAddition": {"name": "the gardenia", "pricerange": "cheap", "area": "centre", "food": "mediterranean"}}
> Assistant Response: The Gardenia is an excellent and cheap place in the center of town, serving Mediterranean cuisine.

Question: Based on the Assistant response and dialogue history, is it necessary to take booking-RequestCrossDomain action towards the user in the assistant response?
Thought: Yes.
Final Response: The Gardenia is an excellent and cheap place in the center of town, serving Mediterranean cuisine. Would you like a table there?

## Example2
> Assistant Action: {"train-InformAddition": {"trainId": "TR6539", "arriveBy": "20:08"}}
> Assistant Response: No problem, the TR6539 train should arrive by 20:08.

Question: Based on the Assistant response and dialogue history, is it necessary to take booking-RequestCrossDomain action towards the user in the assistant response?
Thought: Yes.
Final Response: The TR6539 train should arrive by 20:08. Would you like to make a booking?


# Decision-Making Process (OUTPUT format you must follow)
Question: Based on the Assistant response and dialogue history, is it necessary to take a booking-RequestCrossDomain action towards the user in the assistant response?
Thought: Yes or No. If detailed information about an item has already been provided to the user, booking-RequestCrossDomain can be used to offer additional services, such as booking a hotel/train, making a restaurant reservation.
Final Response: Generate final Assistant Response, supplement the Assistant Response with booking-RequestCrossDomain action.

# Thought and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

Assistant Action
{action}

Assistant Response
{response}

OUTPUT
Question: Based on the Assistant response and dialogue history, is it necessary to take booking-RequestCrossDomain action towards the user in the assistant response?
"""

# Verify
VERIFY_PROMPT = """\
# Objective
Your main function is to control the RequestVerify action to enhance Assistant Response. The following situations require you to perform the RequestVerify action:

1. Cross-Domain Similar Field Copy: When copying similar fields across different domains, seek confirmation to avoid errors. Example:
Human: I am organizing my trip to cambridge and need a place to stay in the east in the cheap price range.
...
Human: I also need a train going to stevenage.
Assistant: Okay! What day would you like to travel?
Supplementary Action: {"train-RequestVerify": {"departure": "Cambridge"}}
Final Response: Okay! What day would you like to travel? I'm presuming you're coming from Cambridge?

2. Incomplete Inquiries: When a request appears incomplete, prompt the user for the missing information. Example:
Assistant: I have 3 great places that serve turkish food in the centre of town. I have 2 that are moderately priced and 1 that is expensive. Do you have a preference?
Human: I need it on Friday, for 6, at 12:15.
Action: {"restaurant-RequestVerify": {"pricerange": "?"}}
Final Response: I would happily book the restaurant but I need you to respond to my previous inquiry about your price preference.

3. Ambiguous Requests: When the request is unclear or can be interpreted in multiple ways, ask for clarification. Example:
Human: Tell me about the ones in the west. And can I get the address for Thanh Binh?
Assistant: The address for Thanh Binh is 17 Magdalene Street City Centre.
Supplementary Action: {"restaurant-RequestVerify": {"name": "Thanh Binh"}}
Final Response: The address for Thanh Binh is 17 Magdalene Street City Centre. Is it the Thanh Binh you are looking for?

4. General Verification. Example:
Human: Yes and I'm also looking for a train from norwich on tuesday going to cambridge arriving by 19:15.
Assistant: I have a train xxx.
Supplementary Action: {"train-RequestVerify": {"none": "none"}}
Final Response: I have a train xxx. Will this work for you?

# Decision-Making Process (OUTPUT format you must follow)
Question: Is the current dialogue history in line with any of the situations above?
Thought: Yes or No. If yes, give Supplementary Action; else give empty Supplementary Action {}.
Supplementary Action: {"domain-RequestVerify": {"slot1": "value1"}}
Final Response: Generate final Assistant Response, supplement the Assistant Response according to the requirements of Supplementary Action.

# Thought, Supplementary Action and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

Assistant Action
{action}

Assistant Response
{response}

OUTPUT
Question: Is the current dialogue history in line with any of the situations above?
"""

GENERAL_NO_REQ_PROMPT = """\
Your main function is to control the 'general' acts to enhance Assistant Response.

'general' domain acts:
1. welcome: Acknowledge and greet the user at the beginning of the interaction.
2. bye: End the interaction and say goodbye to the user.
3. greet: Acknowledge the user in a friendly manner.
4. thank: Express gratitude towards the user for their input or cooperation.

# Decision-Making Process (OUTPUT format you must follow)
Question: Is the 'general' domain acts needed in current conversation?
Thought: Yes or No. If yes, give Supplementary Action; else give empty Supplementary Action {}.
Supplementary Action: {"general-Act1": {"none": "none"}, "general-Act2": {"none": "none"}}
Final Response: Generate final Assistant Response, supplement the Assistant Response according to the requirements of Supplementary Action.

# Thought, Supplementary Action and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

Assistant Action
{action}

Assistant Response
{response}

OUTPUT
Question: Is the 'general' domain acts needed in current conversation?
"""

# General
GENERAL_PROMPT = """\
Your main function is to control the 'general' acts to enhance Assistant Response.

'general' domain acts:
1. reqmore: request whether the user needs more help or assistance when completing a booking in the current domain.
2. welcome: Acknowledge and greet the user at the beginning of the interaction.
3. bye: End the interaction and say goodbye to the user.
4. greet: Acknowledge the user in a friendly manner.
5. thank: Express gratitude towards the user for their input or cooperation.

# Decision-Making Process (OUTPUT format)
Question: Is the 'general' domain acts needed in current conversation?
Thought: Yes or No. If yes, give Supplementary Action; else give empty Supplementary Action {}.
Supplementary Action: {"general-Act1": {"none": "none"}, "general-Act2": {"none": "none"}}
Final Response: Generate final Assistant Response, supplement the Assistant Response according to the requirements of Supplementary Action.

# Thought, Supplementary Action and Final Response must appear in OUTPUT.

INPUT
Dialogue history
{history}

Active domains
{active_domains}

Dialogue state
{state}

Query cache
{query_cache}

User input
Human: {input}

Assistant Action
{action}

Assistant Response
{response}

OUTPUT
Question: Is the 'general' domain acts needed in current conversation?
"""


RESPONSE_PROMPT = """\
# Objective
Your task is to decide on the best course of action based on the current dialogue state, dialogue history. Use the information tracked to determine the most appropriate action and generate a appropriate response.

## System dialog acts as follows: 
Domain-dependent acts:
1.RequestSelect: ask to select between certain choices
2.RequestSpecify: ask broadly to narrow down quickly
3.RequestVerify: clarify for an ambiguous request
4.RequestCrossDomain: offer cross-domain service
5.InformSpecific: provide answer asked explicitly
6.InformAddition: provide implicit answer not requested
7.NoOfferRelevant: provide relevant alternative choices

'general' domain acts:
1.reqmore: request whether the user needs more help or assistance when completing a booking in the current domain
2.welcome: acknowledge and greet the user at the beginning of the interaction
3.bye: end the interaction and say goodbye to the user
4.greet: acknowledge the user in a friendly manner
5.thank: express gratitude towards the user for their input or cooperation

There are 6 domains ('booking', 'restaurant', 'hotel', 'attraction', 'taxi', 'train') and 1 dummy domain ('general').
A domain-dependent dialogue act is defined as a domain token followed by a domain-independent dialogue act, e.g. 'hotel-InformSpecific' means it is an 'InformSpecific' act in the Hotel domain.
Dialogue acts which cannot take slots, e.g., 'bye', are defined under the 'general' domain.
If a dialogue act takes no slots, e.g., dialogue act 'RequestCrossDomain' for an utterance 'would you like to take a reservation?', its slot-value pair is ['none', 'none']
There are Three types of values:
1) If a slot takes a binary value, e.g., 'internet' or 'parking', the value is either 'yes' or 'no'.
2) If a slot is under the act 'RequestSpecify', e.g., 'RequestSpecify' about 'area', the value is expressed as '?'.
3) The value that appears in the utterance e.g., the name of a restaurant.

# OUTPUT format
Action:  {"domain1-act1": {"slot1": "value1", "slot2": "value2"}, "domain2-act2": {"slot3": "value3", "slot4": "value4"}}
Assistant: [Generated response based on the actions]

## OUTPUT Examples
Action: {"attraction-InformAddition": {"type": "nightclub", "choice": "6", "area": {"creter": "5", "south": "1"}}}
Assistant: There are 6 nightclubs located in Cambridge. 5 in the Centre and 1 in the South.

Action: {"booking-InformSpecific": {"reference": "IU63HAEN"}}
Assistant: Booking was successful. The table will be reserved for 15 minutes. Reference number is: IU63HAEN.

Action: {"taxi-InformSpecific": {"phone": "07371414690", "type": "red honda"}}
Assistant: Sure, I've booked a red honda for you. Its contact number is 07371414690.

Action: {"hotel-InformAddition": {"choice": "many different"}, "hotel-RequestSpecify": {"area": "?"}}
Assistant: We have many different hotels. Is there a particular part of town you would like to stay in?

Action: {"train-InformAddition": {"trainID": "TR8882", "departure": "Leicester", "destination": "Cambridge", "arriveBy": "13:54", "leaveAt": "12:09"}, "booking-RequestCrossDomain": {"none": "none"}}
Assistant: TR8882 departs Leicester at 12:09 and arrives in Cambridge by 13:54, would you like to book a seat?

Action: {"train-RequestSpecify": {"day": "?", "departure": "?"}, "train-RequestVerify": {"departure": "Cambridge"}}
Assistant: Okay! What day would you like to travel? I'm presuming you're coming from Cambridge?


INPUT:
> Dialogue history
{history}

> Active domains
{active_domains}

> Dialogue state
{state}

> Query cache
{query_cache}

> User input
Human: {input}

# Instruction
1. Ensure actions are reasonable and avoid conflicts
2. Ensure not more than one questions in your response.
3. Generate concise and appropriate responses based on the selected dialogue actions.

OUTPUT:
"""
