from setuptools import setup, find_packages


setup(
    name='mintospy',
    version='0.0.1',
    license='MIT',
    author='Tomás Perestrelo',
    author_email='tomasperestrelo21@gmail.com',
    packages=find_packages(exclude=('tests*', 'testing*')),
    url='https://github.com/thicccat688/mintospy',
    download_url='https://pypi.org/project/mintospy',
    keywords='python, api, api-wrapper, mintos',
    long_description=open('README.rst.rst', 'r').read(),
    long_description_content_type='text/markdown',
    install_requires=['requests'],
)
