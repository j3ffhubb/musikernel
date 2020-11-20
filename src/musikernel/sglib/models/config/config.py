from pymarshal import type_assert, type_assert_iter


class FileBrowserBookmark:
    """ Created when user clicks "Bookmark..." in a file browser """
    def __init__(
        self,
        name,
        path,
        group,
    ):
        self.name = type_assert(
            name,
            str,
            desc="The name of the bookmark",
        )
        self.path = type_assert(
            path,
            str,
            desc="The path of the bookmark",
        )
        self.group = type_assert(
            group,
            str,
            desc="The group of the bookmark",
        )

class GlobalConfig:
    """
        The global configuration file
    """
    def __init__(
        self,
        tooltips,
        bookmarks,
    ):
        self.tooltips = type_assert(
            tooltips,
            bool,
            desc="True to enable tooltips",
        )
        self.bookmarks = type_assert_iter(
            bookmarks,
            FileBrowserBookmark,
            desc="File browser bookmarks",
        )

    @staticmethod
    def new():
        return GlobalConfig(True, [])

