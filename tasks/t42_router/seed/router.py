import sys


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, handler):
        self.routes.append((method, path, handler))

    def dispatch(self, method, path):
        for m, p, handler in self.routes:
            if m == method and p == path:
                return handler()
        return "404 Not Found"


def home():
    return "home page"


def about():
    return "about page"


def list_users():
    return "all users"


router = Router()
router.add("GET", "/", home)
router.add("GET", "/about", about)
router.add("GET", "/users", list_users)


def main(argv):
    method, path = argv[0], argv[1]
    print(router.dispatch(method, path))


if __name__ == "__main__":
    main(sys.argv[1:])
