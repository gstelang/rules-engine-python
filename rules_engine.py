from dataclasses import dataclass
from enum import Enum, auto
from pickle import TRUE
from typing import List, Optional
import re
import sqlite3

class ConditionType(Enum):
    IS = auto()
    IS_NOT = auto()
    MATCHES = auto()
    NOT_MATCHES = auto()
    # For SQL rules - the rule is considered to be matched if the query returns one or more rows.
    SQL = auto()

class FieldType(Enum):
    SUBJECT = auto
    BODY = auto()
    REPLY = auto()
    DOMAIN = auto()
    NONE = auto()

@dataclass
class Email:
    subject: str
    body: str
    from_email: str
    reply_to: str
    domain: str
    company_domain: str


@dataclass(kw_only=True)
class ScoredEmail(Email):
    score: float


@dataclass
class Condition:
    condition_type: ConditionType
    value: str
    field_type: FieldType

@dataclass
class Rule:
    """The rule that should be matched against the emails that
    are scored high enough.
    
    All rules may have multiple conditions that should be evaluated together.
    All conditions need to be evaluated in conjunction.
    If you need disjunction - split your rule into multiple rules.
    """
    name: str
    min_score: float
    conditions: List[Condition]


class RuleEngine:
    def __init__(self, rules: List[Rule], database_location: Optional[str] = None):
        self.rules = rules
        self.con = None
        # TODO: connect once
        if database_location:
            self.con = sqlite3.connect(database_location)
    
    def evaluate_scored_email(self, email: ScoredEmail) -> List[str]:
        matched_rules = []
        for rule in self.rules:
            if email.score > rule.min_score:
                for condition in rule.conditions:
                    value = condition.value
                    is_matched = False
                    match condition.field_type:
                        case FieldType.SUBJECT:
                            is_matched = self.evaluate_subject(email, value, condition.condition_type)
                        case FieldType.BODY:
                            is_matched = self.evaluate_body(email, value, condition.condition_type)
                        case FieldType.REPLY:
                            is_matched = self.evaluate_reply_to(email, value, condition.condition_type)
                        case FieldType.DOMAIN: 
                            is_matched = self.evaluate_domain(email, value, condition.condition_type)
                        case FieldType.NONE:
                            if condition.condition_type == ConditionType.SQL:
                                is_matched = self.evaluate_sql(email, value)
                        case _:
                            raise RuntimeError(
                                "Encountered an unknown field type"
                            )
                    if is_matched:
                        matched_rules.append(rule.name)        
        return matched_rules

    def evaluate_sql(self, email, value) -> bool:
        if not self.con:
            raise RuntimeError("SQL conditions are not supported for this rules engine")
        if not value.lower().startswith("select"):
            raise RuntimeError("Only select statements are supported for SQL conditions")
        return len(self.con.execute(self.format_email(email, value)).fetchall()) > 0

    def evaluate_subject(self, email, value, type: ConditionType) -> bool:
        if type == ConditionType.IS:
            return email.subject == self.format_email(email, value)
        if type == ConditionType.IS_NOT:
            return email.subject != self.format_email(email, value)
        if type == ConditionType.MATCHES:
            return re.match(value, email.subject) != None
        if type == ConditionType.NOT_MATCHES:
            return re.match(value, email.subject) == None

    def evaluate_body(self, email, value, type: ConditionType) -> bool:
        if type == ConditionType.IS:
            return email.body == self.format_email(email, value)
        if type == ConditionType.IS_NOT:
            return email.body != self.format_email(email, value)
        if type == ConditionType.MATCHES:
            return re.match(value, email.body) != None
        if type == ConditionType.NOT_MATCHES:
            return not re.match(value, email.body) == None

    def evaluate_domain(self, email, value, type: ConditionType) -> bool:
        if type == ConditionType.IS:
            return email.domain == self.format_email(email, value)
        if type == ConditionType.IS_NOT:
            return email.domain != self.format_email(email, value)
        if type == ConditionType.MATCHES:
            return re.match(value, email.domain) != None
        if type == ConditionType.NOT_MATCHES:
            return not re.match(value, email.domain) == None

    def evaluate_reply_to(self, email, value, type: ConditionType) -> bool:
        if type == ConditionType.IS:
            return email.reply_to == self.format_email(email, value)
        if type == ConditionType.IS_NOT:
            return email.reply_to != self.format_email(email, value)
        if type == ConditionType.MATCHES:
            return re.match(value, email.reply_to) != None
        if type == ConditionType.NOT_MATCHES:
            return not re.match(value, email.reply_to) == None

    def format_email(self, email, value) -> str:
        return value.format(email=email)
    