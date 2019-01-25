from subprocess import CalledProcessError
from unittest import mock
from unittest.mock import call

from nephos.helpers.misc import (
    execute,
    execute_until_success,
    input_data,
    input_files,
    get_response,
    pretty_print,
)


class TestExecute:
    @mock.patch("nephos.helpers.misc.check_output")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute(self, mock_print, mock_check_output):
        execute("ls")
        mock_print.assert_called_once()
        mock_print.assert_called_with("ls")
        mock_check_output.assert_called_once()
        mock_check_output.assert_called_with("ls", shell=True, stderr=-2)

    @mock.patch("nephos.helpers.misc.check_output")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute_quiet(self, mock_print, mock_check_output):
        execute("ls", show_command=False)
        mock_print.assert_not_called()
        mock_check_output.assert_called_once()
        mock_check_output.assert_called_with("ls", shell=True, stderr=-2)

    @mock.patch("nephos.helpers.misc.check_output")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute_verbose(self, mock_print, mock_check_output):
        # Add some side effects
        mock_check_output.side_effect = ["output".encode("ascii")]
        execute("ls", verbose=True)
        # First check_output
        mock_check_output.assert_called_once()
        mock_check_output.assert_called_with("ls", shell=True, stderr=-2)
        # Then print
        mock_print.assert_has_calls([call("ls"), call("output")])

    @mock.patch("nephos.helpers.misc.check_output")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute_error(self, mock_print, mock_check_output):
        # Add some side effects
        mock_check_output.side_effect = CalledProcessError(
            cmd="lst",
            returncode=127,
            output="/bin/sh: lst: command not found".encode("ascii"),
        )
        execute("lst")
        # First check_output
        mock_check_output.assert_called_once()
        mock_check_output.assert_called_with("lst", shell=True, stderr=-2)
        # Then print
        mock_print.assert_has_calls(
            [
                call("lst"),
                call("Command failed with CalledProcessError:"),
                call("/bin/sh: lst: command not found"),
            ]
        )

    @mock.patch("nephos.helpers.misc.check_output")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute_error_quiet(self, mock_print, mock_check_output):
        # Add some side effects
        mock_check_output.side_effect = CalledProcessError(
            cmd="lst",
            returncode=127,
            output="/bin/sh: lst: command not found".encode("ascii"),
        )
        execute("lst", show_command=False, show_errors=False)
        # First check_output
        mock_check_output.assert_called_once()
        mock_check_output.assert_called_with("lst", shell=True, stderr=-2)
        # Then print
        mock_print.assert_not_called()


class TestExecuteUntilSuccess:
    @mock.patch("nephos.helpers.misc.execute")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute(self, mock_print, mock_execute):
        mock_execute.side_effect = [
            (None, "error"),
            (None, "error"),
            ("<h1>SomeWebsite</h1>", None),
        ]
        execute_until_success("curl example.com", delay=0)
        mock_print.assert_has_calls([call(".", end="", flush=True)] * 2)
        mock_execute.assert_has_calls(
            [
                call(
                    "curl example.com",
                    show_command=True,
                    show_errors=True,
                    verbose=False,
                )
            ]
            + [
                call(
                    "curl example.com",
                    show_command=False,
                    show_errors=False,
                    verbose=False,
                )
            ]
            * 2
        )

    @mock.patch("nephos.helpers.misc.execute")
    @mock.patch("nephos.helpers.misc.print")
    def test_execute_verbose(self, mock_print, mock_execute):
        mock_execute.side_effect = [
            (None, "error"),
            (None, "error"),
            ("<h1>SomeWebsite</h1>", None),
        ]
        execute_until_success("curl example.com", verbose=True, delay=0)
        mock_print.assert_has_calls(
            [call(".", end="", flush=True)] * 2 + [call("<h1>SomeWebsite</h1>")]
        )
        mock_execute.assert_has_calls(
            [
                call(
                    "curl example.com",
                    show_command=True,
                    show_errors=True,
                    verbose=True,
                )
            ]
            + [
                call(
                    "curl example.com",
                    show_command=False,
                    show_errors=False,
                    verbose=False,
                )
            ]
            * 2
        )


class TestInputData:
    @mock.patch("nephos.helpers.misc.get_response")
    def test_input_data(self, mock_get_response):
        input_data(("hello",))
        mock_get_response.assert_called_with("Input hello")

    @mock.patch("nephos.helpers.misc.get_response")
    def test_input_data_suffix(self, mock_get_response):
        input_data(("hello",), text_append="big")
        mock_get_response.assert_called_with("Input hello big")

    @mock.patch("nephos.helpers.misc.get_response")
    def test_input_data_multiple(self, mock_get_response):
        input_data(("hello", ("goodbye", {"sensitive": True})))
        mock_get_response.assert_has_calls(
            [call("Input hello"), call("Input goodbye", sensitive=True)]
        )


