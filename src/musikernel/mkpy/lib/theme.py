from .util import *

ICON_PATH = os.path.join(
    INSTALL_PREFIX, "share", "pixmaps",
    "{}.png".format(global_pydaw_version_string))

print("ICON_PATH = '{}'".format(ICON_PATH))
if IS_WINDOWS:
    ICON_PATH = os.path.join(
        INSTALL_PREFIX,
        "{}.ico".format(global_pydaw_version_string),
    )

DEFAULT_STYLESHEET_FILE = os.path.join(
    INSTALL_PREFIX,
    "lib",
    global_pydaw_version_string,
    "themes",
    "default",
    "default.pytheme",
)

STYLESHEET_FILE = get_file_setting("default-style", str, None)

if not (
    STYLESHEET_FILE
    and
    os.path.isfile(STYLESHEET_FILE)
):
    STYLESHEET_FILE = DEFAULT_STYLESHEET_FILE

def pydaw_escape_stylesheet(a_stylesheet, a_path):
    f_dir = os.path.dirname(str(a_path))
    if IS_WINDOWS:
        f_dir = f_dir[0].lower() + f_dir[1:].replace("\\", "/")
    f_result = a_stylesheet.replace("$STYLE_FOLDER", f_dir)
    return f_result

def load_color_palette():
    css_hex_color_regex = re.compile("#(?:[0-9a-fA-F]{6})$")

    def test_value(a_val):
        if len(a_val) != 7 or not css_hex_color_regex.match(a_val):
            raise Exception("Invalid value '{}'".format(a_val))

    filename = os.path.join(STYLESHEET_DIR, "palette.json")
    if os.path.isfile(filename):
        print("Attempting to load '{}'".format(filename))
        with open(filename) as fh:
            try:
                tmp_palette = ast.literal_eval(fh.read())
                for k, v in tmp_palette.items():
                    if k not in COLOR_PALETTE:
                        print("Unknown key '{}'".format(k))
                        continue
                    if isinstance(v, list):
                        for val in v:
                            test_value(val)
                    else:
                        test_value(v)
                    COLOR_PALETTE[k] = v
            except Exception as ex:
                print("Error loading color palette: {}".format(ex))

print("Using stylesheet " + STYLESHEET_FILE)
STYLESHEET = pydaw_read_file_text(STYLESHEET_FILE)
STYLESHEET = pydaw_escape_stylesheet(STYLESHEET, STYLESHEET_FILE)
STYLESHEET_DIR = os.path.dirname(STYLESHEET_FILE)

load_color_palette()