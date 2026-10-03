"""Unit tests that need no model and no network: python3 -m unittest"""
import json
import unittest
from datetime import date

from solicitation_analyzer import dates
from solicitation_analyzer.analyze import Analysis, Document, apply_amendments, check_dates, key_facts, merge, verify
from solicitation_analyzer.extract import chunk_pages, to_item
from solicitation_analyzer.llm import Anthropic, Cached, OpenAICompatible, parse_json
from solicitation_analyzer.pdf import Page, split_pages
from solicitation_analyzer.redact import redact
from solicitation_analyzer.report import to_html, to_json, to_markdown
from solicitation_analyzer.schema import ITEM_SCHEMA, KINDS, Item
from solicitation_analyzer.scoring import score, score_fact
from solicitation_analyzer.textmatch import locate

PAGE_2 = """All responses should be submitted electronically in PDF format and emailed to the points of contact:
Pat Doe at pat_doe@example.gov. The subject line of the email should read as follows
"RFI: 140G0326Q0223 - ShakeAlert Production System Code Review."

Respondents must submit capability statements and information describing the general approach/solu-
tion to addressing the listed requirements."""


def item(**kw) -> Item:
    base = dict(kind="required_content", statement="s", quote="q", page=1, cited_page=1, document="d")
    base.update(kw)
    return Item(**base)


class Pdf(unittest.TestCase):
    def test_form_feeds_split_pages_and_drop_the_trailing_one(self):
        pages = split_pages("one\ftwo\fthree\f")
        self.assertEqual([p.number for p in pages], [1, 2, 3])
        self.assertEqual(pages[2].text, "three")

    def test_chunks_keep_page_markers_and_respect_the_budget(self):
        pages = [Page(i, "x" * 4000) for i in range(1, 6)]
        chunks = chunk_pages(pages, max_chars=9000)
        self.assertEqual([c.pages for c in chunks], [[1, 2], [3, 4], [5]])
        self.assertIn("<<<PAGE 3>>>", chunks[1].text)


class QuoteVerification(unittest.TestCase):
    pages = {1: "Nothing relevant here at all.", 2: PAGE_2}

    def test_exact_quote_across_a_line_break(self):
        m = locate("emailed to the points of contact: Pat Doe at pat_doe@example.gov.", self.pages, 2)
        self.assertEqual((m.status, m.page), ("exact", 2))

    def test_hyphenated_line_break_still_matches(self):
        m = locate("describing the general approach/solution to addressing the listed requirements", self.pages, 2)
        self.assertEqual(m.status, "exact")

    def test_wrong_page_is_corrected(self):
        m = locate("submitted electronically in PDF format and emailed", self.pages, 1)
        self.assertEqual((m.status, m.page), ("exact", 2))

    def test_one_dropped_word_is_a_close_match(self):
        m = locate("All responses should be submitted electronically in PDF format and emailed to points of contact", self.pages, 2)
        self.assertEqual(m.status, "fuzzy")
        self.assertGreaterEqual(m.similarity, 0.9)

    def test_table_cells_read_across_are_an_assembled_match(self):
        table = "Provide software        Updates, patches, and          100% of eligible\nupdates and             manufacturer-released          releases provided\nupgrades                upgrades are made available"
        m = locate("Provide software updates, patches, and upgrades are made available", {10: table}, 10)
        self.assertEqual((m.status, m.page), ("assembled", 10))

    def test_scattered_words_far_apart_are_still_missing(self):
        page = "Proposals are reviewed. " + "filler words here " * 40 + "Ten copies of the pages are limited to staff use."
        m = locate("Proposals are limited to ten pages of staff copies", {1: page}, 1)
        self.assertEqual(m.status, "missing")

    def test_invented_text_is_missing(self):
        m = locate("Responses are limited to ten pages in 12-point Arial font", self.pages, 2)
        self.assertEqual(m.status, "missing")

    def test_quote_across_a_page_break_and_its_footer(self):
        pages = {7: "Describe the firm's experience. Include the names, titles\n\n                5\n", 8: "and phone numbers of at least three (3) references excluding ESD employees."}
        m = locate("Include the names, titles and phone numbers of at least three (3) references", pages, 7)
        self.assertEqual((m.status, m.page, m.end_page), ("exact", 7, 8))

    def test_two_column_page_verifies_against_reading_order(self):
        layout = "the Contractor either (a) has no business        project, and has retained the\noperations in Northern Ireland, or (b) shall take    documentation of these efforts"
        reading = "the Contractor either (a) has no business operations in Northern Ireland, or (b) shall take lawful steps"
        doc = Document(path=None, id="d", title="t", pages=[Page(34, layout, reading)])
        kept, _ = verify([item(quote="has no business operations in Northern Ireland, or (b) shall take", cited_page=34)], doc)
        self.assertEqual(kept[0].verification, "exact")

    def test_verify_rejects_invented_items_and_fixes_pages(self):
        doc = Document(path=None, id="d", title="t", pages=[Page(1, self.pages[1]), Page(2, PAGE_2)])
        good = item(quote="Respondents must submit capability statements", cited_page=1, page=1)
        bad = item(quote="Proposals are limited to five pages and must use Arial")
        kept, rejected = verify([good, bad], doc)
        self.assertEqual(kept, [good])
        self.assertEqual(rejected, [bad])
        self.assertEqual(good.page, 2)
        self.assertTrue(any("page 2" in w for w in good.warnings))


