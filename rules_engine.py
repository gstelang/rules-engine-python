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
    SUBJECT = "subject"
    BODY = "body"
    REPLY = "reply_to"
    DOMAIN = "domain"
    NONE = "none"

@dataclass
class Email:
    subject: str
    body: str
    from_email: str
    reply_to: str
    domain: str
    company_domain: str

    def __getitem__(self, item):
        return getattr(self, item)

@dataclass(kw_only=True)
class ScoredEmail(Email):
    score: float

    def __getitem__(self, item):
        return getattr(self, item)

@dataclass
class Condition:
    condition_type: ConditionType
    value: str
    field_type: str

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

class RuleEvaluator:
    def evaluate(self, email, condition):
        pass
    def format_email(self, email, value) -> str:
        return value.format(email=email)
    
class MatchRuleEvaluator(RuleEvaluator):
    def evaluate(self, email, condition):
        if condition.condition_type == ConditionType.IS:
            return email[condition.field_type.value] == self.format_email(email, condition.value)
        if condition.condition_type == ConditionType.IS_NOT:
            return email[condition.field_type.value] != self.format_email(email, condition.value)

class RegexRuleEvaluator(RuleEvaluator):
    def evaluate(self, email, condition):
        if condition.condition_type == ConditionType.MATCHES:
            return re.match(condition.value, email[condition.field_type.value]) != None
        if condition.condition_type == ConditionType.NOT_MATCHES:
            return re.match(condition.value, email[condition.field_type.value]) == None

class SQLRuleEvaluator(RuleEvaluator):
    def __init__(self, con):
        self.con = con

    def evaluate(self, email, condition):
        if not condition.value.lower().startswith("select"):
            raise RuntimeError("Only select statements are supported for SQL conditions")
        return len(self.con.execute(self.format_email(email, condition.value)).fetchall()) > 0

class RuleEngine:
    def __init__(self, rules: List[Rule], database_location: Optional[str] = None):
        self.rules = rules
        self.con = None
        if database_location:
            self.con = sqlite3.connect(database_location)
    
    def evaluate_scored_email(self, email: ScoredEmail) -> List[str]:
        matched_rules = []
        for rule in self.rules:
            if email.score > rule.min_score:
                for condition in rule.conditions:
                    evaluator = {
                        ConditionType.IS: MatchRuleEvaluator(),
                        ConditionType.IS_NOT: MatchRuleEvaluator(),
                        ConditionType.MATCHES: RegexRuleEvaluator(),
                        ConditionType.NOT_MATCHES: RegexRuleEvaluator(),
                        ConditionType.SQL: SQLRuleEvaluator(self.con)
                    }[condition.condition_type]
                    is_matched = evaluator.evaluate(email, condition)
                    if is_matched:
                        matched_rules.append(rule.name)        
        return matched_rules