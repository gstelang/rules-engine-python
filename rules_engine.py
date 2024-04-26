from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
import re
import sqlite3


class ConditionType(Enum):
    SUBJECT_IS = auto()
    SUBJECT_IS_NOT = auto()
    SUBJECT_MATCHES = auto()
    SUBJECT_NOT_MATCHES = auto()
    BODY_IS = auto()
    BODY_IS_NOT = auto()
    BODY_MATCHES = auto()
    BODY_NOT_MATCHES = auto()
    REPLY_TO_IS = auto()
    REPLY_TO_IS_NOT = auto()
    REPLY_TO_MATCHES = auto()
    REPLY_TO_NOT_MATCHES = auto()
    DOMAIN_IS = auto()
    DOMAIN_IS_NOT = auto()
    DOMAIN_MATCHES = auto()
    DOMAIN_NOT_MATCHES = auto()
    # For SQL rules - the rule is considered to be matched if the query returns one or more rows.
    SQL = auto()


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
        if database_location:
            self.con = sqlite3.connect(database_location)
    
    def evaluate_scored_email(self, email: ScoredEmail) -> List[str]:
        matched_rules = []
        for rule in self.rules:
            if email.score > rule.min_score:
                for condition in rule.conditions:
                    match [condition.condition_type, condition.value]:
                        case [ConditionType.SUBJECT_IS, value]:
                            if email.subject == value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.SUBJECT_MATCHES, value]:
                            if re.match(value, email.subject):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.SUBJECT_IS_NOT, value]:
                            if email.subject != value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.SUBJECT_NOT_MATCHES, value]:
                            if not re.match(value, email.subject):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.BODY_IS, value]:
                            if email.body == value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.BODY_MATCHES, value]:
                            if re.match(value, email.body):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.BODY_IS_NOT, value]:
                            if email.body != value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.BODY_NOT_MATCHES, value]:
                            if not re.match(value, email.body):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.REPLY_TO_IS, value]:
                            if email.reply_to == value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.REPLY_TO_MATCHES, value]:
                            if re.match(value, email.reply_to):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.REPLY_TO_IS_NOT, value]:
                            if email.reply_to != value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.REPLY_TO_NOT_MATCHES, value]:
                            if not re.match(value, email.reply_to):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.DOMAIN_IS, value]:
                            if email.domain == value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.DOMAIN_MATCHES, value]:
                            if re.match(value, email.domain):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.DOMAIN_IS_NOT, value]:
                            if email.domain != value.format(email=email):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.DOMAIN_NOT_MATCHES, value]:
                            if not re.match(value, email.domain):
                                matched_rules.append(rule.name)
                            continue
                        case [ConditionType.SQL, value]:
                            if not self.con:
                                raise RuntimeError("SQL conditions are not supported for this rules engine")
                            if not value.lower().startswith("select"):
                                raise RuntimeError("Only select statements are supported for SQL conditions")
                            if len(self.con.execute(value.format(email=email)).fetchall()) > 0:
                                matched_rules.append(rule.name)
                            continue
                        case _:
                            raise RuntimeError(
                                "Encountered an unknown condition type"
                            )
        return matched_rules