class Dates(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(dates.find_dates("by October 16, 2026"), [date(2026, 10, 16)])
        self.assertEqual(dates.find_dates("10 OCT 2026 @ 13:00"), [date(2026, 10, 10)])
        self.assertEqual(dates.find_dates("no later than 12/23/2025"), [date(2025, 12, 23)])
        self.assertEqual(dates.find_dates("Questions 7/8/26"), [date(2026, 7, 8)])
        self.assertEqual(dates.find_dates("Sept. 4, 2026"), [date(2026, 9, 4)])

    def test_struck_through_revision_yields_both_dates(self):
        self.assertEqual(dates.find_dates("2:00 PM ET on August 7 13, 2026"), [date(2026, 8, 7), date(2026, 8, 13)])

    def test_times(self):
        self.assertEqual(dates.find_times("at 12:00pm PST"), ["12:00"])
        self.assertEqual(dates.find_times("5:00 pm CST"), ["17:00"])
        self.assertEqual(dates.find_times("10 OCT 2026 @ 13:00 EST"), ["13:00"])
        self.assertEqual(dates.find_times("2:00 PM ET"), ["14:00"])
        self.assertEqual(dates.find_times("10/26/2026 1700 CD"), ["17:00"])

    def test_check_dates_flags_a_date_not_in_the_quote(self):
        i = item(kind="response_due", quote="Proposals are due October 16, 2026", date="2026-10-17")
        check_dates(i)
        self.assertTrue(any("does not contain the date" in w for w in i.warnings))

    def test_check_dates_flags_amendment_strikethrough(self):
        i = item(kind="response_due", quote="Submission of Proposals (date and time) 8/7/26 8/13/26", date="2026-08-13")
        check_dates(i)
        self.assertTrue(any("struck through" in w for w in i.warnings))


class MergeAndAmend(unittest.TestCase):
    def test_undated_response_deadlines_become_other_deadlines(self):
        from solicitation_analyzer.analyze import reclassify

        q = item(kind="response_due", statement="Submit questions via online form by 12/23/2025.", date="2025-12-23")
        p = item(kind="response_due", statement="Proposals are due August 13; questions are answered by July 28.", date="2026-08-13")
        reclassify([q, p])
        self.assertEqual((q.kind, p.kind), ("questions_due", "response_due"))
        late = item(kind="response_due", statement="Late proposals will not be considered")
        due = item(kind="response_due", date="2026-08-13")
        reclassify([late, due])
        self.assertEqual((late.kind, due.kind), ("other_deadline", "response_due"))

    def test_repeats_fold_into_the_first_page(self):
        a = item(statement="Submit in PDF format", quote="All responses should be submitted electronically in PDF format", page=2)
        b = item(statement="Submit in PDF format.", quote="responses should be submitted electronically in PDF format", page=5)
        merged = merge([b, a])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0].page, merged[0].also_on), (2, [5]))

    def test_an_amendment_restating_the_base_keeps_the_amendment_version(self):
        base = item(statement="Font no smaller than 10 point", quote="Font size for all document and proposal files must be no smaller than Times New Roman size 10", document="rfp", role="base", page=4)
        amd = item(statement="Font no smaller than 10 point", quote="Font size for all document and proposal files must be no smaller than Times New Roman size 10", document="amd2", role="amendment", page=5)
        merged = merge([base, amd])
        self.assertEqual([(m.document, m.page) for m in merged], [("amd2", 5)])

    def test_alike_lines_with_different_quotes_stay_apart(self):
        a = item(statement="Include SAM UEI number in the submission", quote="3. SAM UEI number.", page=2)
        b = item(statement="Include GSA contract number in the submission", quote="4. GSA contract number, if applicable.", page=2)
        self.assertEqual(len(merge([a, b])), 2)

    def test_different_dates_are_not_merged(self):
        a = item(kind="response_due", statement="Proposals due", quote="Proposals due 8/7/26", date="2026-08-07")
        b = item(kind="response_due", statement="Proposals due", quote="Proposals due 8/7/26", date="2026-08-13")
        self.assertEqual(len(merge([a, b])), 2)

    def test_amendment_deadline_supersedes_the_base(self):
        base = item(kind="response_due", date="2026-08-07", document="rfp", role="base")
        amd = item(kind="response_due", date="2026-08-13", document="add2", role="amendment")
        apply_amendments([base, amd])
        self.assertEqual(base.superseded_by, "add2")
        self.assertIsNone(amd.superseded_by)
        analysis = Analysis("t", [], [base, amd], [], [], "m", "p", 1.0, "2026-10-03")
        self.assertEqual(key_facts(analysis)["response_due"].date, "2026-08-13")


    def test_set_aside_and_naics_lines_are_recognized(self):
        from solicitation_analyzer.analyze import reclassify

        sa = item(statement="Solicitation is set aside for 100% Service-Disabled Veteran-Owned Small Business.")
        na = item(statement="Associated NAICS code is 541519 with a $34.0 million size standard.")
        cover = item(statement="Cover page must include Business Size under required NAICS.")
        reclassify([sa, na, cover])
        self.assertEqual((sa.kind, na.kind, cover.kind), ("set_aside", "naics", "required_content"))

    def test_key_facts_prefer_the_proposal_channel_and_the_award_rule(self):
        items = [
            item(kind="submission_method", statement="Debriefing requests are submitted through the online form.", quote="request for debriefing through the online form"),
            item(kind="response_due", statement="Submit bids electronically via online form by January 13, 2026.", quote="submit their bids electronically", date="2026-01-13"),
            item(kind="basis_of_award", statement="Technical Evaluation is 70% of the final score.", quote="The Technical Evaluation is 70%"),
            item(kind="basis_of_award", statement="Award goes to the highest aggregate score.", quote="awarded to the vendor whose aggregate technical and cost score is the highest"),
        ]
        facts = key_facts(Analysis("t", [], items, [], [], "m", "p", 1.0, "x"))
        self.assertIn("bids electronically", facts["submission_method"].statement)
        self.assertIn("highest", facts["basis_of_award"].statement)


