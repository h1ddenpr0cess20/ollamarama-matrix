from ollamarama.handlers.router import Router


def test_router_unknown_command():
    r = Router()
    fn, args = r.dispatch(object(), "!r", "@u", "User", ".unknown hi", False, bot_name="Bot")
    assert fn is None
    assert args == tuple()


def test_router_admin_dispatch_requires_admin_flag():
    r = Router()

    async def h(ctx, room, sender, display, args):
        pass

    r.register(".model", h, admin=True)
    fn, _ = r.dispatch(object(), "!r", "@u", "User", ".model q", False, bot_name="Bot")
    assert fn is None
    fn, _ = r.dispatch(object(), "!r", "@u", "Admin", ".model q", True, bot_name="Bot")
    assert fn is h


def test_router_botname_must_match_exactly():
    r = Router()

    async def h(ctx, room, sender, display, args):
        pass

    r.register(".ai", h)
    fn, _ = r.dispatch(object(), "!r", "@u", "User", "Bot hi", False, bot_name="Bot")
    assert fn is None
    fn, _ = r.dispatch(object(), "!r", "@u", "User", "OtherBot: hi", False, bot_name="Bot")
    assert fn is None

