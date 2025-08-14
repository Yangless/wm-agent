import re


action.action_typev= “ActionType.ATTACK_CITY”
condition.required_action_types=[<ActionType.ATTACK_CITY: 'attack_city'>]
if action.action_type in condition.required_action_types:
                    required_types_found.append(action.action_type.value)

print(required_types_found)