class Model(unittest.TestCase):
    def test_parse_json_tolerates_fences_and_prose(self):
        self.assertEqual(parse_json('Sure:\n```json\n{"items": []}\n```'), {"items": []})

    def test_to_item_rejects_unknown_kinds_and_empty_quotes(self):
        self.assertIsNone(to_item({"kind": "vibes", "quote": "x"}, "d", "base"))
        self.assertIsNone(to_item({"kind": "page_limit", "quote": ""}, "d", "base"))
        self.assertEqual(to_item({"kind": "page_limit", "quote": "30 pages", "page": 4}, "d", "base").page, 4)

    def test_schema_enumerates_every_kind(self):
        self.assertEqual(ITEM_SCHEMA["properties"]["items"]["items"]["properties"]["kind"]["enum"], KINDS)

    def test_request_bodies(self):
        body = OpenAICompatible("m").request_body("sys", "user", ITEM_SCHEMA, 100)
        self.assertEqual(body["response_format"]["json_schema"]["schema"], ITEM_SCHEMA)
        self.assertEqual(body["temperature"], 0)
        a = Anthropic("claude-x").request_body("sys", "user", ITEM_SCHEMA, 100)
        self.assertEqual(a["tool_choice"], {"type": "tool", "name": "record_items"})

    def test_an_overflowing_chunk_is_retried_page_by_page(self):
        from solicitation_analyzer.extract import extract_items
        from solicitation_analyzer.llm import TooLong

        class Fake:
            name, model = "fake", "fake-1"
            budgets = []

            def complete_json(self, system, user, schema, max_tokens):
                Fake.budgets.append(max_tokens)
                if "Pages 1 to 2" in user:
                    raise TooLong("too long")
                page = int(user.split("Pages ")[1].split(" ")[0])
                return {"items": [{"kind": "page_limit", "statement": "s", "quote": f"quote {page}", "page": page, "date": "", "time": "", "weight": ""}]}

        pages = [Page(1, "a" * 100), Page(2, "b" * 100)]
        items, errors = extract_items(Fake(), pages, "d", "t", max_tokens=1000)
        self.assertEqual(([i.page for i in items], errors), ([1, 2], []))
        self.assertEqual(Fake.budgets, [1000, 2000, 2000])

    def test_cache_returns_the_stored_reply_without_calling(self):
        import tempfile

        class Fake:
            name, model, calls = "fake", "fake-1", 0

            def complete_json(self, *a):
                Fake.calls += 1
                return {"items": [Fake.calls]}

        with tempfile.TemporaryDirectory() as d:
            cached = Cached(Fake(), d)
            self.assertEqual(cached.complete_json("s", "u", {}, 1), {"items": [1]})
            self.assertEqual(cached.complete_json("s", "u", {}, 1), {"items": [1]})
            self.assertEqual(Fake.calls, 1)


