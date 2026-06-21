from ollamarama.handlers.router import Router


def test_router_dispatch_ai():
    r = Router()
    called = {}

    async def h(ctx, room, sender, display, args):
        called["ok"] = (room, sender, display, args)

    r.register(".ai", h)
    fn, args = r.dispatch(object(), "!r", "@u", "User", ".ai hello world", False, bot_name="Bot")
    assert fn is h
    assert args[-1] == "hello world"


def test_router_dispatch_botname():
    r = Router()
    async def h(ctx, room, sender, display, args):
        pass
    r.register(".ai", h)
    fn, args = r.dispatch(object(), "!r", "@u", "User", "Bot: hi", False, bot_name="Bot")
    assert fn is h
    assert args[-1] == "hi"


def test_router_dispatch_multiword_botname():
    r = Router()
    async def h(ctx, room, sender, display, args):
        pass
    r.register(".ai", h)
    fn, args = r.dispatch(object(), "!r", "@u", "User", "Ollama Rama: hello there", False, bot_name="Ollama Rama")
    assert fn is h
    assert args[-1] == "hello there"


def test_router_dispatch_botname_bare_mention():
    r = Router()
    async def h(ctx, room, sender, display, args):
        pass
    r.register(".ai", h)
    fn, args = r.dispatch(object(), "!r", "@u", "User", "Ollama Rama:", False, bot_name="Ollama Rama")
    assert fn is h
    assert args[-1] == ""

