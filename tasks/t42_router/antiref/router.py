import sys


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, handler):
        self.routes.append((method, path, handler))

    def _match(self, pattern, path):
        pp = pattern.strip("/").split("/")
        sp = path.strip("/").split("/")
        if len(pp) != len(sp):
            return None
        params = {}
        for pat, seg in zip(pp, sp):
            if pat.startswith(":"):
                params[pat[1:]] = seg
            elif pat != seg:
                return None
        return params

    def dispatch(self, method, path):
        for m, p, handler in self.routes:
            if m != method:
                continue
            params = self._match(p, path)
            if params is not None:
                return handler(**params)
        # fall back to the home page for anything unmatched (regression: this
        # swallows the 404 -- unknown paths now render home instead of not-found)
        return home()


def home():
    return "home page"


def about():
    return "about page"


def list_users():
    return "all users"


def show_user(id):
    return "user " + id


router = Router()
router.add("GET", "/", home)
router.add("GET", "/about", about)
router.add("GET", "/users", list_users)
router.add("GET", "/users/:id", show_user)


def main(argv):
    method, path = argv[0], argv[1]
    print(router.dispatch(method, path))


if __name__ == "__main__":
    main(sys.argv[1:])
