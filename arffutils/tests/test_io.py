from io import StringIO

from nose.tools import assert_raises
import nose
import os.path

from arffutils.io import io_handler


data_path = os.path.join(os.path.dirname(__file__), "data", "io")
test_input_file = os.path.join(data_path, "test_input.txt")
test_output_file = os.path.join(data_path, "test_output.txt")

test_input_str = u"abcd"
test_output_str = u"xyz"


class TestIO():
    def test_read_stringio(self):
        f = StringIO(test_input_str)
        with io_handler(f) as fh:
            x = fh.read()
        assert x == test_input_str

    def test_write_stringio(self):
        f = StringIO()
        with io_handler(f, "w") as fh:
            fh.write(test_input_str)
        assert fh.getvalue() == test_input_str
        assert not fh.closed

    def test_read_file(self):
        f = test_input_file
        with io_handler(f) as fh:
            x = fh.read()
        assert x == test_input_str

    def test_write_file(self):
        f = test_output_file
        with io_handler(f, "w") as fh:
            fh.write(test_output_str)
        with open(test_output_file) as f:
            x = f.read()
            assert x == test_output_str

    def test_read_file_handle(self):
        f = open(test_input_file)
        with io_handler(f) as fh:
            assert f == fh
            x = fh.read()
        f.close()
        assert x == test_input_str

    def test_write_file_handle(self):
        f = open(test_output_file, "w")
        with io_handler(f) as fh:
            assert f == fh
            fh.write(test_output_str)
        f.close()
        with open(test_output_file) as f:
            x = f.read()
            assert x == test_output_str

if __name__ == '__main__':
    nose.main()