class TestInputFiles:
    files = ["./some_folder/some_file&.txt", "./another_file.txt"]

    @mock.patch("nephos.helpers.misc.open")
    @mock.patch("nephos.helpers.misc.isfile")
    @mock.patch("nephos.helpers.misc.get_response")
    @mock.patch("nephos.helpers.misc.print")
    def test_input_files(self, mock_print, mock_get_response, mock_isfile, mock_open):
        mock_isfile.side_effect = [True]
        mock_get_response.side_effect = [self.files[0]]
        data = input_files(("hello",))
        mock_print.assert_not_called()
        mock_get_response.assert_called_with("Input hello")
        mock_isfile.assert_called_with(self.files[0])
        mock_open.assert_called_with(self.files[0], "rb")
        assert data.keys() == {"hello"}

    @mock.patch("nephos.helpers.misc.open")
    @mock.patch("nephos.helpers.misc.isfile")
    @mock.patch("nephos.helpers.misc.get_response")
    @mock.patch("nephos.helpers.misc.print")
    def test_input_files_suffix(
        self, mock_print, mock_get_response, mock_isfile, mock_open
    ):
        mock_isfile.side_effect = [True]
        mock_get_response.side_effect = [self.files[0]]
        data = input_files(("hello",), text_append="big")
        mock_print.assert_not_called()
        mock_get_response.assert_called_with("Input hello big")
        mock_isfile.assert_called_with(self.files[0])
        mock_open.assert_called_with(self.files[0], "rb")
        assert data.keys() == {"hello"}

    @mock.patch("nephos.helpers.misc.open")
    @mock.patch("nephos.helpers.misc.isfile")
    @mock.patch("nephos.helpers.misc.get_response")
    @mock.patch("nephos.helpers.misc.print")
    def test_input_files_multiple(
        self, mock_print, mock_get_response, mock_isfile, mock_open
    ):
        mock_isfile.side_effect = [True, True]
        mock_get_response.side_effect = self.files
        data = input_files(("hello", "goodbye"))
        mock_print.assert_not_called()
        mock_get_response.assert_has_calls([call("Input hello"), call("Input goodbye")])
        mock_isfile.assert_has_calls([call(self.files[0]), call(self.files[1])])
        mock_open.assert_any_call(self.files[0], "rb")
        mock_open.assert_any_call(self.files[1], "rb")
        assert data.keys() == {"hello", "goodbye"}

    @mock.patch("nephos.helpers.misc.open")
    @mock.patch("nephos.helpers.misc.isfile")
    @mock.patch("nephos.helpers.misc.get_response")
    @mock.patch("nephos.helpers.misc.print")
    def test_input_files_mistake(
        self, mock_print, mock_get_response, mock_isfile, mock_open
    ):
        mock_isfile.side_effect = [False, True]
        mock_get_response.side_effect = [self.files[0] + "OOPS", self.files[0]]
        data = input_files(("hello",))
        mock_print.assert_called_once_with(
            "{} is not a file".format(self.files[0] + "OOPS")
        )
        mock_get_response.assert_has_calls([call("Input hello"), call("Input hello")])
        mock_isfile.assert_has_calls(
            [call(self.files[0] + "OOPS"), call(self.files[0])]
        )
        mock_open.assert_called_with(self.files[0], "rb")
        assert data.keys() == {"hello"}

    @mock.patch("nephos.helpers.misc.open")
    @mock.patch("nephos.helpers.misc.isfile")
    @mock.patch("nephos.helpers.misc.get_response")
    @mock.patch("nephos.helpers.misc.print")
    def test_input_files_cleankey(
        self, mock_print, mock_get_response, mock_isfile, mock_open
    ):
        mock_isfile.side_effect = [True]
        mock_get_response.side_effect = [self.files[0]]
        data = input_files((None,), clean_key=True)
        mock_print.assert_called_once_with(
            "Replaced some_file&.txt with some_file_.txt"
        )
        mock_get_response.assert_called_with("Input None")
        mock_isfile.assert_called_with(self.files[0])
        mock_open.assert_called_with(self.files[0], "rb")
        assert data.keys() == {"some_file_.txt"}


class TestGetResponse:
    @mock.patch("nephos.helpers.misc.input")
    @mock.patch("nephos.helpers.misc.print")
    def test_get_response(self, mock_print, mock_input):
        mock_input.side_effect = ["An answer"]
        answer = get_response("A question")
        mock_input.assert_called_once()
        mock_print.assert_called_with("A question")
        assert answer == "An answer"

    @mock.patch("nephos.helpers.misc.getpass")
    @mock.patch("nephos.helpers.misc.input")
    @mock.patch("nephos.helpers.misc.print")
    def test_get_response_password(self, mock_print, mock_input, mock_getpass):
        mock_getpass.side_effect = ["A password"]
        answer = get_response("A question", sensitive=True)
        mock_input.assert_not_called()
        mock_print.assert_called_with("A question")
        mock_getpass.assert_called_once_with("Password:")
        assert answer == "A password"

    @mock.patch("nephos.helpers.misc.input")
    @mock.patch("nephos.helpers.misc.print")
    def test_get_response_options(self, mock_print, mock_input):
        mock_input.side_effect = ["mistake", "y"]
        get_response("A question", ("y", "n"))
        mock_input.assert_has_calls([call()] * 2)
        mock_print.assert_has_calls(
            [
                call("A question"),
                call("Permitted responses: ('y', 'n')"),
                call("Invalid response, try again!"),
            ]
        )


class TestPrettyPrint:
    @mock.patch("nephos.helpers.misc.print")
    def test_pretty_print(self, mock_print):
        pretty_print('{"some": "json"}')
        mock_print.assert_called_with(
            '{\x1b[34;01m"some"\x1b[39;49;00m: \x1b[33m"json"\x1b[39;49;00m}\n'
        )