class Output(unittest.TestCase):
    def test_redaction(self):
        self.assertEqual(redact("email Pat at pat.doe@usgs.gov or call (703) 555-0100"), "email Pat at [email] or call [phone]")
        self.assertEqual(redact("Primary Contact: Pat Doe"), "Primary Contact: [name]")
        self.assertEqual(redact("to the Contract Manager (CM), Sam Roe at sam.roe.3@us.af.mil AND"), "to the Contract Manager (CM), [name] at [email] AND")
        self.assertEqual(redact("emailed to the points of contact: Pat Doe at pat_doe@example.gov."), "emailed to the points of contact: [name] at [email].")
        self.assertEqual(redact("Submit capability statements and the general approach"), "Submit capability statements and the general approach")

    def test_names_from_contact_lines_and_emails_are_removed_everywhere(self):
        from solicitation_analyzer.redact import contact_names

        pages = ["Attn: Pat Quill, Contract Specialist\nEmail: Sam.Roe@example.gov"]
        names = contact_names(pages)
        self.assertEqual(names, {"Pat Quill", "Sam Roe"})
        self.assertEqual(redact("OFFER DUE DATE/LOCAL TIME SAM ROE 10/26/2026", names), "OFFER DUE DATE/LOCAL TIME [name] 10/26/2026")

    def test_reports_escape_document_text(self):
        doc = Document(path=None, id="d", title="RFP <script>", pages=[Page(1, "x")])
        i = item(statement="Use <b>bold</b>", quote="a & b", verification="exact")
        data = to_json(Analysis("RFP <script>", [doc], [i], [], [], "m", "p", 1.0, "2026-10-03T00:00:00+00:00"))
        page = to_html(data)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", page)
        self.assertIn("- [ ] Use <b>bold</b>", to_markdown(data))
        json.dumps(data)


class Scoring(unittest.TestCase):
    def test_not_stated_is_right_only_when_left_out(self):
        self.assertTrue(score_fact(None, None)["correct"])
        self.assertFalse(score_fact(None, {"statement": "x", "quote": "y"})["correct"])

    def test_dates_and_times(self):
        s = score_fact({"date": "2026-10-10", "time": "13:00"}, {"statement": "", "quote": "", "date": "2026-10-10", "time": "15:00"})
        self.assertTrue(s["correct"])
        self.assertFalse(s["time_correct"])

    def test_checklist_needs_every_group_in_one_item(self):
        gold = {"facts": {}, "evaluation_factors": [], "checklist": [{"id": "f", "text": "", "all": [["font"], ["10"]]}]}
        report = {"key_facts": {}, "items": [{"statement": "Font size 10", "quote": ""}]}
        self.assertEqual(score(gold, report)["checklist_found"], 1)
        report = {"key_facts": {}, "items": [{"statement": "Font", "quote": ""}, {"statement": "10 copies", "quote": ""}]}
        self.assertEqual(score(gold, report)["checklist_found"], 0)


if __name__ == "__main__":
    unittest.main()
