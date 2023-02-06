from setuptools import setup, find_packages


setup(
    name='mintospy',
    version='0.6.1',
    license='MIT',
    author='Tomás Perestrelo',
    author_email='tomasperestrelo21@gmail.com',
    packages=find_packages(exclude=('tests*', 'testing*')),
    url='https://github.com/thicccat688/mintospy',
    download_url='https://pypi.org/project/mintospy',
    keywords='python, api, api-wrapper, mintos',
    long_description=open('README.rst', 'r').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'anyio==3.6.2',
        'async-generator==1.10',
        'attrs==22.1.0',
        'beautifulsoup4==4.11.1',
        'bleach==5.0.1',
        'build==0.9.0',
        'certifi==2022.12.7',
        'cffi==1.15.1',
        'charset-normalizer==2.1.1',
        'click==8.1.3',
        'colorama==0.4.6',
        'commonmark==0.9.1',
        'docutils==0.19',
        'exceptiongroup==1.0.4',
        'filelock==3.8.0',
        'h11==0.14.0',
        'httpcore==0.16.2',
        'httpx==0.23.1',
        'idna==3.4',
        'importlib-metadata==5.2.0',
        'iniconfig==1.1.1',
        'jaraco.classes==3.2.3',
        'keyring==23.13.1',
        'more-itertools==9.0.0',
        'numpy==1.23.5',
        'outcome==1.2.0',
        'packaging==22.0',
        'pandas==1.5.2',
        'pep517==0.13.0',
        'pip-tools==6.12.1',
        'pkginfo==1.9.2',
        'pluggy==1.0.0',
        'pycparser==2.21',
        'pydub==0.25.1',
        'Pygments==2.13.0',
        'pyotp==2.8.0',
        'pyparsing==3.0.9',
        'PySocks==1.7.1',
        'python-dateutil==2.8.2',
        'python-dotenv==0.19.2',
        'pytz==2022.6',
        'pywin32-ctypes==0.2.0',
        'readme-renderer==37.3',
        'requests==2.28.1',
        'requests-file==1.5.1',
        'requests-toolbelt==0.10.1',
        'rfc3986==1.5.0',
        'rich==12.6.0',
        'selenium==4.7.2',
        'selenium-recaptcha-solver==1.0.6',
        'six==1.16.0',
        'sniffio==1.3.0',
        'sortedcontainers==2.4.0',
        'soupsieve==2.3.2.post1',
        'SpeechRecognition==3.8.1',
        'tldextract==3.4.0',
        'tomli==2.0.1',
        'tqdm==4.64.1',
        'trio==0.22.0',
        'trio-websocket==0.9.2',
        'twine==4.0.2',
        'urllib3==1.26.13',
        'webdriver-manager==3.8.5',
        'webencodings==0.5.1',
        'wsproto==1.2.0',
        'zipp==3.11.0',
        'selenium-stealth==1.0.6',
        'cloudscraper~=1.2.68',
    ],
)
