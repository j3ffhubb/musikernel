#!/usr/bin/env python3

import os, sys, subprocess

pydaw_version = "musikernel3"

print("sys.argv == {}".format(sys.argv))

# When respawning, give the old process a chance to garbage collect first
if "--delay" in sys.argv:
    sys.argv.remove("--delay")
    import time
    time.sleep(2)

if len(sys.argv) > 1:
    import signal

    def sig_handle(a_1=None, a_2=None):
        try:
            f_proc.kill()
        except Exception as ex:
            print("Exception while trying to kill engine from "
                "helper script: {}".format(ex))

    signal.signal(signal.SIGTERM, sig_handle)
    signal.signal(signal.SIGINT, sig_handle)
    signal.signal(signal.SIGABRT, sig_handle)

    f_path = "{}/{}-engine".format(os.path.dirname(__file__), pydaw_version)
    print(f_path)
    f_proc = subprocess.Popen([f_path] + sys.argv[1:])
    f_proc.wait()
    print("helper script:  f_proc returned with {}".format(f_proc.returncode))
    sys.exit(f_proc.returncode)
else:
    f_prefix_dir = os.path.dirname(__file__)
    f_path = os.path.join(
        f_prefix_dir, "..", "lib", pydaw_version, "pydaw")
    f_path = os.path.abspath(f_path)
    print(f_path)
    sys.path.insert(0, f_path)
    from mkpy.musikernel import main
    main()
