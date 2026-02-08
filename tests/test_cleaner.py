"""Tests for vox.cleaner — code-aware text cleaning."""

from vox.cleaner import clean


class TestFillerRemoval:
    def test_removes_um_uh(self):
        assert clean("um so the function uh returns") == "So the function returns"

    def test_removes_multi_word_fillers(self):
        assert clean("you know the API is broken") == "The API is broken"

    def test_keeps_like_after_keeper(self):
        assert "like" in clean("it looks like a bug").lower()

    def test_removes_like_as_filler(self):
        result = clean("so like the function like returns none")
        assert result.count("like") == 0

    def test_empty_input(self):
        assert clean("") == ""
        assert clean("   ") == ""


class TestCodeKeywords:
    def test_capitalizes_none(self):
        assert "None" in clean("it returns none")

    def test_capitalizes_true_false(self):
        result = clean("set it to true or false")
        assert "True" in result
        assert "False" in result

    def test_preserves_surrounding_text(self):
        result = clean("check if the value is none then return")
        assert "None" in result
        assert "return" in result


class TestTechTerms:
    def test_capitalizes_api(self):
        assert "API" in clean("the api is down")

    def test_capitalizes_json(self):
        assert "JSON" in clean("parse the json response")

    def test_capitalizes_python(self):
        assert "Python" in clean("write it in python")

    def test_capitalizes_github(self):
        assert "GitHub" in clean("push to github")


class TestCasingCommands:
    def test_snake_case(self):
        result = clean("define snake case my variable name.")
        assert "my_variable_name" in result

    def test_camel_case(self):
        result = clean("call camel case get user data.")
        assert "getUserData" in result

    def test_pascal_case(self):
        result = clean("pascal case user service")
        assert "UserService" in result

    def test_kebab_case(self):
        result = clean("use kebab case my component.")
        assert "my-component" in result

    def test_all_caps(self):
        result = clean("all caps max retries")
        assert "MAX_RETRIES" in result


class TestFormatCommands:
    def test_new_line(self):
        result = clean("first line new line second line")
        assert "\n" in result

    def test_period(self):
        result = clean("end of sentence period")
        assert "." in result

    def test_open_close_paren(self):
        result = clean("call open paren close paren")
        assert "(" in result
        assert ")" in result

    def test_arrow(self):
        result = clean("returns arrow string")
        assert "->" in result


class TestWhitespace:
    def test_collapses_spaces(self):
        assert "  " not in clean("too   many   spaces   here")

    def test_strips_leading_trailing(self):
        result = clean("  hello world  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestCapitalizeFirst:
    def test_first_letter_capitalized(self):
        result = clean("the function works")
        assert result[0] == "T"
