PASSIVE_STAGE = """\
Your task is to decide on the best course of action based on the current dialogue state, dialogue history. Use the information tracked to determine the most appropriate action and generate a appropriate response.

# Basic system dialog actions
Actions need to take slots:
1.NoOffer: inform the user of the situation and the reason when their needs cannot be met;
2.InformSpecific: provide the explicit answer to the user's direct request or booking details;
3.RequestSpecify: ask the user for specific information, such as reservation details or requirements.

Actions cannot take slots:
1.welcome: acknowledge the user at the beginning of the interaction;
2.bye: end the interaction and say goodbye to the user;
3.greet: greet the user in a friendly manner;
4.thank: express gratitude towards the user for their input or cooperation;

There are Three types of values:
1) If a slot takes a binary value, e.g., 'internet' or 'parking', the value is either 'yes' or 'no'.
2) If a slot is under the act 'RequestSpecify', e.g., 'RequestSpecify' about 'area', the value is expressed as '?'.
3) The value that appears in the utterance e.g., the name of a restaurant.

# Instruction
1. Ensure actions are reasonable and avoid conflicts
2. Ensure not more than one questions in your response.
3. Generate concise and appropriate responses based on the selected dialogue actions.

# Examples
{example}
> Dialogue history
{history}
> Active domains
{active_domains}
> Dialogue state
{state}
> Knowledge retrieval observation
{query_cache}
> User input
Human: {input}
Use the format to output:
###
Question: What basic actions should I take to respond to the user?
Thought: Beacuse..., I have to...
Action: {"domain1-act1": {"slot1": "value1", "slot2": "value2"}, "domain2-act2": {"slot3": "value3", "slot4": "value4"}}
Response: [Generated response based on the actions]
###
"""

PROACTIVE_STAGE = """\
Your task is to choose appropriate proactive actions to supplement the Assistant's response.

## Proactive dialog actions as follows:
1.InformAddition: provide additional, implicit information that could be helpful to the user but was not explicitly requested;
2.OfferRelevant: provide relevant information to the user when their needs cannot be met;
3.RequestSelect: ask the user to make a selection if there are several options that meet the user's need;
4.RequestSpecify: ask the user for a specific preference or booking information;
5.RequestVerify: ask clarification question when copying similar slot across different domains or the user's request is unclear;
6.RequestCrossDomain: offer cross-domain services that might suit the user when current goal is completed.
7.reqmore: ask if further assistance is needed.

There are Three types of values:
1) If a slot takes a binary value, e.g., 'internet' or 'parking', the value is either 'yes' or 'no'.
2) If a slot is under the act 'RequestSpecify', e.g., 'RequestSpecify' about 'area', the value is expressed as '?'.
3) The value that appears in the utterance e.g., the name of a restaurant.

# Instruction
1. Ensure actions are reasonable and avoid conflicts
2. Ensure not more than one questions in your response.
3. Generate concise and appropriate responses based on the selected dialogue actions.

## Examples
{examples}
> Dialogue history
{history}
> Active domains
{active_domains}
> Dialogue state
{state}
> Knowledge retrieval observation
{query_cache}
> User input
User: {input}
> Assistant response
Assistant: {response}

Use the format to output:
###
Question: Is it still necessary to supplement additional proactive actions to the existing response?
Thought: Yes or No. If yes, analyze which action would be helpful from the perspectives of information quality and user experience.
Action: {"domain1-act1": {"slot1": "value1", "slot2": "value2"}}
Response: [Generate final Assistant Response]
###
"""