import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import unittest
import rules_engine


RuleAlwaysMatch = rules_engine.Rule(
    name="Always Match",
    min_score=0,
    conditions=[
        rules_engine.Condition(
            field_type=rules_engine.FieldType.SUBJECT,
            condition_type=rules_engine.ConditionType.MATCHES,
            value=".*",
        )
    ]
)


RuleNeverMatch = rules_engine.Rule(
    name="Never Match",
    min_score=0,
    conditions=[
        rules_engine.Condition(
            field_type=rules_engine.FieldType.SUBJECT,
            condition_type=rules_engine.ConditionType.MATCHES,
            value="aaaaaaaaaaaomg"
        )
    ]
)


AlwaysMatchRulesEngine = rules_engine.RuleEngine(
    rules=[RuleAlwaysMatch]
)

NeverMatchRulesEngine = rules_engine.RuleEngine(
    rules=[RuleNeverMatch]
)

CompareFieldsRulesEngine = rules_engine.RuleEngine(
    rules=[
        RuleNeverMatch,
        RuleAlwaysMatch,
        rules_engine.Rule(
            name="From and reply to emails are different",
            min_score=0,
            conditions=[
                rules_engine.Condition(
                    field_type=rules_engine.FieldType.REPLY,
                    condition_type=rules_engine.ConditionType.IS_NOT,
                    value="{email.from_email}"
                )
            ]
        ),
        rules_engine.Rule(
            name="Domain is not company domain",
            min_score=0,
            conditions=[
                rules_engine.Condition(
                    field_type=rules_engine.FieldType.DOMAIN,
                    condition_type=rules_engine.ConditionType.IS_NOT,
                    value="{email.company_domain}"
                )
            ]
        ),
    ]
)

DBRulesEngine = rules_engine.RuleEngine(
    rules=[
        rules_engine.Rule(
            name="SQL: Subject contains known bad pattern",
            min_score=0,
            conditions=[
                rules_engine.Condition(
                    condition_type=rules_engine.ConditionType.SQL,
                    value=(
                        "select 1 from bad_values "
                        "where instr(lower('{email.subject}'), lower(value)) > 0 "
                        "and type = 'subject'"
                    ),
                    field_type=rules_engine.FieldType.NONE
                )  
            ]
        )
    ],
    database_location="rules_db.sqlite"
)


class TestingRulesEngineMain(unittest.TestCase):
    def test_always_match(self):
        result = AlwaysMatchRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my dear friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="hacker@email.com",
                reply_to="hacker@email.com",
                domain="email.com",
                company_domain="abnormalsecurity.com",
                score=1
            )
        )
        self.assertEqual(result, ["Always Match"])
    
    def test_never_match(self):
        result = NeverMatchRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my dear friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="hacker@email.com",
                reply_to="hacker@email.com",
                domain="email.com",
                company_domain="abnormalsecurity.com",
                score=1
            )
        )
        self.assertEqual(result, [])
    
    def test_from_reply_to_different(self):
        result = CompareFieldsRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my dear friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="ceo@abnormalsecurity.com",
                reply_to="hacker@email.com",
                domain="abnormalsecurity.com",
                company_domain="abnormalsecurity.com",
                score=0.6
            )
        )
        self.assertEqual(result, [
            "Always Match",
            "From and reply to emails are different"
        ])
    
    def test_from_not_company_domain(self):
        result = CompareFieldsRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my dear friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="ceo@normalsecurity.com",
                reply_to="ceo@normalsecurity.com",
                domain="normalsecurity.com",
                company_domain="abnormalsecurity.com",
                score=0.8
            )
        )
        self.assertEqual(result, [
            "Always Match",
            "Domain is not company domain"
        ])
    
    def test_db_rule_match(self):
        result = DBRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my dear friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="ceo@abnormalsecurity.com",
                reply_to="ceo@abnormalsecurity.com",
                domain="abnormalsecurity.com",
                company_domain="abnormalsecurity.com",
                score=0.8
            )
        )
        self.assertEqual(result, [
            "SQL: Subject contains known bad pattern"
        ])
    
    def test_db_rule_match_not(self):
        result = DBRulesEngine.evaluate_scored_email(
            email=rules_engine.ScoredEmail(
                subject="Hello my weird friend",
                body="I wish you a wonderful day and need a lot of money.",
                from_email="ceo@abnormalsecurity.com",
                reply_to="ceo@abnormalsecurity.com",
                domain="abnormalsecurity.com",
                company_domain="abnormalsecurity.com",
                score=0.8
            )
        )
        self.assertEqual(result, [])


class TestingRulesEngineCustom(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(1)
