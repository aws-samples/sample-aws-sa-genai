import pip

def install_whl(path):
    pip.main(['install', path])

install_whl("<path of botocore>/botocore-1.23.32-py3-none-any.whl")