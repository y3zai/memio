from memio.exceptions import MemioError, NotSupportedError, ProviderError


class TestMemioError:
    def test_is_exception(self):
        assert issubclass(MemioError, Exception)

    def test_message(self):
        e = MemioError("something broke")
        assert str(e) == "something broke"


class TestProviderError:
    def test_inherits_memio_error(self):
        assert issubclass(ProviderError, MemioError)

    def test_attributes(self):
        cause = ValueError("bad input")
        e = ProviderError(provider="mem0", operation="add", cause=cause)
        assert e.provider == "mem0"
        assert e.operation == "add"
        assert e.cause is cause

    def test_message_format(self):
        cause = RuntimeError("timeout")
        e = ProviderError(provider="zep", operation="search", cause=cause)
        assert "[zep] search failed: timeout" == str(e)

    def test_can_be_caught_as_memio_error(self):
        cause = RuntimeError("fail")
        e = ProviderError(provider="mem0", operation="add", cause=cause)
        try:
            raise e
        except MemioError as caught:
            assert caught is e


class TestNotSupportedError:
    def test_inherits_provider_error(self):
        assert issubclass(NotSupportedError, ProviderError)

    def test_attributes(self):
        e = NotSupportedError(provider="zep", operation="delete")
        assert e.provider == "zep"
        assert e.operation == "delete"
        assert isinstance(e.cause, NotImplementedError)

    def test_message_format(self):
        e = NotSupportedError(provider="mem0", operation="delete")
        assert "mem0" in str(e)
        assert "delete" in str(e)

    def test_can_be_caught_as_provider_error(self):
        e = NotSupportedError(provider="zep", operation="delete")
        try:
            raise e
        except ProviderError as caught:
            assert caught is e
