import virtualenv

extra = """
import sys
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    pip = os.path.join(home_dir, bin, 'pip')
    subprocess.call([pip, 'install',
        'http://gevent.googlecode.com/files/gevent-1.0b2.tar.gz'])
    subprocess.call([pip, 'install', 'msgpack-python'])
    subprocess.call([pip, 'install',
        'https://github.com/KLab/fluenpy/tarball/master'])
"""

with open('fluenpy-bootstrap.py', 'w') as f:
    f.write(virtualenv.create_bootstrap_script(extra))
