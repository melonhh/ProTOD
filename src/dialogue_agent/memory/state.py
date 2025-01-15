
import json
import re
import copy
from loguru import logger

from src.prompt import DST_PROMPT, SQL_PROMPT, NoOfferRelevant_PROMPT, INFORM_PROMPT, REQUEST_PROMPT, CROSSDOMAIN_PROMPT, VERIFY_PROMPT, GENERAL_PROMPT, RESPONSE_PROMPT, CACHE_PROMPT, Modify_SQL_PROMPT, NoOfferRelevant_RESPONSE_PROMPT, GENERAL_NO_REQ_PROMPT
from src.utils import AICall, format_prompt


class ConversationState:
    """
    """
    def __init__(self, llm_engine=None, **kwargs) -> None:
        if llm_engine:
            self.llm_engine = llm_engine
        else:
            self.llm_engine = AICall(**kwargs)
        self.dst_prompt = DST_PROMPT
        self.sql_prompt = SQL_PROMPT
        self.no_offer_prompt = NoOfferRelevant_PROMPT
        self.no_offer_response_prompt = NoOfferRelevant_RESPONSE_PROMPT
        self.inform_prompt = INFORM_PROMPT
        self.request_prompt = REQUEST_PROMPT
        self.crossdomain_prompt = CROSSDOMAIN_PROMPT
        self.verify_prompt = VERIFY_PROMPT
        self.general_prompt = GENERAL_PROMPT
        self.general_no_req_prompt = GENERAL_NO_REQ_PROMPT
        self.response_prompt = RESPONSE_PROMPT
        self.cache_prompt = CACHE_PROMPT
        self.modify_sql_prompt = Modify_SQL_PROMPT
        self.domains = ['taxi', 'restaurant', 'hotel', 'attraction', 'train']
        self.query_domains = ['restaurant', 'hotel', 'attraction', 'train']
        self.active_domains = []
        self.state = {}
        self.no_offer_options = {
            'restaurant': ['food', 'area', 'pricerange'],
            'hotel': ['area', 'type', 'star', 'pricerange'],
            'attraction': ['area', 'type'],
            'train': ['leaveAt', 'arriveBy', 'day']
        }
        self.query_cache = None
        self.process_history = []
    
    def no_offer_relevant(self, prompt_map: dict, original_sql: str, tried_slots: list, domain) -> str:
        prompt_dict = copy.deepcopy(prompt_map)
        sql_active_domains = [domain]
        sql_state = {}
        sql_state[domain] = self.state[domain]['semi']
        
        prompt_dict['no_offer_options'] = {}
        prompt_dict['no_offer_options'][domain] = []
        for key in self.no_offer_options[domain]:
            if key in tried_slots:
                continue
            if key in sql_state[domain] and (sql_state[domain][key] == '' or sql_state[domain][key] == 'not mentioned' or sql_state[domain][key] == 'dont care'):
                continue
            prompt_dict['no_offer_options'][domain].append(key)

        prompt_dict['active_domains'] = str(sql_active_domains)
        prompt_dict['state'] = json.dumps(sql_state)
        prompt_dict['sql'] = original_sql
        
        # select key
        prompt = format_prompt(prompt_dict, self.no_offer_prompt)
        result = self.llm_engine.call(
            user_prompt=prompt,
            temperature=0.0
        )
        
        self.process_history.append({
            'function': "NoOfferRelevant_Key_Select",
            'process': prompt,
            'result': result
        })
        
        logger.debug(f'no_offer_relevant prompt: {prompt}')
        logger.debug(f'no_offer_relevant result: {result}')
        
        selected_key_re = re.findall(r'Condition:\s+(.*)\s*SQL', result)
        if len(selected_key_re) != 0:
            selected_key = selected_key_re[0].strip()
            selected_key = re.sub(r"'", '', selected_key)
            selected_key = re.sub(r"\[", '', selected_key)
            selected_key = re.sub(r"\]", '', selected_key)
        else:
            pass
        
        sql = ''
        if result.find('```sql') != -1:
            sql_match = re.findall(r'```sql(.*)```', result, re.DOTALL)
            if sql_match:
                sql = sql_match[0].strip()
        else:
            new_sql_re = re.findall(r'SQL:(.*)', result)
            if len(new_sql_re) != 0:
                sql = new_sql_re[0]
            sql = sql.strip()
        
        return sql, selected_key
        
        
    def no_offer_response(self, prompt_map: dict, o_sql: str, n_sql: str) -> str:
        new_prompt_map = copy.deepcopy(prompt_map)
        new_prompt_map['o_sql'] = o_sql
        new_prompt_map['n_sql'] = n_sql
        prompt = format_prompt(new_prompt_map, self.no_offer_response_prompt)
        action_response = self.llm_engine.call(
            user_prompt=prompt,
            temperature=0.0
        )
        self.process_history.append({
            'function': "NoOfferResponse",
            'prompt': prompt,
            'result': action_response
        })
        logger.debug(f'No_offer_response action result: \n{action_response}')
        return self.parse_action_response(action_response)
    
    def inform_response(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.inform_prompt)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        self.process_history.append({
            'function': 'InfromResponse',
            'prompt': prompt,
            'result': action_response
        })
        # logger.debug(f'Inform action prompt: \n{prompt}')
        logger.debug(f'Inform action result: \n{action_response}')
        return self.parse_reflect(action_response, 'Inform')
    
    def request_response(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.request_prompt)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        self.process_history.append({
            'function': 'RequestResponse',
            'prompt': prompt,
            'result': action_response
        })
        # logger.debug(f'Request action prompt: \n{prompt}')
        logger.debug(f'Request action result: \n{action_response}')
        return self.parse_reflect(action_response, 'Request')
    
    def crossdomain_response(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.crossdomain_prompt)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        self.process_history.append({
            'prompt': "CrossDomain",
            'result': action_response
        })
        logger.debug(f'CrossDomain action result: \n{action_response}')
        return self.parse_reflect(action_response, 'RequestCrossDomain')

    def verify_response(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.verify_prompt)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        self.process_history.append({
            'function': 'VerifyResponse',
            'prompt': prompt,
            'result': action_response
        })
        logger.debug(f'Verify action result: \n{action_response}')
        return self.parse_reflect(action_response, 'Verify')
    
    def general_response(self, prompt_map: dict, has_request) -> str:
        prompt_template = self.general_no_req_prompt if has_request else self.general_prompt
        prompt = format_prompt(prompt_map, prompt_template)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        self.process_history.append({
            'function': 'GeneralResponse',
            'prompt': prompt,
            'result': action_response
        })
        logger.debug(f'General action result: \n{action_response}')
        
        return self.parse_reflect(action_response, "general")
    
    def parse_reflect(self, reflect_response, act_type):
        
        reflect_response = reflect_response.replace('json', '')
        reflect_response = reflect_response.replace('```', '')
        
        thought_re = re.findall(r'Thought:\s*(.*)', reflect_response)
        if len(thought_re) != 0:
            thought = thought_re[-1]
            if 'No' in thought:
                return False, '', {}
        else:
            logger.error('Dialogue action parse Error')
            return False, '', {}
        
        response_pattern = re.compile(r'Response:\s*(.*)', re.DOTALL)
        response_match = response_pattern.search(reflect_response)
        response = response_match.group(1) if response_match else ''
        
        if act_type == 'RequestCrossDomain':
            if 'Yes' in thought:
                action = {'booking-RequestCrossDomain': [['none', 'none']]}
                return True, response, action
            else:
                action = {}
                return False, response, action
        else:
            if 'Yes' in thought:
                action_pattern = re.compile(r'Action:\s*(\{.*\})\s*.*Response', re.DOTALL)
                action_match = action_pattern.search(reflect_response)
                action_json = action_match.group(1) if action_match else {}
                parse_success = False
                limit = 3
                tries = 0
                while not parse_success and tries < limit:
                    try:
                        action = json.loads(action_json) if action_match else {}
                        parse_success = True
                    except json.decoder.JSONDecodeError as e:
                        logger.error('Result Parse Error')
                        action_json = self.correct_format(action_json)
                        
                    tries += 1
                
                return True, response, action
            else:
                action = {}
                return False, response, action
        
    
    def parse_action_response(self, action_response):
        action = ""
        response = ""
        
        action_response = action_response.replace('json', '')
        action_response = action_response.replace('```', '') 
        action_pattern = re.compile(r'Action:\s*(\{.*\})\s*Assistant', re.DOTALL)
        action_match = action_pattern.search(action_response)
        action_json = action_match.group(1) if action_match else {}
        
        parse_success = False
        limit = 3
        tries = 0
        while not parse_success and tries < limit:
            try:
                action = json.loads(action_json) if action_match else {}
                parse_success = True
            except json.decoder.JSONDecodeError as e:
                logger.error('DST Result Parse Error')
                action_json = self.correct_format(action_json)
                
            tries += 1
            
        response_pattern = re.compile(r'Assistant:\s*(.*)', re.DOTALL)
        response_match = response_pattern.search(action_response)
        response = response_match.group(1) if response_match else ''
        
        return response, action
    
    def response(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.response_prompt)
        action_response =  self.llm_engine.call(
            prompt,
            temperature=0.0
        )
        # logger.debug(f'Generate response prompt: \n{prompt}')
        logger.debug(f'Generate normal response result: \n{action_response}')
        
        self.process_history.append({
            'function': 'NormalResponse',
            'prompt': prompt,
            'result': action_response
        })
        return self.parse_action_response(action_response)
    
    def conclude_state(self, prompt_map: dict) -> str:
        prompt = format_prompt(prompt_map, self.dst_prompt)
        # logger.debug('DST Prompt: \n' + prompt)
        result =  self.llm_engine.call(
            user_prompt=prompt,
            temperature=0.0
        )
        self.process_history.append({
            'prompt': prompt,
            'output': result
        })
        return result
    
    def is_need_query(self, prompt_map: dict) -> bool:
        prompt = format_prompt(prompt_map, self.cache_prompt)
        need_new_query = self.llm_engine.call(
            user_prompt=prompt,
            temperature=0.0
        )
        result = False
        if 'Yes' in need_new_query:
            result = True
        
        self.process_history.append({
            'prompt': prompt,
            'result': result
        })
        
        return result
        

    def generate_sql(self, prompt_map: dict) -> list[str]:
        prompt_dict = copy.deepcopy(prompt_map)
        
        res = {}
        for d in self.active_domains:
            if d in self.query_domains:
                sql_active_domains = []
                sql_state = {}
                sql_active_domains.append(d)
                sql_state[d] = copy.deepcopy(self.state[d]['semi'])
                
                # sql_state[d].pop('day', None)
                # sql_state[d].pop('people', None)
                # sql_state[d].pop('stay', None)
                # sql_state[d].pop('time', None)
                
                prompt_dict['active_domains'] = str(sql_active_domains)
                prompt_dict['state'] = json.dumps(sql_state)
        
                prompt = format_prompt(prompt_dict, self.sql_prompt)
                sql =  self.llm_engine.call(
                    user_prompt=prompt,
                    temperature=0.0
                )
        
                self.process_history.append({
                    'prompt': prompt,
                    'result': sql
                })
        
                # logger.debug(f'Generate SQL prompt: \n{prompt}')
                logger.debug(f'Generate SQL result: \n{sql}')
                if sql.find('```sql') != -1:
                    sql_match = re.findall(r'```sql(.*)```', sql, re.DOTALL)
                    if sql_match:
                        res[d] = sql_match[0].strip()
                    else:
                        pass
                else:
                    res[d] = sql.strip()
                
                
                def replace_quotes(match):
                    replace_quotes.count += 1
                    if replace_quotes.count % 2 == 0:
                        return "''"
                    return match.group(0)

                if res[d].count("'") == 3:
                    replace_quotes.count = 0
                    res[d] = re.sub(r"'", replace_quotes, res[d])
                    
        return res

    def correct_format(self, err_resp: str) -> str:
        prompt = "Your task is to correct the string to json format. The string to be corrected is {err_resp}. It can not be parsed by Python json.loads(). Now give the corrected json format string.".replace("{err_resp}", err_resp)
        logger.debug(f'Correct format: \n{prompt}')
        output =  self.llm_engine.call(
            user_prompt=prompt,
            sys_prompt="You are an assistent and good at writing json string. Do not use Markdown format.",
            temperature=0.0
        )
        json_pattern = re.compile(r'\s*(\{.+\})\s*', re.DOTALL)
        json_match = json_pattern.search(output)
        json_str = json_match.group(1) if json_match else output
        return json_str

    def update(self, prompt_map: dict):
        output: str = self.conclude_state(prompt_map)
        logger.debug('DST Prompt Output: \n' + output)
        active_domains_pattern = re.compile(r'Active domains:\s*(\[[^\]]+\])')
        active_domains_match = active_domains_pattern.search(output)
        active_domains = json.loads(active_domains_match.group(1)) if active_domains_match else []
        
        dialogue_state_pattern = re.compile(r'Dialogue state:\s*.*?(\{.*\})', re.DOTALL)
        dialogue_state_match = dialogue_state_pattern.search(output)
        dialogue_state_json = dialogue_state_match.group(1) if dialogue_state_match else '{}'
        # dialogue_state_json = dialogue_state_json.replace('json', '')
        # dialogue_state_json = dialogue_state_json.replace('```', '')
        
        # format parse
        parse_success = False
        limit = 3
        tries = 0
        while not parse_success and tries < limit:
            try:
                dialogue_state = json.loads(dialogue_state_json) if dialogue_state_match else {}
                parse_success = True
            except json.decoder.JSONDecodeError as e:
                dialogue_state_json = self.correct_format(dialogue_state_json)
                
            tries += 1

        # contend parse TODO
        
        if parse_success:
            self.active_domains = active_domains
            
            for domain in dialogue_state:
                for domain_type in dialogue_state[domain]:
                    for key in dialogue_state[domain][domain_type]:
                        if isinstance(dialogue_state[domain][domain_type][key], str):
                            # temp = dialogue_state[domain][domain_type][key].lower()
                            # temp = temp.replace("'", '')
                            dialogue_state[domain][domain_type][key] = dialogue_state[domain][domain_type][key].lower()
                            
                if domain not in self.state:
                    self.state[domain] = dialogue_state[domain]
                else:
                    for domain_type in dialogue_state[domain]:
                        if domain_type not in self.state[domain]:
                            self.state[domain][domain_type] = dialogue_state[domain][domain_type]
                        else:
                            self.state[domain][domain_type].update(dialogue_state[domain][domain_type])
                
            logger.debug(f"DST parse result: \nActive_domians: {self.get_active_domains()} \nDialogue state: {self.get_state()}")

    
    def get_active_domains(self):
        return str(self.active_domains)

    def get_state(self):
        return json.dumps(self.state)
    

    def clear(self):
        self.active_domains = []
        self.state = {}
        