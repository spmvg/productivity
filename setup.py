import setuptools

setuptools.setup(
    name="productivity-spmvg",
    version="0.0.1",
    author="spmvg",
    author_email="13852721+spmvg@users.noreply.github.com",
    url="https://github.com/spmvg/productivity",
    packages=setuptools.find_packages(include=['productivity']),
    install_requires=[
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'parameterized',
        'pytz'
    ],
    python_requires='>=3.7'
)